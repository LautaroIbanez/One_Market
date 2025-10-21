"""Global strategy ranking service.

This service provides comprehensive ranking of strategies across multiple
timeframes and combinations, using weighted metrics and normalization.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field

from app.service.strategy_orchestrator import StrategyBacktestResult
from app.config.settings import settings


class RankedStrategy(BaseModel):
    """Ranked strategy with comprehensive metrics."""
    
    strategy_name: str
    timeframe: Optional[str] = None
    is_combination: bool = False
    
    # Global ranking
    global_score: float
    global_rank: int
    
    # Timeframe breakdown
    timeframe_breakdown: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    
    # Weighted metrics
    weighted_sharpe: float
    weighted_win_rate: float
    weighted_max_dd: float
    weighted_profit_factor: float
    weighted_expectancy: float
    
    # Raw metrics (best across timeframes)
    best_sharpe: float
    best_win_rate: float
    best_cagr: float
    best_profit_factor: float
    best_expectancy: float
    worst_max_dd: float
    
    # Consistency metrics
    sharpe_consistency: float  # Coefficient of variation
    win_rate_consistency: float
    cagr_consistency: float


class GlobalRankingService:
    """Service for global strategy ranking across timeframes and combinations."""
    
    def __init__(self):
        """Initialize global ranking service."""
        self.weights = settings.RANKING_WEIGHTS
        self.target_timeframes = settings.TARGET_TIMEFRAMES
    
    def rank_strategies(
        self,
        multi_timeframe_results: Dict[str, List[StrategyBacktestResult]],
        combination_results: Optional[Dict[str, List[StrategyBacktestResult]]] = None
    ) -> List[RankedStrategy]:
        """Rank strategies globally across timeframes and combinations.
        
        Args:
            multi_timeframe_results: Results by timeframe
            combination_results: Optional combination results
            
        Returns:
            List of ranked strategies
        """
        # Collect all results
        all_results = []
        
        # Add individual strategy results
        for timeframe, results in multi_timeframe_results.items():
            for result in results:
                all_results.append({
                    'result': result,
                    'timeframe': timeframe,
                    'is_combination': False
                })
        
        # Add combination results if provided
        if combination_results:
            for timeframe, results in combination_results.items():
                for result in results:
                    all_results.append({
                        'result': result,
                        'timeframe': timeframe,
                        'is_combination': True
                    })
        
        # Group by strategy name
        strategy_groups = {}
        for item in all_results:
            strategy_name = item['result'].strategy_name
            if strategy_name not in strategy_groups:
                strategy_groups[strategy_name] = []
            strategy_groups[strategy_name].append(item)
        
        # Calculate global rankings
        ranked_strategies = []
        
        for strategy_name, items in strategy_groups.items():
            ranked_strategy = self._calculate_global_ranking(strategy_name, items)
            ranked_strategies.append(ranked_strategy)
        
        # Sort by global score
        ranked_strategies.sort(key=lambda x: x.global_score, reverse=True)
        
        # Assign ranks
        for i, strategy in enumerate(ranked_strategies):
            strategy.global_rank = i + 1
        
        return ranked_strategies
    
    def _calculate_global_ranking(
        self,
        strategy_name: str,
        items: List[Dict[str, Any]]
    ) -> RankedStrategy:
        """Calculate global ranking for a strategy."""
        
        # Extract metrics by timeframe
        timeframe_metrics = {}
        all_sharpes = []
        all_win_rates = []
        all_cagrs = []
        all_profit_factors = []
        all_expectancies = []
        all_max_dds = []
        
        for item in items:
            result = item['result']
            timeframe = item['timeframe']
            is_combination = item['is_combination']
            
            timeframe_metrics[timeframe] = {
                'sharpe_ratio': result.sharpe_ratio,
                'win_rate': result.win_rate,
                'cagr': result.cagr,
                'profit_factor': result.profit_factor,
                'expectancy': result.expectancy,
                'max_drawdown': result.max_drawdown,
                'total_trades': result.total_trades
            }
            
            all_sharpes.append(result.sharpe_ratio)
            all_win_rates.append(result.win_rate)
            all_cagrs.append(result.cagr)
            all_profit_factors.append(result.profit_factor)
            all_expectancies.append(result.expectancy)
            all_max_dds.append(result.max_drawdown)
        
        # Calculate weighted metrics
        weighted_sharpe = np.mean(all_sharpes) * self.weights['sharpe_ratio']
        weighted_win_rate = np.mean(all_win_rates) * self.weights['win_rate']
        weighted_max_dd = abs(np.mean(all_max_dds)) * self.weights['max_drawdown']  # Convert to positive
        weighted_profit_factor = np.mean(all_profit_factors) * self.weights['profit_factor']
        weighted_expectancy = np.mean(all_expectancies) * self.weights['expectancy']
        
        # Calculate global score
        global_score = (
            weighted_sharpe +
            weighted_win_rate +
            weighted_max_dd +
            weighted_profit_factor +
            weighted_expectancy
        )
        
        # Calculate consistency metrics
        sharpe_consistency = np.std(all_sharpes) / np.mean(all_sharpes) if np.mean(all_sharpes) != 0 else 0
        win_rate_consistency = np.std(all_win_rates) / np.mean(all_win_rates) if np.mean(all_win_rates) != 0 else 0
        cagr_consistency = np.std(all_cagrs) / np.mean(all_cagrs) if np.mean(all_cagrs) != 0 else 0
        
        # Get best metrics
        best_sharpe = max(all_sharpes)
        best_win_rate = max(all_win_rates)
        best_cagr = max(all_cagrs)
        best_profit_factor = max(all_profit_factors)
        best_expectancy = max(all_expectancies)
        worst_max_dd = min(all_max_dds)  # Most negative (worst)
        
        return RankedStrategy(
            strategy_name=strategy_name,
            timeframe=None,  # Multi-timeframe
            is_combination=any(item['is_combination'] for item in items),
            global_score=global_score,
            global_rank=0,  # Will be set later
            timeframe_breakdown=timeframe_metrics,
            weighted_sharpe=weighted_sharpe,
            weighted_win_rate=weighted_win_rate,
            weighted_max_dd=weighted_max_dd,
            weighted_profit_factor=weighted_profit_factor,
            weighted_expectancy=weighted_expectancy,
            best_sharpe=best_sharpe,
            best_win_rate=best_win_rate,
            best_cagr=best_cagr,
            best_profit_factor=best_profit_factor,
            best_expectancy=best_expectancy,
            worst_max_dd=worst_max_dd,
            sharpe_consistency=sharpe_consistency,
            win_rate_consistency=win_rate_consistency,
            cagr_consistency=cagr_consistency
        )
    
    def get_top_strategies(
        self,
        ranked_strategies: List[RankedStrategy],
        top_n: int = 10,
        include_combinations: bool = True
    ) -> List[RankedStrategy]:
        """Get top N strategies.
        
        Args:
            ranked_strategies: List of ranked strategies
            top_n: Number of top strategies to return
            include_combinations: Whether to include combination strategies
            
        Returns:
            List of top strategies
        """
        filtered = ranked_strategies
        
        if not include_combinations:
            filtered = [s for s in ranked_strategies if not s.is_combination]
        
        return filtered[:top_n]
    
    def get_strategy_breakdown(
        self,
        strategy_name: str,
        ranked_strategies: List[RankedStrategy]
    ) -> Optional[RankedStrategy]:
        """Get detailed breakdown for a specific strategy.
        
        Args:
            strategy_name: Name of strategy
            ranked_strategies: List of ranked strategies
            
        Returns:
            RankedStrategy with detailed breakdown
        """
        for strategy in ranked_strategies:
            if strategy.strategy_name == strategy_name:
                return strategy
        return None
    
    def export_ranking_report(
        self,
        ranked_strategies: List[RankedStrategy],
        filename: Optional[str] = None
    ) -> str:
        """Export ranking report to CSV.
        
        Args:
            ranked_strategies: List of ranked strategies
            filename: Optional filename
            
        Returns:
            CSV content
        """
        if filename is None:
            filename = f"global_ranking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Create DataFrame
        data = []
        for strategy in ranked_strategies:
            data.append({
                'Rank': strategy.global_rank,
                'Strategy': strategy.strategy_name,
                'Type': 'Combination' if strategy.is_combination else 'Individual',
                'Global Score': strategy.global_score,
                'Best Sharpe': strategy.best_sharpe,
                'Best Win Rate': strategy.best_win_rate,
                'Best CAGR': strategy.best_cagr,
                'Best Profit Factor': strategy.best_profit_factor,
                'Best Expectancy': strategy.best_expectancy,
                'Worst Max DD': strategy.worst_max_dd,
                'Sharpe Consistency': strategy.sharpe_consistency,
                'Win Rate Consistency': strategy.win_rate_consistency,
                'CAGR Consistency': strategy.cagr_consistency
            })
        
        df = pd.DataFrame(data)
        return df.to_csv(index=False)
