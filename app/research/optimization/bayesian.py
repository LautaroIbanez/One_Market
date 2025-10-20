"""Bayesian optimization for trading strategies.

This module provides Bayesian optimization using scikit-optimize
for efficient parameter search with fewer iterations.
"""
import uuid
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

try:
    from skopt import gp_minimize
    from skopt.space import Real, Integer, Categorical
    from skopt.utils import use_named_args
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False

from app.research.backtest.engine import BacktestEngine, BacktestConfig
from app.research.optimization.storage import OptimizationStorage, OptimizationResult


class BayesianConfig(BaseModel):
    """Configuration for Bayesian optimization."""
    
    strategy_name: str = Field(..., description="Strategy to optimize")
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe")
    param_space: Dict[str, Dict[str, Any]] = Field(..., description="Parameter space definition")
    scoring_metric: str = Field(default="sharpe_ratio", description="Metric to optimize")
    maximize: bool = Field(default=True, description="Maximize metric (False to minimize)")
    n_calls: int = Field(default=50, description="Number of optimization calls")
    n_initial_points: int = Field(default=10, description="Number of random initial points")
    random_state: Optional[int] = Field(default=42, description="Random state for reproducibility")


def _create_skopt_space(param_space: Dict[str, Dict[str, Any]]) -> List[Any]:
    """Create scikit-optimize search space from parameter space definition.
    
    Args:
        param_space: Parameter space definition
            Format: {param_name: {'type': 'real'|'integer'|'categorical', 'low': x, 'high': y, 'categories': [...]}}
    
    Returns:
        List of scikit-optimize space dimensions
    """
    if not SKOPT_AVAILABLE:
        raise ImportError("scikit-optimize is required for Bayesian optimization. Install with: pip install scikit-optimize")
    
    dimensions = []
    param_names = []
    
    for param_name, param_def in param_space.items():
        param_type = param_def.get('type', 'real')
        
        if param_type == 'real':
            dim = Real(
                low=param_def['low'],
                high=param_def['high'],
                name=param_name
            )
        elif param_type == 'integer':
            dim = Integer(
                low=param_def['low'],
                high=param_def['high'],
                name=param_name
            )
        elif param_type == 'categorical':
            dim = Categorical(
                categories=param_def['categories'],
                name=param_name
            )
        else:
            raise ValueError(f"Unknown parameter type: {param_type}")
        
        dimensions.append(dim)
        param_names.append(param_name)
    
    return dimensions, param_names


def bayesian_optimize(
    df: pd.DataFrame,
    config: BayesianConfig,
    backtest_config: Optional[BacktestConfig] = None,
    storage: Optional[OptimizationStorage] = None,
    verbose: bool = True
) -> List[OptimizationResult]:
    """Run Bayesian optimization.
    
    Args:
        df: DataFrame with OHLCV data
        config: Bayesian optimization configuration
        backtest_config: Backtest configuration (optional)
        storage: Optimization storage (optional)
        verbose: Show progress
        
    Returns:
        List of optimization results sorted by score
    """
    if not SKOPT_AVAILABLE:
        raise ImportError("scikit-optimize is required for Bayesian optimization. Install with: pip install scikit-optimize")
    
    if backtest_config is None:
        backtest_config = BacktestConfig(
            initial_capital=100000.0,
            risk_per_trade=0.02,
            commission_pct=0.001
        )
    
    if storage is None:
        storage = OptimizationStorage()
    
    # Create search space
    dimensions, param_names = _create_skopt_space(config.param_space)
    
    if verbose:
        print(f"Bayesian optimization: {config.n_calls} iterations")
        print(f"Parameters: {param_names}")
    
    # Store results
    results = []
    engine = BacktestEngine(backtest_config)
    
    # Objective function
    @use_named_args(dimensions)
    def objective(**params):
        run_id = str(uuid.uuid4())
        
        try:
            # Run backtest with these parameters
            backtest_result = engine.run(
                df=df,
                strategy_name=config.strategy_name,
                strategy_params=params,
                timeframe=config.timeframe
            )
            
            # Extract metrics from backtest result
            metrics_result = backtest_result
            
            # Extract score
            score = getattr(metrics_result, config.scoring_metric)
            
            # Create optimization result
            opt_result = OptimizationResult(
                run_id=run_id,
                strategy_name=config.strategy_name,
                symbol=config.symbol,
                timeframe=config.timeframe,
                parameters=params,
                metrics={
                    'sharpe_ratio': metrics_result.sharpe_ratio,
                    'total_return': metrics_result.total_return,
                    'total_return_pct': metrics_result.total_return_pct,
                    'max_drawdown': metrics_result.max_drawdown,
                    'win_rate': metrics_result.win_rate,
                    'total_trades': metrics_result.total_trades,
                    'avg_win': metrics_result.avg_win,
                    'avg_loss': metrics_result.avg_loss,
                    'profit_factor': metrics_result.profit_factor
                },
                score=score
            )
            
            results.append(opt_result)
            
            if verbose:
                print(f"Iteration {len(results)}: score={score:.4f}, params={params}")
            
            # Return negative score if minimizing
            return -score if config.maximize else score
            
        except Exception as e:
            if verbose:
                print(f"Error with params {params}: {e}")
            # Return worst possible score
            return 1e10 if config.maximize else -1e10
    
    # Run optimization
    result = gp_minimize(
        func=objective,
        dimensions=dimensions,
        n_calls=config.n_calls,
        n_initial_points=config.n_initial_points,
        random_state=config.random_state,
        verbose=False
    )
    
    # Sort results by score
    results.sort(key=lambda x: x.score, reverse=True)
    
    # Save results
    storage.save_results_batch(results)
    
    if verbose:
        print(f"\nCompleted Bayesian optimization: {len(results)} iterations")
        if results:
            best = results[0]
            print(f"Best score: {best.score:.4f}")
            print(f"Best parameters: {best.parameters}")
    
    return results


def suggest_next_parameters(
    past_results: List[OptimizationResult],
    param_space: Dict[str, Dict[str, Any]],
    n_suggestions: int = 5
) -> List[Dict[str, Any]]:
    """Suggest next parameters to try based on past results.
    
    Args:
        past_results: Previous optimization results
        param_space: Parameter space definition
        n_suggestions: Number of suggestions to return
        
    Returns:
        List of suggested parameter combinations
    """
    if not SKOPT_AVAILABLE:
        raise ImportError("scikit-optimize is required for parameter suggestions")
    
    # Create search space
    dimensions, param_names = _create_skopt_space(param_space)
    
    # Extract X (parameters) and y (scores)
    X = []
    y = []
    for r in past_results:
        param_values = [r.parameters.get(name) for name in param_names]
        X.append(param_values)
        y.append(-r.score)  # Minimize negative score
    
    # Use Gaussian Process to suggest next points
    from skopt import Optimizer
    
    opt = Optimizer(dimensions, random_state=42)
    opt.tell(X, y)
    
    suggestions = []
    for _ in range(n_suggestions):
        suggested = opt.ask()
        param_dict = dict(zip(param_names, suggested))
        suggestions.append(param_dict)
    
    return suggestions

