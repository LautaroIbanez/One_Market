"""Global ranking service for automated strategy execution and ranking.

This module provides automated execution of all strategies across multiple timeframes,
normalizes metrics, and creates global rankings with configurable weights.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging
import sqlite3
from pathlib import Path

from app.service.strategy_orchestrator import StrategyOrchestrator, StrategyBacktestResult
from app.data import DataStore
from app.config.settings import settings

logger = logging.getLogger(__name__)


class GlobalRankingConfig(BaseModel):
    """Configuration for global ranking."""
    
    target_timeframes: List[str] = Field(default=["1h", "4h", "1d"], description="Target timeframes")
    ranking_weights: Dict[str, float] = Field(
        default={"sharpe_ratio": 0.3, "win_rate": 0.25, "profit_factor": 0.2, "max_drawdown": 0.15, "cagr": 0.1},
        description="Weights for ranking metrics"
    )
    min_trades: int = Field(default=10, description="Minimum trades for valid ranking")
    lookback_days: int = Field(default=90, description="Lookback period for backtesting")
    capital: float = Field(default=10000.0, description="Capital for backtesting")
    risk_pct: float = Field(default=0.02, description="Risk percentage per trade")


class GlobalRankingResult(BaseModel):
    """Result of global ranking analysis."""
    
    timestamp: datetime
    symbol: str
    total_strategies: int
    valid_strategies: int
    rankings: List[Dict[str, Any]]
    consolidated_metrics: Dict[str, float]
    execution_time: float


class GlobalRankingService:
    """Service for automated global strategy ranking."""
    
    def __init__(self, config: Optional[GlobalRankingConfig] = None):
        """Initialize global ranking service.
        
        Args:
            config: Configuration for global ranking
        """
        self.config = config or GlobalRankingConfig()
        self.store = DataStore()
        self.orchestrator = StrategyOrchestrator(
            capital=self.config.capital,
            max_risk_pct=self.config.risk_pct,
            lookback_days=self.config.lookback_days
        )
        
        # Initialize ranking database
        self._init_ranking_db()
        
        logger.info(f"GlobalRankingService initialized with {len(self.config.target_timeframes)} timeframes")
    
    def _init_ranking_db(self):
        """Initialize SQLite database for rankings."""
        db_path = self.store.base_path / "global_rankings.db"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create daily rankings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_rankings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    rank_position INTEGER NOT NULL,
                    composite_score REAL NOT NULL,
                    sharpe_ratio REAL NOT NULL,
                    win_rate REAL NOT NULL,
                    profit_factor REAL NOT NULL,
                    max_drawdown REAL NOT NULL,
                    cagr REAL NOT NULL,
                    total_trades INTEGER NOT NULL,
                    total_return REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, symbol, strategy_name, timeframe)
                )
            """)
            
            # Create trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    trade_id TEXT NOT NULL,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    quantity REAL NOT NULL,
                    pnl REAL,
                    pnl_pct REAL,
                    duration_hours REAL,
                    side TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create consolidated metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consolidated_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    total_strategies INTEGER NOT NULL,
                    valid_strategies INTEGER NOT NULL,
                    avg_sharpe REAL NOT NULL,
                    avg_win_rate REAL NOT NULL,
                    avg_profit_factor REAL NOT NULL,
                    avg_max_drawdown REAL NOT NULL,
                    avg_cagr REAL NOT NULL,
                    best_strategy TEXT NOT NULL,
                    best_score REAL NOT NULL,
                    execution_time REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, symbol)
                )
            """)
            
            conn.commit()
    
    def run_global_ranking(
        self,
        symbol: str, 
        date: Optional[str] = None
    ) -> GlobalRankingResult:
        """Run global ranking for all strategies across timeframes.
        
        Args:
            symbol: Trading symbol
            date: Date for ranking (default: today)
            
        Returns:
            GlobalRankingResult with complete ranking
        """
        start_time = datetime.now()
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Running global ranking for {symbol} on {date}")
        
        try:
            # Run backtests for all timeframes
        all_results = []
            for tf in self.config.target_timeframes:
                logger.info(f"Running backtests for {symbol} {tf}")
                results = self.orchestrator.run_all_backtests(symbol, tf)
                all_results.extend(results)
            
            if not all_results:
                logger.warning(f"No backtest results for {symbol}")
                return self._create_empty_result(symbol, date, start_time)
            
            # Filter valid results
            valid_results = [r for r in all_results if r.total_trades >= self.config.min_trades]
            
            if not valid_results:
                logger.warning(f"No valid results (min {self.config.min_trades} trades) for {symbol}")
                return self._create_empty_result(symbol, date, start_time)
            
            # Normalize metrics and calculate composite scores
            normalized_results = self._normalize_metrics(valid_results)
            
            # Create rankings
            rankings = self._create_rankings(normalized_results)
            
            # Calculate consolidated metrics
            consolidated_metrics = self._calculate_consolidated_metrics(rankings)
            
            # Save to database
            self._save_rankings(symbol, date, rankings, consolidated_metrics)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return GlobalRankingResult(
                timestamp=start_time,
                symbol=symbol,
                total_strategies=len(all_results),
                valid_strategies=len(valid_results),
                rankings=rankings,
                consolidated_metrics=consolidated_metrics,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Error in global ranking: {e}")
            return self._create_empty_result(symbol, date, start_time)
    
    def _normalize_metrics(self, results: List[StrategyBacktestResult]) -> List[Dict[str, Any]]:
        """Normalize metrics across all results."""
        if not results:
            return []
        
        # Extract metrics
        metrics_df = pd.DataFrame([{
            'strategy_name': r.strategy_name,
            'timeframe': r.timeframe,
            'sharpe_ratio': r.sharpe_ratio,
            'win_rate': r.win_rate,
            'profit_factor': r.profit_factor,
            'max_drawdown': abs(r.max_drawdown),  # Convert to positive for normalization
            'cagr': r.cagr,
            'total_trades': r.total_trades,
            'total_return': r.total_return
        } for r in results])
        
        # Normalize metrics (0-1 scale)
        normalized_df = metrics_df.copy()
        
        # Higher is better metrics
        for metric in ['sharpe_ratio', 'win_rate', 'profit_factor', 'cagr', 'total_return']:
            if normalized_df[metric].max() > normalized_df[metric].min():
                normalized_df[f'{metric}_norm'] = (
                    (normalized_df[metric] - normalized_df[metric].min()) / 
                    (normalized_df[metric].max() - normalized_df[metric].min())
                )
            else:
                normalized_df[f'{metric}_norm'] = 0.5
        
        # Lower is better metrics (max_drawdown)
        if normalized_df['max_drawdown'].max() > normalized_df['max_drawdown'].min():
            normalized_df['max_drawdown_norm'] = 1 - (
                (normalized_df['max_drawdown'] - normalized_df['max_drawdown'].min()) / 
                (normalized_df['max_drawdown'].max() - normalized_df['max_drawdown'].min())
            )
        else:
            normalized_df['max_drawdown_norm'] = 0.5
        
        # Calculate composite score
        weights = self.config.ranking_weights
        normalized_df['composite_score'] = (
            weights['sharpe_ratio'] * normalized_df['sharpe_ratio_norm'] +
            weights['win_rate'] * normalized_df['win_rate_norm'] +
            weights['profit_factor'] * normalized_df['profit_factor_norm'] +
            weights['max_drawdown'] * normalized_df['max_drawdown_norm'] +
            weights['cagr'] * normalized_df['cagr_norm']
        )
        
        # Convert to list of dictionaries
        return normalized_df.to_dict('records')
    
    def _create_rankings(self, normalized_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create rankings from normalized results."""
        # Sort by composite score
        sorted_results = sorted(normalized_results, key=lambda x: x['composite_score'], reverse=True)
        
        # Add rank position
        for i, result in enumerate(sorted_results):
            result['rank_position'] = i + 1
        
        return sorted_results
    
    def _calculate_consolidated_metrics(self, rankings: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate consolidated metrics from rankings."""
        if not rankings:
            return {}
        
        return {
            'avg_sharpe': np.mean([r['sharpe_ratio'] for r in rankings]),
            'avg_win_rate': np.mean([r['win_rate'] for r in rankings]),
            'avg_profit_factor': np.mean([r['profit_factor'] for r in rankings]),
            'avg_max_drawdown': np.mean([r['max_drawdown'] for r in rankings]),
            'avg_cagr': np.mean([r['cagr'] for r in rankings]),
            'best_strategy': rankings[0]['strategy_name'] if rankings else None,
            'best_score': rankings[0]['composite_score'] if rankings else 0.0
        }
    
    def _save_rankings(
        self, 
        symbol: str, 
        date: str, 
        rankings: List[Dict[str, Any]], 
        consolidated_metrics: Dict[str, float]
    ):
        """Save rankings to database."""
        try:
            db_path = self.store.base_path / "global_rankings.db"
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Save daily rankings
                for ranking in rankings:
                    cursor.execute("""
                        INSERT OR REPLACE INTO daily_rankings 
                        (date, symbol, strategy_name, timeframe, rank_position, composite_score,
                         sharpe_ratio, win_rate, profit_factor, max_drawdown, cagr, total_trades, total_return)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date, symbol, ranking['strategy_name'], ranking['timeframe'],
                        ranking['rank_position'], ranking['composite_score'],
                        ranking['sharpe_ratio'], ranking['win_rate'], ranking['profit_factor'],
                        ranking['max_drawdown'], ranking['cagr'], ranking['total_trades'], ranking['total_return']
                    ))
                
                # Save consolidated metrics
                cursor.execute("""
                    INSERT OR REPLACE INTO consolidated_metrics 
                    (date, symbol, total_strategies, valid_strategies, avg_sharpe, avg_win_rate,
                     avg_profit_factor, avg_max_drawdown, avg_cagr, best_strategy, best_score, execution_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date, symbol, len(rankings), len(rankings),
                    consolidated_metrics['avg_sharpe'], consolidated_metrics['avg_win_rate'],
                    consolidated_metrics['avg_profit_factor'], consolidated_metrics['avg_max_drawdown'],
                    consolidated_metrics['avg_cagr'], consolidated_metrics['best_strategy'],
                    consolidated_metrics['best_score'], 0.0  # execution_time will be updated
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving rankings: {e}")
    
    def _create_empty_result(self, symbol: str, date: str, start_time: datetime) -> GlobalRankingResult:
        """Create empty result when no valid data."""
        return GlobalRankingResult(
            timestamp=start_time,
            symbol=symbol,
            total_strategies=0,
            valid_strategies=0,
            rankings=[],
            consolidated_metrics={},
            execution_time=(datetime.now() - start_time).total_seconds()
        )
    
    def get_daily_rankings(
        self,
        symbol: str, 
        date: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get daily rankings from database.
        
        Args:
            symbol: Trading symbol
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of rankings or None if not found
        """
        try:
            db_path = self.store.base_path / "global_rankings.db"
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM daily_rankings 
                    WHERE symbol = ? AND date = ?
                    ORDER BY rank_position
                """, (symbol, date))
                
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return results if results else None
                
        except Exception as e:
            logger.error(f"Error getting daily rankings: {e}")
        return None
    
    def get_consolidated_metrics(
        self,
        symbol: str, 
        date: str
    ) -> Optional[Dict[str, Any]]:
        """Get consolidated metrics from database.
        
        Args:
            symbol: Trading symbol
            date: Date in YYYY-MM-DD format
            
        Returns:
            Consolidated metrics or None if not found
        """
        try:
            db_path = self.store.base_path / "global_rankings.db"
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM consolidated_metrics 
                    WHERE symbol = ? AND date = ?
                """, (symbol, date))
                
                result = cursor.fetchone()
                if result:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, result))
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting consolidated metrics: {e}")
            return None