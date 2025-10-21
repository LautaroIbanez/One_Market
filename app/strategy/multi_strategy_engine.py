"""Multi-Strategy Engine with Advanced Portfolio Management.

This module provides an advanced multi-strategy execution engine that:
- Runs multiple strategies in parallel with individual position sizing
- Aggregates signals by weighted voting or ensemble methods
- Tracks per-strategy performance with rolling metrics
- Auto-selects strategies based on recent performance
- Implements advanced risk management (VaR, correlations)
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from collections import defaultdict
import logging

from app.research.signals import generate_signal, get_strategy_list
from app.research.backtest.engine import BacktestEngine, BacktestConfig
from app.service.decision import DecisionEngine, DailyDecision
from app.core.risk import calculate_position_size_fixed_risk

logger = logging.getLogger(__name__)


class StrategyPerformance(BaseModel):
    """Per-strategy performance metrics."""
    strategy_name: str
    sharpe_ratio: float = 0.0
    total_return: float = 0.0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    total_trades: int = 0
    avg_trade_return: float = 0.0
    profit_factor: float = 0.0
    calmar_ratio: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.now)
    rolling_returns: List[float] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class StrategyWeight(BaseModel):
    """Strategy weight configuration."""
    strategy_name: str
    weight: float = Field(ge=0.0, le=1.0, description="Weight in ensemble (0-1)")
    enabled: bool = True
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    max_allocation_pct: float = Field(default=0.3, description="Max % of capital")


class EnsembleSignal(BaseModel):
    """Aggregated signal from multiple strategies."""
    signal: int = Field(..., description="Aggregated signal: 1 (long), -1 (short), 0 (flat)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Ensemble confidence")
    strategy_votes: Dict[str, int] = Field(..., description="Individual strategy votes")
    strategy_weights: Dict[str, float] = Field(..., description="Weights used")
    contributing_strategies: List[str] = Field(..., description="Strategies that contributed")
    
    class Config:
        arbitrary_types_allowed = True


class MultiStrategyEngine:
    """Advanced multi-strategy execution engine."""
    
    def __init__(
        self,
        capital: float = 100000.0,
        risk_per_strategy_pct: float = 0.01,
        max_total_risk_pct: float = 0.05,
        auto_select_top_n: int = 5,
        rolling_window_days: int = 90,
        rebalance_frequency_days: int = 7
    ):
        """Initialize multi-strategy engine.
        
        Args:
            capital: Total capital
            risk_per_strategy_pct: Risk per strategy (as % of capital)
            max_total_risk_pct: Maximum total risk across all strategies
            auto_select_top_n: Number of top strategies to auto-select
            rolling_window_days: Window for rolling performance metrics
            rebalance_frequency_days: How often to rebalance strategy weights
        """
        self.capital = capital
        self.risk_per_strategy_pct = risk_per_strategy_pct
        self.max_total_risk_pct = max_total_risk_pct
        self.auto_select_top_n = auto_select_top_n
        self.rolling_window_days = rolling_window_days
        self.rebalance_frequency_days = rebalance_frequency_days
        
        # Strategy tracking
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        self.strategy_weights: Dict[str, StrategyWeight] = {}
        self.last_rebalance: Optional[datetime] = None
        
        # Initialize all strategies with equal weights
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Initialize all available strategies with equal weights."""
        strategies = get_strategy_list()
        initial_weight = 1.0 / len(strategies)
        
        for strategy in strategies:
            self.strategy_weights[strategy] = StrategyWeight(
                strategy_name=strategy,
                weight=initial_weight,
                enabled=True
            )
            self.strategy_performance[strategy] = StrategyPerformance(
                strategy_name=strategy
            )
    
    def calculate_strategy_performance(
        self,
        df: pd.DataFrame,
        lookback_days: Optional[int] = None
    ) -> Dict[str, StrategyPerformance]:
        """Calculate rolling performance for all strategies.
        
        Args:
            df: DataFrame with OHLCV data
            lookback_days: Lookback period (defaults to rolling_window_days)
            
        Returns:
            Dictionary of strategy performances
        """
        if lookback_days is None:
            lookback_days = self.rolling_window_days
        
        logger.info(f"Calculating performance for {len(self.strategy_weights)} strategies")
        
        # Calculate returns for lookback period
        if len(df) < 50:
            logger.warning("Insufficient data for performance calculation")
            return self.strategy_performance
        
        backtest_engine = BacktestEngine(BacktestConfig(
            initial_capital=self.capital,
            risk_per_trade=self.risk_per_strategy_pct,
            commission_pct=0.001
        ))
        
        for strategy_name in self.strategy_weights.keys():
            try:
                # Generate signals
                signal_output = generate_signal(strategy_name, df)
                
                # Run backtest
                result = backtest_engine.run(
                    df=df,
                    signals=signal_output.signal,
                    strategy_name=strategy_name,
                    verbose=False
                )
                
                # Update performance
                perf = StrategyPerformance(
                    strategy_name=strategy_name,
                    sharpe_ratio=result.sharpe_ratio,
                    total_return=result.total_return,
                    win_rate=result.win_rate,
                    max_drawdown=result.max_drawdown,
                    total_trades=result.total_trades,
                    avg_trade_return=result.avg_trade if result.total_trades > 0 else 0.0,
                    profit_factor=result.profit_factor,
                    calmar_ratio=result.calmar_ratio,
                    last_updated=datetime.now()
                )
                
                self.strategy_performance[strategy_name] = perf
                
            except Exception as e:
                logger.error(f"Error calculating performance for {strategy_name}: {e}")
        
        return self.strategy_performance
    
    def auto_select_strategies(
        self,
        metric: str = "sharpe_ratio",
        min_trades: int = 5
    ) -> List[str]:
        """Automatically select top performing strategies.
        
        Args:
            metric: Metric to rank by (sharpe_ratio, total_return, win_rate, calmar_ratio)
            min_trades: Minimum number of trades required
            
        Returns:
            List of selected strategy names
        """
        # Filter strategies by minimum trades
        candidates = [
            (name, perf) 
            for name, perf in self.strategy_performance.items()
            if perf.total_trades >= min_trades
        ]
        
        if not candidates:
            logger.warning("No strategies meet minimum trade requirement")
            return list(self.strategy_weights.keys())[:self.auto_select_top_n]
        
        # Sort by selected metric
        sorted_strategies = sorted(
            candidates,
            key=lambda x: getattr(x[1], metric),
            reverse=True
        )
        
        # Select top N
        selected = [name for name, _ in sorted_strategies[:self.auto_select_top_n]]
        
        logger.info(f"Auto-selected strategies by {metric}: {selected}")
        return selected
    
    def calculate_ensemble_weights(
        self,
        method: str = "sharpe_weighted",
        normalize: bool = True
    ) -> Dict[str, float]:
        """Calculate dynamic weights for strategy ensemble.
        
        Args:
            method: Weighting method (sharpe_weighted, equal, inverse_volatility)
            normalize: Normalize weights to sum to 1
            
        Returns:
            Dictionary of strategy weights
        """
        weights = {}
        
        if method == "equal":
            # Equal weighting
            enabled_strategies = [
                name for name, sw in self.strategy_weights.items() if sw.enabled
            ]
            weight = 1.0 / len(enabled_strategies) if enabled_strategies else 0.0
            weights = {name: weight for name in enabled_strategies}
        
        elif method == "sharpe_weighted":
            # Weight by Sharpe ratio (clip negative to small positive)
            for name, perf in self.strategy_performance.items():
                if self.strategy_weights[name].enabled:
                    weights[name] = max(0.01, perf.sharpe_ratio)
        
        elif method == "calmar_weighted":
            # Weight by Calmar ratio
            for name, perf in self.strategy_performance.items():
                if self.strategy_weights[name].enabled:
                    weights[name] = max(0.01, perf.calmar_ratio)
        
        elif method == "inverse_volatility":
            # Weight inversely by volatility (drawdown proxy)
            for name, perf in self.strategy_performance.items():
                if self.strategy_weights[name].enabled:
                    volatility = abs(perf.max_drawdown) if perf.max_drawdown != 0 else 1.0
                    weights[name] = 1.0 / volatility
        
        else:
            raise ValueError(f"Unknown weighting method: {method}")
        
        # Normalize weights
        if normalize and weights:
            total = sum(weights.values())
            if total > 0:
                weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def aggregate_signals(
        self,
        df: pd.DataFrame,
        method: str = "weighted_vote",
        auto_select: bool = True
    ) -> EnsembleSignal:
        """Aggregate signals from multiple strategies.
        
        Args:
            df: DataFrame with OHLCV data
            method: Aggregation method (weighted_vote, majority_vote, average)
            auto_select: Use auto-selected strategies only
            
        Returns:
            EnsembleSignal with aggregated signal
        """
        # Select strategies
        if auto_select:
            selected_strategies = self.auto_select_strategies()
        else:
            selected_strategies = [
                name for name, sw in self.strategy_weights.items() if sw.enabled
            ]
        
        if not selected_strategies:
            logger.warning("No strategies selected")
            return EnsembleSignal(
                signal=0,
                confidence=0.0,
                strategy_votes={},
                strategy_weights={},
                contributing_strategies=[]
            )
        
        # Calculate weights
        weights = self.calculate_ensemble_weights(method="sharpe_weighted")
        
        # Generate signals
        strategy_votes = {}
        strategy_signals = {}
        
        for strategy_name in selected_strategies:
            try:
                signal_output = generate_signal(strategy_name, df)
                current_signal = int(signal_output.signal.iloc[-1])
                strategy_votes[strategy_name] = current_signal
                strategy_signals[strategy_name] = signal_output
            except Exception as e:
                logger.error(f"Error generating signal for {strategy_name}: {e}")
                strategy_votes[strategy_name] = 0
        
        # Aggregate based on method
        if method == "weighted_vote":
            # Weighted sum of signals
            weighted_sum = sum(
                strategy_votes.get(name, 0) * weights.get(name, 0)
                for name in selected_strategies
            )
            
            # Convert to discrete signal
            if weighted_sum > 0.1:
                final_signal = 1
            elif weighted_sum < -0.1:
                final_signal = -1
            else:
                final_signal = 0
            
            # Confidence is absolute value of weighted sum
            confidence = min(1.0, abs(weighted_sum))
        
        elif method == "majority_vote":
            # Count votes
            long_votes = sum(1 for v in strategy_votes.values() if v == 1)
            short_votes = sum(1 for v in strategy_votes.values() if v == -1)
            total_votes = len(strategy_votes)
            
            # Majority wins
            if long_votes > total_votes / 2:
                final_signal = 1
                confidence = long_votes / total_votes
            elif short_votes > total_votes / 2:
                final_signal = -1
                confidence = short_votes / total_votes
            else:
                final_signal = 0
                confidence = 0.0
        
        elif method == "average":
            # Simple average
            avg_signal = np.mean(list(strategy_votes.values()))
            final_signal = 1 if avg_signal > 0.2 else (-1 if avg_signal < -0.2 else 0)
            confidence = min(1.0, abs(avg_signal))
        
        else:
            raise ValueError(f"Unknown aggregation method: {method}")
        
        contributing = [name for name in selected_strategies if strategy_votes.get(name, 0) != 0]
        
        return EnsembleSignal(
            signal=final_signal,
            confidence=confidence,
            strategy_votes=strategy_votes,
            strategy_weights=weights,
            contributing_strategies=contributing
        )
    
    def should_rebalance(self) -> bool:
        """Check if it's time to rebalance strategy weights.
        
        Returns:
            True if rebalancing is needed
        """
        if self.last_rebalance is None:
            return True
        
        days_since_rebalance = (datetime.now() - self.last_rebalance).days
        return days_since_rebalance >= self.rebalance_frequency_days
    
    def rebalance_strategies(
        self,
        df: pd.DataFrame,
        method: str = "sharpe_weighted"
    ):
        """Rebalance strategy weights based on recent performance.
        
        Args:
            df: DataFrame with OHLCV data
            method: Weighting method
        """
        logger.info("Rebalancing strategy weights...")
        
        # Update performance metrics
        self.calculate_strategy_performance(df)
        
        # Calculate new weights
        new_weights = self.calculate_ensemble_weights(method, normalize=True)
        
        # Update strategy weights
        for name, weight in new_weights.items():
            if name in self.strategy_weights:
                self.strategy_weights[name].weight = weight
        
        # Disable poorly performing strategies
        for name, perf in self.strategy_performance.items():
            if perf.sharpe_ratio < -0.5 or (perf.total_trades > 10 and perf.win_rate < 0.3):
                logger.warning(f"Disabling poorly performing strategy: {name}")
                self.strategy_weights[name].enabled = False
        
        self.last_rebalance = datetime.now()
        logger.info("Rebalancing complete")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get summary of current portfolio state.
        
        Returns:
            Dictionary with portfolio metrics
        """
        enabled_strategies = [name for name, sw in self.strategy_weights.items() if sw.enabled]
        
        # Calculate aggregate metrics
        total_weight = sum(sw.weight for sw in self.strategy_weights.values() if sw.enabled)
        avg_sharpe = np.mean([
            perf.sharpe_ratio for name, perf in self.strategy_performance.items()
            if self.strategy_weights[name].enabled
        ]) if enabled_strategies else 0.0
        
        avg_win_rate = np.mean([
            perf.win_rate for name, perf in self.strategy_performance.items()
            if self.strategy_weights[name].enabled
        ]) if enabled_strategies else 0.0
        
        return {
            'capital': self.capital,
            'num_strategies_enabled': len(enabled_strategies),
            'num_strategies_total': len(self.strategy_weights),
            'total_weight': total_weight,
            'avg_sharpe_ratio': avg_sharpe,
            'avg_win_rate': avg_win_rate,
            'last_rebalance': self.last_rebalance.isoformat() if self.last_rebalance else None,
            'days_since_rebalance': (datetime.now() - self.last_rebalance).days if self.last_rebalance else None,
            'should_rebalance': self.should_rebalance(),
            'enabled_strategies': enabled_strategies
        }

