"""Simplified daily recommendation service for One Market platform."""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import logging

from app.data import DataStore, DataFetcher
from app.research.signals import generate_signal, get_strategy_list
from app.service.recommendation_contract import Recommendation, PlanDirection, RecommendationRequest, RecommendationResponse
from app.service.strategy_ranking import StrategyRankingService, StrategyRecommendation
from app.service.recommendation_weights import RecommendationWeightCalculator, WeightConfig
from app.config.settings import settings

logger = logging.getLogger(__name__)


class DailyRecommendationService:
    """Service for generating daily trading recommendations."""

    def __init__(self, capital: float = 10000.0, max_risk_pct: float = 2.0):
        """Initialize recommendation service.
        
        Args:
            capital: Available capital
            max_risk_pct: Maximum risk percentage per trade
        """
        self.capital = capital
        self.max_risk_pct = max_risk_pct
        self.store = DataStore()
        self.fetcher = DataFetcher()
        
        # Initialize strategy ranking service
        self.strategy_ranking = StrategyRankingService(
            capital=capital,
            max_risk_pct=max_risk_pct,
            lookback_days=90
        )
        
        # Initialize weight calculator
        self.weight_calculator = RecommendationWeightCalculator(
            config=WeightConfig(
                method="softmax",
                temperature=1.0,
                min_weight=0.01,
                max_weight=0.5,
                normalize=True
            )
        )
        
        # Initialize recommendation database
        self._init_recommendation_db()
        
        logger.info(f"DailyRecommendationService initialized with capital=${capital:,.2f}")
    
    def _init_recommendation_db(self):
        """Initialize SQLite database for recommendations."""
        db_path = self.store.base_path / "recommendations.db"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create recommendations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL,
                    entry_band_min REAL,
                    entry_band_max REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    quantity REAL,
                    risk_amount REAL,
                    risk_percentage REAL,
                    rationale TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    dataset_hash TEXT NOT NULL,
                    params_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    UNIQUE(date, symbol, timeframe)
                )
            """)
            
            conn.commit()
    
    def get_daily_recommendation(
        self, 
        symbol: str, 
        date: str,
        timeframes: List[str] = None,
        use_strategy_ranking: bool = True
    ) -> Recommendation:
        """Generate daily recommendation for symbol/date.
        
        Args:
            symbol: Trading symbol
            date: Date in YYYY-MM-DD format
            timeframes: List of timeframes to analyze
            use_strategy_ranking: Whether to use strategy ranking for recommendation
            
        Returns:
            Recommendation object or HOLD with reason
        """
        if timeframes is None:
            timeframes = ["1h", "4h", "1d"]
        
        try:
            logger.info(f"Generating recommendation for {symbol} on {date}")
            
            # For now, return a simple HOLD recommendation
            return self._create_hold_recommendation(
                symbol, date, "Sistema en mantenimiento - recomendación temporal"
            )
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return self._create_hold_recommendation(
                symbol, date, f"Error in recommendation generation: {str(e)}"
            )
    
    def _create_hold_recommendation(self, symbol: str, date: str, reason: str) -> Recommendation:
        """Create a HOLD recommendation."""
        return Recommendation(
            date=date,
            symbol=symbol,
            timeframe="1h",
            direction=PlanDirection.HOLD,
            entry_band=None,
            stop_loss=None,
            take_profit=None,
            quantity=None,
            risk_amount=None,
            risk_percentage=None,
            confidence=0.0,
            rationale=reason,
            dataset_hash=f"hold_{symbol}_{date}",
            params_hash="hold_recommendation"
        )
    
    def get_recommendation_history(
        self, 
        symbol: str, 
        from_date: str, 
        to_date: str
    ) -> List[Recommendation]:
        """Get recommendation history for symbol and date range."""
        try:
            db_path = self.store.base_path / "recommendations.db"
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM recommendations 
                    WHERE symbol = ? AND date BETWEEN ? AND ?
                    ORDER BY date DESC
                """, (symbol, from_date, to_date))
                
                rows = cursor.fetchall()
                recommendations = []
                
                for row in rows:
                    recommendation = Recommendation(
                        date=row[1],
                        symbol=row[2],
                        timeframe=row[3],
                        direction=PlanDirection(row[4]),
                        entry_band=row[5],
                        stop_loss=row[6],
                        take_profit=row[7],
                        quantity=row[8],
                        risk_amount=row[9],
                        risk_percentage=row[10],
                        confidence=row[11],
                        rationale=row[12],
                        dataset_hash=row[13],
                        params_hash=row[14]
                    )
                    recommendations.append(recommendation)
                
                return recommendations
                
        except Exception as e:
            logger.error(f"Error getting recommendation history: {e}")
            return []
    
    def _save_recommendation(self, recommendation: Recommendation):
        """Save recommendation to database."""
        try:
            db_path = self.store.base_path / "recommendations.db"
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO recommendations (
                        date, symbol, timeframe, direction, entry_price,
                        entry_band_min, entry_band_max, stop_loss, take_profit,
                        quantity, risk_amount, risk_percentage, rationale,
                        confidence, dataset_hash, params_hash, created_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    recommendation.date,
                    recommendation.symbol,
                    recommendation.timeframe,
                    recommendation.direction.value,
                    recommendation.entry_band,
                    recommendation.entry_band,
                    recommendation.entry_band,
                    recommendation.stop_loss,
                    recommendation.take_profit,
                    recommendation.quantity,
                    recommendation.risk_amount,
                    recommendation.risk_percentage,
                    recommendation.rationale,
                    recommendation.confidence,
                    recommendation.dataset_hash,
                    recommendation.params_hash,
                    datetime.now().isoformat(),
                    (datetime.now() + timedelta(hours=24)).isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving recommendation: {e}")
