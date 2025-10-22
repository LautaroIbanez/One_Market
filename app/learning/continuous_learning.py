"""Continuous Learning Pipeline.

This module implements automated retraining and recalibration of strategies:
- Automated daily/weekly backtests with recent data
- Parameter recalibration based on rolling performance
- Strategy weight updates
- Performance tracking and historical comparison
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging
from pydantic import BaseModel, Field

from app.data.store import DataStore
from app.strategy.multi_strategy_engine import MultiStrategyEngine
from app.research.optimization import OptimizationStorage, bayesian_optimize, BayesianConfig
from app.research.signals import get_strategy_list

logger = logging.getLogger(__name__)


class LearningConfig(BaseModel):
    """Configuration for continuous learning pipeline."""
    symbol: str
    timeframe: str
    recalibration_frequency_days: int = Field(default=7, description="Days between recalibrations")
    lookback_days: int = Field(default=90, description="Days of data for training")
    min_trades_required: int = Field(default=10, description="Minimum trades for valid backtest")
    performance_threshold: float = Field(default=0.0, description="Minimum Sharpe for enabled strategy")
    auto_disable_poor_performers: bool = Field(default=True, description="Auto-disable bad strategies")


class PerformanceSnapshot(BaseModel):
    """Snapshot of strategy performance at a point in time."""
    timestamp: datetime = Field(default_factory=datetime.now)
    strategy_name: str
    sharpe_ratio: float
    total_return: float
    win_rate: float
    max_drawdown: float
    total_trades: int
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class RecalibrationResult(BaseModel):
    """Result of a recalibration run."""
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str
    timeframe: str
    num_strategies_updated: int
    performance_improvements: Dict[str, float] = Field(default_factory=dict)
    newly_disabled: List[str] = Field(default_factory=list)
    newly_enabled: List[str] = Field(default_factory=list)
    duration_seconds: float = 0.0
    
    class Config:
        arbitrary_types_allowed = True


class ContinuousLearningPipeline:
    """Automated learning and recalibration system."""
    
    def __init__(
        self,
        config: LearningConfig,
        storage_path: str = "storage/learning"
    ):
        """Initialize continuous learning pipeline.
        
        Args:
            config: Learning configuration
            storage_path: Path to store learning history
        """
        self.config = config
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.storage_path / "performance_history.json"
        self.config_file = self.storage_path / "strategy_configs.json"
        self.recalibration_log_file = self.storage_path / "recalibration_log.json"
        
        # Initialize components
        self.data_store = DataStore()
        self.opt_storage = OptimizationStorage()
        
        # Load history
        self.performance_history: List[PerformanceSnapshot] = self._load_history()
        self.strategy_configs: Dict[str, Dict] = self._load_configs()
        self.recalibration_log: List[RecalibrationResult] = self._load_recalibration_log()
    
    def _load_history(self) -> List[PerformanceSnapshot]:
        """Load performance history from disk."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                return [PerformanceSnapshot(**item) for item in data]
            except Exception as e:
                logger.error(f"Error loading history: {e}")
        return []
    
    def _save_history(self):
        """Save performance history to disk."""
        try:
            data = [s.dict() for s in self.performance_history]
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def _load_configs(self) -> Dict[str, Dict]:
        """Load strategy configurations from disk."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading configs: {e}")
        return {}
    
    def _save_configs(self):
        """Save strategy configurations to disk."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.strategy_configs, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving configs: {e}")
    
    def _load_recalibration_log(self) -> List[RecalibrationResult]:
        """Load recalibration log from disk."""
        if self.recalibration_log_file.exists():
            try:
                with open(self.recalibration_log_file, 'r') as f:
                    data = json.load(f)
                return [RecalibrationResult(**item) for item in data]
            except Exception as e:
                logger.error(f"Error loading recalibration log: {e}")
        return []
    
    def _save_recalibration_log(self):
        """Save recalibration log to disk."""
        try:
            data = [r.dict() for r in self.recalibration_log]
            with open(self.recalibration_log_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving recalibration log: {e}")
    
    def should_recalibrate(self) -> bool:
        """Check if it's time to recalibrate.
        
        Returns:
            True if recalibration is needed
        """
        if not self.recalibration_log:
            return True
        
        last_recalibration = self.recalibration_log[-1].timestamp
        days_since = (datetime.now() - last_recalibration).days
        
        return days_since >= self.config.recalibration_frequency_days
    
    def run_daily_backtest(
        self,
        engine: Optional[MultiStrategyEngine] = None
    ) -> Dict[str, PerformanceSnapshot]:
        """Run daily backtest for all strategies.
        
        Args:
            engine: Optional MultiStrategyEngine instance
            
        Returns:
            Dictionary of strategy performance snapshots
        """
        logger.info(f"Running daily backtest for {self.config.symbol} {self.config.timeframe}")
        
        # Load data
        bars = self.data_store.read_bars(self.config.symbol, self.config.timeframe)
        if not bars or len(bars) < 100:
            logger.warning("Insufficient data for backtest")
            return {}
        
        df = pd.DataFrame([{
            'timestamp': bar.timestamp,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        } for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Use last N days
        if self.config.lookback_days and len(df) > self.config.lookback_days:
            df = df.tail(self.config.lookback_days)
        
        # Create or use engine
        if engine is None:
            engine = MultiStrategyEngine(
                capital=100000.0,
                rolling_window_days=self.config.lookback_days
            )
        
        # Calculate performance
        performance = engine.calculate_strategy_performance(df)
        
        # Create snapshots
        snapshots = {}
        for name, perf in performance.items():
            snapshot = PerformanceSnapshot(
                timestamp=datetime.now(),
                strategy_name=name,
                sharpe_ratio=perf.sharpe_ratio,
                total_return=perf.total_return,
                win_rate=perf.win_rate,
                max_drawdown=perf.max_drawdown,
                total_trades=perf.total_trades,
                parameters=self.strategy_configs.get(name, {})
            )
            snapshots[name] = snapshot
            self.performance_history.append(snapshot)
        
        # Save history
        self._save_history()
        
        logger.info(f"Daily backtest complete: {len(snapshots)} strategies evaluated")
        return snapshots
    
    def recalibrate_strategy(
        self,
        strategy_name: str,
        df: pd.DataFrame,
        param_space: Dict[str, Dict[str, Any]],
        n_calls: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Recalibrate a single strategy using Bayesian optimization.
        
        Args:
            strategy_name: Strategy to recalibrate
            df: DataFrame with OHLCV data
            param_space: Parameter space for optimization
            n_calls: Number of optimization calls
            
        Returns:
            Best parameters found, or None if failed
        """
        logger.info(f"Recalibrating {strategy_name}...")
        
        try:
            config = BayesianConfig(
                strategy_name=strategy_name,
                symbol=self.config.symbol,
                timeframe=self.config.timeframe,
                param_space=param_space,
                scoring_metric="sharpe_ratio",
                maximize=True,
                n_calls=n_calls,
                n_initial_points=min(10, n_calls // 3)
            )
            
            results = bayesian_optimize(
                df=df,
                config=config,
                storage=self.opt_storage,
                verbose=False
            )
            
            if results and len(results) > 0:
                best_params = results[0].parameters
                logger.info(f"Recalibration successful: {best_params}")
                return best_params
            
        except Exception as e:
            logger.error(f"Recalibration failed for {strategy_name}: {e}")
        
        return None
    
    def run_recalibration(
        self,
        strategies_to_update: Optional[List[str]] = None,
        force: bool = False
    ) -> RecalibrationResult:
        """Run full recalibration pipeline.
        
        Args:
            strategies_to_update: Specific strategies to update (None = all)
            force: Force recalibration even if not due
            
        Returns:
            RecalibrationResult with outcomes
        """
        start_time = datetime.now()
        
        if not force and not self.should_recalibrate():
            logger.info("Recalibration not due yet")
            return RecalibrationResult(
                symbol=self.config.symbol,
                timeframe=self.config.timeframe,
                num_strategies_updated=0
            )
        
        logger.info("Starting recalibration pipeline...")
        
        # Load data
        bars = self.data_store.read_bars(self.config.symbol, self.config.timeframe)
        if not bars:
            logger.error("No data available")
            return RecalibrationResult(
                symbol=self.config.symbol,
                timeframe=self.config.timeframe,
                num_strategies_updated=0
            )
        
        df = pd.DataFrame([{
            'timestamp': bar.timestamp,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        } for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        if self.config.lookback_days and len(df) > self.config.lookback_days:
            df = df.tail(self.config.lookback_days)
        
        # Run backtest first
        engine = MultiStrategyEngine(capital=100000.0)
        snapshots = self.run_daily_backtest(engine)
        
        # Determine which strategies to update
        if strategies_to_update is None:
            strategies_to_update = get_strategy_list()
        
        # Track results
        performance_improvements = {}
        newly_disabled = []
        newly_enabled = []
        num_updated = 0
        
        # Define parameter spaces (simplified versions)
        param_spaces = {
            "ema_triple_momentum": {
                'fast_period': {'type': 'integer', 'low': 5, 'high': 12},
                'mid_period': {'type': 'integer', 'low': 15, 'high': 30}
            },
            "atr_channel_breakout_volume": {
                'atr_multiplier': {'type': 'real', 'low': 1.5, 'high': 3.0},
                'volume_threshold': {'type': 'real', 'low': 1.2, 'high': 2.0}
            }
        }
        
        for strategy_name in strategies_to_update:
            # Get current performance
            current_perf = snapshots.get(strategy_name)
            if not current_perf:
                continue
            
            # Check if should recalibrate
            if current_perf.total_trades < self.config.min_trades_required:
                logger.info(f"Skipping {strategy_name}: insufficient trades ({current_perf.total_trades})")
                continue
            
            # Recalibrate if param space defined
            if strategy_name in param_spaces:
                new_params = self.recalibrate_strategy(
                    strategy_name,
                    df,
                    param_spaces[strategy_name],
                    n_calls=20
                )
                
                if new_params:
                    old_sharpe = current_perf.sharpe_ratio
                    # Store new params
                    self.strategy_configs[strategy_name] = new_params
                    num_updated += 1
                    
                    # Re-evaluate with new params
                    # (Simplified: in production, would run new backtest)
                    performance_improvements[strategy_name] = 0.0  # Placeholder
            
            # Auto-disable poor performers
            if self.config.auto_disable_poor_performers:
                if current_perf.sharpe_ratio < self.config.performance_threshold:
                    if strategy_name not in newly_disabled:
                        newly_disabled.append(strategy_name)
                        logger.warning(f"Disabling poor performer: {strategy_name} (Sharpe: {current_perf.sharpe_ratio:.2f})")
        
        # Save configs
        self._save_configs()
        
        # Create result
        duration = (datetime.now() - start_time).total_seconds()
        result = RecalibrationResult(
            timestamp=datetime.now(),
            symbol=self.config.symbol,
            timeframe=self.config.timeframe,
            num_strategies_updated=num_updated,
            performance_improvements=performance_improvements,
            newly_disabled=newly_disabled,
            newly_enabled=newly_enabled,
            duration_seconds=duration
        )
        
        # Log result
        self.recalibration_log.append(result)
        self._save_recalibration_log()
        
        logger.info(f"Recalibration complete: {num_updated} strategies updated in {duration:.1f}s")
        return result
    
    def get_performance_trend(
        self,
        strategy_name: str,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """Get performance trend for a strategy.
        
        Args:
            strategy_name: Strategy name
            lookback_days: Lookback period
            
        Returns:
            Dictionary with trend analysis
        """
        # Filter history
        cutoff = datetime.now() - timedelta(days=lookback_days)
        recent = [
            s for s in self.performance_history
            if s.strategy_name == strategy_name and s.timestamp >= cutoff
        ]
        
        if not recent:
            return {'strategy': strategy_name, 'data_points': 0}
        
        # Calculate trends
        sharpe_values = [s.sharpe_ratio for s in recent]
        return_values = [s.total_return for s in recent]
        
        return {
            'strategy': strategy_name,
            'data_points': len(recent),
            'avg_sharpe': np.mean(sharpe_values),
            'sharpe_trend': 'improving' if len(sharpe_values) > 1 and sharpe_values[-1] > sharpe_values[0] else 'declining',
            'avg_return': np.mean(return_values),
            'latest_sharpe': sharpe_values[-1] if sharpe_values else 0.0,
            'latest_return': return_values[-1] if return_values else 0.0
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics.
        
        Returns:
            Dictionary with system health
        """
        if not self.recalibration_log:
            return {
                'status': 'new',
                'last_recalibration': None,
                'days_since_recalibration': None
            }
        
        last_recal = self.recalibration_log[-1]
        days_since = (datetime.now() - last_recal.timestamp).days
        
        return {
            'status': 'healthy' if days_since < self.config.recalibration_frequency_days else 'needs_recalibration',
            'last_recalibration': last_recal.timestamp.isoformat(),
            'days_since_recalibration': days_since,
            'total_recalibrations': len(self.recalibration_log),
            'last_num_updated': last_recal.num_strategies_updated,
            'last_duration_seconds': last_recal.duration_seconds,
            'should_recalibrate': self.should_recalibrate()
        }



