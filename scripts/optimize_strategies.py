"""Strategy optimization script for automated/scheduled runs.

This script runs parameter optimization for all strategies and updates
combination weights automatically.

Usage:
    python scripts/optimize_strategies.py --symbol BTC-USDT --timeframe 1h --method bayesian
    python scripts/optimize_strategies.py --symbol BTC-USDT --timeframe 4h --method grid --update-weights
"""
import argparse
import sys
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.store import DataStore
from app.research.optimization import (
    grid_search_optimize,
    bayesian_optimize,
    GridSearchConfig,
    BayesianConfig,
    OptimizationStorage
)
from app.research.signals import get_strategy_list


def optimize_strategy(
    strategy_name: str,
    symbol: str,
    timeframe: str,
    method: str = "bayesian",
    n_calls: int = 50,
    verbose: bool = True
) -> dict:
    """Optimize a single strategy.
    
    Args:
        strategy_name: Strategy to optimize
        symbol: Trading symbol
        timeframe: Timeframe
        method: Optimization method ('grid' or 'bayesian')
        n_calls: Number of optimization calls
        verbose: Print progress
        
    Returns:
        Best result dictionary
    """
    # Load data
    store = DataStore()
    df = store.read_dataframe(symbol, timeframe)
    
    if df.empty:
        print(f"No data available for {symbol} {timeframe}")
        return None
    
    storage = OptimizationStorage()
    
    # Define parameter spaces for each strategy
    param_spaces = {
        "atr_channel_breakout_volume": {
            'atr_period': {'type': 'integer', 'low': 10, 'high': 20},
            'atr_multiplier': {'type': 'real', 'low': 1.5, 'high': 3.0},
            'volume_ma_period': {'type': 'integer', 'low': 15, 'high': 30},
            'volume_threshold': {'type': 'real', 'low': 1.2, 'high': 2.0}
        },
        "vwap_zscore_reversion": {
            'vwap_period': {'type': 'integer', 'low': 15, 'high': 30},
            'zscore_entry': {'type': 'real', 'low': 1.5, 'high': 3.0},
            'zscore_exit': {'type': 'real', 'low': 0.3, 'high': 1.0}
        },
        "ema_triple_momentum": {
            'fast_period': {'type': 'integer', 'low': 5, 'high': 12},
            'mid_period': {'type': 'integer', 'low': 15, 'high': 30},
            'slow_period': {'type': 'integer', 'low': 40, 'high': 70},
            'rsi_bull_threshold': {'type': 'integer', 'low': 45, 'high': 55},
            'rsi_bear_threshold': {'type': 'integer', 'low': 45, 'high': 55}
        },
        "ma_crossover": {
            'fast_period': {'type': 'integer', 'low': 5, 'high': 15},
            'slow_period': {'type': 'integer', 'low': 15, 'high': 30}
        },
        "rsi_regime_pullback": {
            'rsi_period': {'type': 'integer', 'low': 10, 'high': 20},
            'oversold': {'type': 'integer', 'low': 25, 'high': 35},
            'overbought': {'type': 'integer', 'low': 65, 'high': 75},
            'regime_period': {'type': 'integer', 'low': 40, 'high': 60}
        }
    }
    
    if strategy_name not in param_spaces:
        print(f"No parameter space defined for {strategy_name}")
        return None
    
    param_space = param_spaces[strategy_name]
    
    if method == "bayesian":
        config = BayesianConfig(
            strategy_name=strategy_name,
            symbol=symbol,
            timeframe=timeframe,
            param_space=param_space,
            scoring_metric="sharpe_ratio",
            maximize=True,
            n_calls=n_calls,
            n_initial_points=min(10, n_calls // 5)
        )
        
        results = bayesian_optimize(
            df=df,
            config=config,
            storage=storage,
            verbose=verbose
        )
    
    elif method == "grid":
        # Convert parameter space to grid
        param_grid = {}
        for param_name, param_def in param_space.items():
            if param_def['type'] == 'integer':
                # Sample 3-5 points
                low, high = param_def['low'], param_def['high']
                step = max(1, (high - low) // 3)
                param_grid[param_name] = list(range(low, high + 1, step))
            elif param_def['type'] == 'real':
                # Sample 3 points
                low, high = param_def['low'], param_def['high']
                param_grid[param_name] = [low, (low + high) / 2, high]
        
        config = GridSearchConfig(
            strategy_name=strategy_name,
            symbol=symbol,
            timeframe=timeframe,
            param_grid=param_grid,
            scoring_metric="sharpe_ratio",
            maximize=True,
            save_all_results=True
        )
        
        results = grid_search_optimize(
            df=df,
            config=config,
            storage=storage,
            verbose=verbose
        )
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    if results and len(results) > 0:
        best = results[0]
        return {
            'strategy': strategy_name,
            'score': best.score,
            'parameters': best.parameters,
            'metrics': best.metrics
        }
    
    return None


def update_combination_weights(symbol: str, timeframe: str, output_file: str = "storage/strategy_weights.json"):
    """Update strategy combination weights based on optimization results.
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe
        output_file: Output file for weights
    """
    storage = OptimizationStorage()
    
    # Get best results for each strategy
    strategies = get_strategy_list()
    weights = {}
    
    print(f"\nCalculating weights based on optimization results...")
    
    for strategy in strategies:
        results = storage.get_best_parameters(strategy, symbol, timeframe, top_n=1)
        
        if results:
            best = results[0]
            # Use Sharpe ratio as weight (clip to positive)
            weight = max(0.01, best.score)
            weights[strategy] = weight
            print(f"  {strategy}: {weight:.4f} (Sharpe: {best.score:.4f})")
        else:
            # Default weight for strategies without optimization
            weights[strategy] = 0.1
            print(f"  {strategy}: 0.1000 (default, no optimization data)")
    
    # Normalize weights to sum to 1
    total_weight = sum(weights.values())
    normalized_weights = {k: v / total_weight for k, v in weights.items()}
    
    # Save weights
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    weights_data = {
        'symbol': symbol,
        'timeframe': timeframe,
        'updated_at': datetime.now().isoformat(),
        'weights': normalized_weights,
        'raw_scores': weights
    }
    
    with open(output_path, 'w') as f:
        json.dump(weights_data, f, indent=2)
    
    print(f"\nWeights saved to {output_file}")
    print("\nNormalized weights:")
    for strategy, weight in sorted(normalized_weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  {strategy}: {weight:.4f} ({weight*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Optimize trading strategies")
    parser.add_argument("--symbol", default="BTC-USDT", help="Trading symbol")
    parser.add_argument("--timeframe", default="1h", help="Timeframe")
    parser.add_argument("--method", choices=["grid", "bayesian"], default="bayesian", help="Optimization method")
    parser.add_argument("--n-calls", type=int, default=50, help="Number of optimization calls")
    parser.add_argument("--strategies", nargs="+", help="Specific strategies to optimize (default: all)")
    parser.add_argument("--update-weights", action="store_true", help="Update combination weights after optimization")
    parser.add_argument("--weights-output", default="storage/strategy_weights.json", help="Output file for weights")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("STRATEGY OPTIMIZATION")
    print("=" * 80)
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Method: {args.method}")
    print(f"Calls: {args.n_calls}")
    print("=" * 80)
    
    # Get strategies to optimize
    if args.strategies:
        strategies_to_optimize = args.strategies
    else:
        strategies_to_optimize = get_strategy_list()
    
    print(f"\nOptimizing {len(strategies_to_optimize)} strategies:")
    for s in strategies_to_optimize:
        print(f"  - {s}")
    
    # Optimize each strategy
    results = []
    for i, strategy in enumerate(strategies_to_optimize, 1):
        print(f"\n{'='*80}")
        print(f"[{i}/{len(strategies_to_optimize)}] Optimizing {strategy}...")
        print(f"{'='*80}")
        
        result = optimize_strategy(
            strategy_name=strategy,
            symbol=args.symbol,
            timeframe=args.timeframe,
            method=args.method,
            n_calls=args.n_calls,
            verbose=args.verbose
        )
        
        if result:
            results.append(result)
            print(f"\n✓ Completed {strategy}")
            print(f"  Best Score: {result['score']:.4f}")
            print(f"  Win Rate: {result['metrics']['win_rate']:.2%}")
            print(f"  Total Trades: {result['metrics']['total_trades']}")
        else:
            print(f"\n✗ Failed to optimize {strategy}")
    
    # Summary
    print(f"\n{'='*80}")
    print("OPTIMIZATION SUMMARY")
    print(f"{'='*80}")
    print(f"Completed: {len(results)}/{len(strategies_to_optimize)} strategies")
    
    if results:
        print("\nTop 5 strategies by Sharpe ratio:")
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        for i, result in enumerate(sorted_results[:5], 1):
            print(f"  {i}. {result['strategy']}: {result['score']:.4f}")
    
    # Update weights if requested
    if args.update_weights:
        print(f"\n{'='*80}")
        update_combination_weights(args.symbol, args.timeframe, args.weights_output)
    
    print(f"\n{'='*80}")
    print("DONE")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()

