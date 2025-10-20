"""Grid search optimization for trading strategies.

This module provides grid search optimization capabilities for systematic
parameter tuning using exhaustive search.
"""
import uuid
from typing import Dict, List, Any, Optional
from itertools import product
import pandas as pd
from pydantic import BaseModel, Field
from tqdm import tqdm

from app.research.backtest.engine import BacktestEngine, BacktestConfig
from app.research.optimization.storage import OptimizationStorage, OptimizationResult


class GridSearchConfig(BaseModel):
    """Configuration for grid search optimization."""
    
    strategy_name: str = Field(..., description="Strategy to optimize")
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe")
    param_grid: Dict[str, List[Any]] = Field(..., description="Parameter grid")
    scoring_metric: str = Field(default="sharpe_ratio", description="Metric to optimize")
    maximize: bool = Field(default=True, description="Maximize metric (False to minimize)")
    n_jobs: int = Field(default=1, description="Number of parallel jobs")
    save_all_results: bool = Field(default=True, description="Save all results or only best")


def grid_search_optimize(
    df: pd.DataFrame,
    config: GridSearchConfig,
    backtest_config: Optional[BacktestConfig] = None,
    storage: Optional[OptimizationStorage] = None,
    verbose: bool = True
) -> List[OptimizationResult]:
    """Run grid search optimization.
    
    Args:
        df: DataFrame with OHLCV data
        config: Grid search configuration
        backtest_config: Backtest configuration (optional)
        storage: Optimization storage (optional)
        verbose: Show progress bar
        
    Returns:
        List of optimization results sorted by score
    """
    if backtest_config is None:
        backtest_config = BacktestConfig(
            initial_capital=100000.0,
            risk_per_trade=0.02,
            commission_pct=0.001
        )
    
    if storage is None:
        storage = OptimizationStorage()
    
    # Generate parameter combinations
    param_names = list(config.param_grid.keys())
    param_values = list(config.param_grid.values())
    param_combinations = list(product(*param_values))
    
    if verbose:
        print(f"Grid search: {len(param_combinations)} parameter combinations")
    
    results = []
    
    # Initialize backtest engine
    engine = BacktestEngine(backtest_config)
    
    # Iterate through parameter combinations
    iterator = tqdm(param_combinations) if verbose else param_combinations
    
    for param_tuple in iterator:
        params = dict(zip(param_names, param_tuple))
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
            if not config.maximize:
                score = -score
            
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
            
        except Exception as e:
            if verbose:
                print(f"Error with params {params}: {e}")
            continue
    
    # Sort by score
    results.sort(key=lambda x: x.score, reverse=True)
    
    # Save results
    if config.save_all_results:
        storage.save_results_batch(results)
    else:
        if results:
            storage.save_result(results[0])
    
    if verbose:
        print(f"\nCompleted grid search: {len(results)} successful runs")
        if results:
            best = results[0]
            print(f"Best score: {best.score:.4f}")
            print(f"Best parameters: {best.parameters}")
    
    return results


def analyze_grid_search_results(results: List[OptimizationResult]) -> pd.DataFrame:
    """Analyze grid search results.
    
    Args:
        results: List of optimization results
        
    Returns:
        DataFrame with analysis
    """
    data = []
    for r in results:
        row = {'score': r.score}
        row.update(r.parameters)
        row.update(r.metrics)
        data.append(row)
    
    df = pd.DataFrame(data)
    return df


def get_parameter_importance(results: List[OptimizationResult]) -> Dict[str, float]:
    """Calculate parameter importance based on score variance.
    
    Args:
        results: List of optimization results
        
    Returns:
        Dictionary of parameter importances
    """
    df = analyze_grid_search_results(results)
    
    # Get parameter columns
    param_cols = [col for col in df.columns if col not in ['score'] + list(results[0].metrics.keys())]
    
    importance = {}
    for param in param_cols:
        # Group by parameter value and calculate mean score variance
        grouped = df.groupby(param)['score'].agg(['mean', 'std'])
        # Importance is the range of mean scores
        importance[param] = grouped['mean'].max() - grouped['mean'].min()
    
    # Normalize
    total = sum(importance.values())
    if total > 0:
        importance = {k: v / total for k, v in importance.items()}
    
    return importance

