"""Walk-forward optimization.

This module implements walk-forward analysis for strategy optimization
and out-of-sample validation.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Callable, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class WalkForwardConfig(BaseModel):
    """Configuration for walk-forward analysis."""
    
    train_period: int = Field(default=180, description="Training period in days")
    test_period: int = Field(default=30, description="Testing period in days")
    step_size: int = Field(default=30, description="Step size for rolling window")
    anchored: bool = Field(default=False, description="Use anchored (expanding) window")
    min_train_size: int = Field(default=60, description="Minimum training size in days")


class WalkForwardResult(BaseModel):
    """Result of a single walk-forward iteration."""
    
    iteration: int = Field(..., description="Iteration number")
    train_start: datetime = Field(..., description="Training start date")
    train_end: datetime = Field(..., description="Training end date")
    test_start: datetime = Field(..., description="Test start date")
    test_end: datetime = Field(..., description="Test end date")
    
    # Optimal parameters found in training
    optimal_params: Dict[str, Any] = Field(..., description="Optimal parameters")
    
    # In-sample (training) metrics
    is_total_return: float = Field(..., description="IS total return")
    is_sharpe: float = Field(..., description="IS Sharpe ratio")
    is_max_dd: float = Field(..., description="IS max drawdown")
    is_trades: int = Field(..., description="IS number of trades")
    
    # Out-of-sample (test) metrics
    oos_total_return: float = Field(..., description="OOS total return")
    oos_sharpe: float = Field(..., description="OOS Sharpe ratio")
    oos_max_dd: float = Field(..., description="OOS max drawdown")
    oos_trades: int = Field(..., description="OOS number of trades")
    
    # Efficiency metrics
    efficiency_ratio: float = Field(..., description="OOS return / IS return")
    degradation: float = Field(..., description="Performance degradation")
    
    class Config:
        arbitrary_types_allowed = True


class WalkForwardSummary(BaseModel):
    """Summary of walk-forward analysis."""
    
    total_iterations: int = Field(..., description="Total iterations")
    
    # Aggregated OOS metrics
    oos_total_return: float = Field(..., description="Combined OOS return")
    oos_avg_return: float = Field(..., description="Average OOS return per period")
    oos_avg_sharpe: float = Field(..., description="Average OOS Sharpe")
    oos_max_dd: float = Field(..., description="Maximum OOS drawdown")
    oos_win_rate: float = Field(..., description="OOS win rate (% positive periods)")
    
    # Consistency metrics
    avg_efficiency_ratio: float = Field(..., description="Average efficiency ratio")
    consistency_score: float = Field(..., description="Consistency score (0-1)")
    avg_degradation: float = Field(..., description="Average degradation")
    
    # Best iteration
    best_iteration: int = Field(..., description="Best performing iteration")
    best_oos_return: float = Field(..., description="Best OOS return")
    
    # Results list
    iterations: List[WalkForwardResult] = Field(default_factory=list, description="All iterations")


class WalkForwardOptimizer:
    """Walk-forward optimizer."""
    
    def __init__(self, config: Optional[WalkForwardConfig] = None):
        """Initialize optimizer.
        
        Args:
            config: Walk-forward configuration
        """
        self.config = config or WalkForwardConfig()
    
    def optimize(
        self,
        df: pd.DataFrame,
        strategy_func: Callable,
        param_grid: Dict[str, List[Any]],
        objective: str = 'sharpe',
        verbose: bool = True
    ) -> WalkForwardSummary:
        """Run walk-forward optimization.
        
        Args:
            df: DataFrame with OHLCV data
            strategy_func: Function that generates signals given df and params
            param_grid: Dictionary of parameter ranges to test
            objective: Optimization objective ('sharpe', 'return', 'calmar')
            verbose: Print progress
            
        Returns:
            WalkForwardSummary with all results
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Walk-Forward Optimization")
            print(f"{'='*60}")
            print(f"Train: {self.config.train_period} days")
            print(f"Test: {self.config.test_period} days")
            print(f"Step: {self.config.step_size} days")
            print(f"Anchored: {self.config.anchored}")
        
        # Convert timestamps to datetime
        df = df.copy()
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Calculate total data span
        total_days = (df['datetime'].iloc[-1] - df['datetime'].iloc[0]).days
        
        # Calculate number of iterations
        if self.config.anchored:
            num_iterations = (total_days - self.config.train_period - self.config.test_period) // self.config.step_size + 1
        else:
            num_iterations = (total_days - self.config.train_period - self.config.test_period) // self.config.step_size + 1
        
        if verbose:
            print(f"\nTotal days: {total_days}")
            print(f"Iterations: {num_iterations}")
        
        # Run iterations
        results = []
        for i in range(num_iterations):
            if verbose:
                print(f"\nIteration {i+1}/{num_iterations}")
            
            result = self._run_iteration(
                df, i, strategy_func, param_grid, objective, verbose
            )
            
            if result:
                results.append(result)
        
        # Calculate summary
        summary = self._calculate_summary(results, verbose)
        
        return summary
    
    def _run_iteration(
        self,
        df: pd.DataFrame,
        iteration: int,
        strategy_func: Callable,
        param_grid: Dict[str, List[Any]],
        objective: str,
        verbose: bool
    ) -> Optional[WalkForwardResult]:
        """Run single walk-forward iteration.
        
        Args:
            df: Full DataFrame
            iteration: Iteration number
            strategy_func: Strategy function
            param_grid: Parameter grid
            objective: Optimization objective
            verbose: Print progress
            
        Returns:
            WalkForwardResult or None if insufficient data
        """
        # Calculate date ranges
        start_idx = iteration * self.config.step_size
        
        if self.config.anchored:
            train_start_idx = 0
        else:
            train_start_idx = start_idx
        
        train_end_idx = start_idx + self.config.train_period
        test_start_idx = train_end_idx
        test_end_idx = test_start_idx + self.config.test_period
        
        # Check bounds
        if test_end_idx > len(df):
            return None
        
        # Split data
        train_df = df.iloc[train_start_idx:train_end_idx].copy()
        test_df = df.iloc[test_start_idx:test_end_idx].copy()
        
        if len(train_df) < self.config.min_train_size:
            return None
        
        # Get dates
        train_start = train_df['datetime'].iloc[0]
        train_end = train_df['datetime'].iloc[-1]
        test_start = test_df['datetime'].iloc[0]
        test_end = test_df['datetime'].iloc[-1]
        
        if verbose:
            print(f"  Train: {train_start.date()} to {train_end.date()}")
            print(f"  Test:  {test_start.date()} to {test_end.date()}")
        
        # Optimize on training data
        optimal_params, is_metrics = self._optimize_params(
            train_df, strategy_func, param_grid, objective, verbose
        )
        
        if verbose:
            print(f"  Optimal params: {optimal_params}")
            print(f"  IS {objective}: {is_metrics[objective]:.4f}")
        
        # Test on out-of-sample data
        oos_metrics = self._backtest_params(
            test_df, strategy_func, optimal_params, verbose
        )
        
        if verbose:
            print(f"  OOS {objective}: {oos_metrics[objective]:.4f}")
        
        # Calculate efficiency
        efficiency = oos_metrics['return'] / is_metrics['return'] if is_metrics['return'] != 0 else 0
        degradation = is_metrics[objective] - oos_metrics[objective]
        
        return WalkForwardResult(
            iteration=iteration,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
            optimal_params=optimal_params,
            is_total_return=is_metrics['return'],
            is_sharpe=is_metrics['sharpe'],
            is_max_dd=is_metrics['max_dd'],
            is_trades=is_metrics['trades'],
            oos_total_return=oos_metrics['return'],
            oos_sharpe=oos_metrics['sharpe'],
            oos_max_dd=oos_metrics['max_dd'],
            oos_trades=oos_metrics['trades'],
            efficiency_ratio=efficiency,
            degradation=degradation
        )
    
    def _optimize_params(
        self,
        df: pd.DataFrame,
        strategy_func: Callable,
        param_grid: Dict[str, List[Any]],
        objective: str,
        verbose: bool
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """Optimize parameters on training data.
        
        Args:
            df: Training DataFrame
            strategy_func: Strategy function
            param_grid: Parameter grid
            objective: Optimization objective
            verbose: Print progress
            
        Returns:
            Tuple of (optimal_params, metrics)
        """
        # Generate parameter combinations
        from itertools import product
        
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(product(*values))
        
        best_params = None
        best_score = -np.inf
        best_metrics = None
        
        for combo in combinations:
            params = dict(zip(keys, combo))
            
            try:
                metrics = self._backtest_params(df, strategy_func, params, False)
                score = metrics[objective]
                
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_metrics = metrics
            except Exception as e:
                if verbose:
                    print(f"    Error with params {params}: {e}")
                continue
        
        return best_params, best_metrics
    
    def _backtest_params(
        self,
        df: pd.DataFrame,
        strategy_func: Callable,
        params: Dict[str, Any],
        verbose: bool
    ) -> Dict[str, float]:
        """Backtest with specific parameters.
        
        Args:
            df: DataFrame
            strategy_func: Strategy function
            params: Parameters
            verbose: Print progress
            
        Returns:
            Dictionary of metrics
        """
        # Generate signals
        signals = strategy_func(df, **params)
        
        # Simple return calculation (vectorized)
        returns = df['close'].pct_change()
        strategy_returns = signals.shift(1) * returns
        
        # Calculate metrics
        total_return = (1 + strategy_returns).prod() - 1
        sharpe = (strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)) if strategy_returns.std() > 0 else 0
        
        # Drawdown
        cum_returns = (1 + strategy_returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        max_dd = abs(drawdown.min())
        
        # Trades
        signal_changes = (signals != signals.shift(1)).sum()
        
        return {
            'return': float(total_return),
            'sharpe': float(sharpe),
            'max_dd': float(max_dd),
            'trades': int(signal_changes),
            'calmar': float(total_return / max_dd) if max_dd > 0 else 0
        }
    
    def _calculate_summary(
        self,
        results: List[WalkForwardResult],
        verbose: bool
    ) -> WalkForwardSummary:
        """Calculate walk-forward summary.
        
        Args:
            results: List of iteration results
            verbose: Print summary
            
        Returns:
            WalkForwardSummary
        """
        if not results:
            raise ValueError("No valid results to summarize")
        
        # Aggregate OOS metrics
        oos_returns = [r.oos_total_return for r in results]
        oos_sharpes = [r.oos_sharpe for r in results]
        oos_dds = [r.oos_max_dd for r in results]
        efficiency_ratios = [r.efficiency_ratio for r in results]
        degradations = [r.degradation for r in results]
        
        # Combined return
        oos_total_return = np.prod([1 + r for r in oos_returns]) - 1
        
        # Win rate
        oos_win_rate = sum(1 for r in oos_returns if r > 0) / len(oos_returns)
        
        # Consistency score (% of periods with positive returns)
        consistency = oos_win_rate
        
        # Best iteration
        best_idx = np.argmax(oos_returns)
        
        summary = WalkForwardSummary(
            total_iterations=len(results),
            oos_total_return=float(oos_total_return),
            oos_avg_return=float(np.mean(oos_returns)),
            oos_avg_sharpe=float(np.mean(oos_sharpes)),
            oos_max_dd=float(max(oos_dds)),
            oos_win_rate=float(oos_win_rate),
            avg_efficiency_ratio=float(np.mean(efficiency_ratios)),
            consistency_score=float(consistency),
            avg_degradation=float(np.mean(degradations)),
            best_iteration=int(best_idx),
            best_oos_return=float(oos_returns[best_idx]),
            iterations=results
        )
        
        if verbose:
            self._print_summary(summary)
        
        return summary
    
    def _print_summary(self, summary: WalkForwardSummary):
        """Print walk-forward summary.
        
        Args:
            summary: WalkForwardSummary
        """
        print(f"\n{'='*60}")
        print(f"WALK-FORWARD SUMMARY")
        print(f"{'='*60}")
        
        print(f"\n📊 Out-of-Sample Performance:")
        print(f"  Total Return: {summary.oos_total_return:.2%}")
        print(f"  Avg Return/Period: {summary.oos_avg_return:.2%}")
        print(f"  Avg Sharpe: {summary.oos_avg_sharpe:.2f}")
        print(f"  Max Drawdown: {summary.oos_max_dd:.2%}")
        print(f"  Win Rate: {summary.oos_win_rate:.2%}")
        
        print(f"\n📈 Robustness:")
        print(f"  Avg Efficiency: {summary.avg_efficiency_ratio:.2f}")
        print(f"  Consistency: {summary.consistency_score:.2%}")
        print(f"  Avg Degradation: {summary.avg_degradation:.4f}")
        
        print(f"\n🏆 Best Iteration:")
        print(f"  Iteration: {summary.best_iteration + 1}")
        print(f"  Return: {summary.best_oos_return:.2%}")
        
        print(f"{'='*60}\n")

