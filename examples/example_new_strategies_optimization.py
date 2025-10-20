"""Example: New Strategies and Optimization.

This example demonstrates:
1. Using new atomic signal strategies (ATR Channel Breakout, VWAP Z-Score, EMA Triple Momentum)
2. Grid search optimization for parameter tuning
3. Bayesian optimization for efficient parameter search
4. Volatility-based entry/SL/TP ranges
5. Strategy ranking and selection

Usage:
    python examples/example_new_strategies_optimization.py
"""
import pandas as pd
from datetime import datetime

# Import data loading
from app.data.store import DataStore

# Import new strategies
from app.research.signals import (
    atr_channel_breakout_volume,
    vwap_zscore_reversion,
    ema_triple_momentum,
    get_strategy_list
)

# Import optimization
from app.research.optimization import (
    grid_search_optimize,
    bayesian_optimize,
    GridSearchConfig,
    BayesianConfig,
    OptimizationStorage
)

# Import decision engine
from app.service.decision import DecisionEngine


def main():
    print("=" * 80)
    print("NEW STRATEGIES AND OPTIMIZATION EXAMPLE")
    print("=" * 80)
    
    # 1. Load data
    print("\n1. Loading market data...")
    store = DataStore()
    df = store.read_dataframe("BTC-USDT", "1h")
    print(f"   Loaded {len(df)} bars for BTC-USDT 1h")
    print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # 2. Test new strategies
    print("\n2. Testing new atomic strategies...")
    
    # ATR Channel Breakout with Volume Filter
    print("\n   a) ATR Channel Breakout with Volume Filter:")
    atr_breakout_signal = atr_channel_breakout_volume(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        volume=df['volume'],
        atr_period=14,
        atr_multiplier=2.0,
        volume_ma_period=20,
        volume_threshold=1.5
    )
    long_signals = (atr_breakout_signal.signal == 1).sum()
    short_signals = (atr_breakout_signal.signal == -1).sum()
    print(f"      Long signals: {long_signals}, Short signals: {short_signals}")
    print(f"      Avg strength: {abs(atr_breakout_signal.strength).mean():.3f}")
    
    # VWAP Z-Score Mean Reversion
    print("\n   b) VWAP Z-Score Mean Reversion:")
    vwap_signal = vwap_zscore_reversion(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        volume=df['volume'],
        vwap_period=20,
        zscore_entry=2.0,
        zscore_exit=0.5
    )
    long_signals = (vwap_signal.signal == 1).sum()
    short_signals = (vwap_signal.signal == -1).sum()
    print(f"      Long signals: {long_signals}, Short signals: {short_signals}")
    print(f"      Avg strength: {abs(vwap_signal.strength).mean():.3f}")
    
    # Triple EMA + RSI Momentum
    print("\n   c) Triple EMA + RSI Regime Momentum:")
    ema_signal = ema_triple_momentum(
        close=df['close'],
        fast_period=8,
        mid_period=21,
        slow_period=55,
        rsi_period=14,
        rsi_bull_threshold=50,
        rsi_bear_threshold=50
    )
    long_signals = (ema_signal.signal == 1).sum()
    short_signals = (ema_signal.signal == -1).sum()
    print(f"      Long signals: {long_signals}, Short signals: {short_signals}")
    print(f"      Avg strength: {abs(ema_signal.strength).mean():.3f}")
    
    # 3. Grid Search Optimization Example
    print("\n3. Grid Search Optimization (small example)...")
    
    grid_config = GridSearchConfig(
        strategy_name="ema_triple_momentum",
        symbol="BTC-USDT",
        timeframe="1h",
        param_grid={
            'fast_period': [5, 8, 10],
            'mid_period': [15, 21, 30],
            'slow_period': [40, 55, 70],
            'rsi_bull_threshold': [45, 50, 55]
        },
        scoring_metric="sharpe_ratio",
        maximize=True,
        save_all_results=True
    )
    
    print(f"   Running grid search with {3*3*3*3} = 81 combinations...")
    print("   (This may take a few minutes...)")
    
    try:
        storage = OptimizationStorage()
        grid_results = grid_search_optimize(
            df=df,
            config=grid_config,
            storage=storage,
            verbose=True
        )
        
        if grid_results:
            best = grid_results[0]
            print(f"\n   Best parameters found:")
            for param, value in best.parameters.items():
                print(f"      {param}: {value}")
            print(f"   Best Sharpe Ratio: {best.score:.4f}")
            print(f"   Win Rate: {best.metrics['win_rate']:.2%}")
            print(f"   Total Trades: {best.metrics['total_trades']}")
    
    except Exception as e:
        print(f"   Grid search skipped: {e}")
    
    # 4. Bayesian Optimization Example
    print("\n4. Bayesian Optimization (requires scikit-optimize)...")
    
    bayesian_config = BayesianConfig(
        strategy_name="atr_channel_breakout_volume",
        symbol="BTC-USDT",
        timeframe="1h",
        param_space={
            'atr_period': {'type': 'integer', 'low': 10, 'high': 20},
            'atr_multiplier': {'type': 'real', 'low': 1.5, 'high': 3.0},
            'volume_ma_period': {'type': 'integer', 'low': 15, 'high': 30},
            'volume_threshold': {'type': 'real', 'low': 1.2, 'high': 2.0}
        },
        scoring_metric="sharpe_ratio",
        maximize=True,
        n_calls=30,
        n_initial_points=10
    )
    
    print(f"   Running Bayesian optimization with {bayesian_config.n_calls} iterations...")
    
    try:
        bayesian_results = bayesian_optimize(
            df=df,
            config=bayesian_config,
            storage=storage,
            verbose=True
        )
        
        if bayesian_results:
            best = bayesian_results[0]
            print(f"\n   Best parameters found:")
            for param, value in best.parameters.items():
                print(f"      {param}: {value}")
            print(f"   Best Sharpe Ratio: {best.score:.4f}")
    
    except ImportError:
        print("   Bayesian optimization requires scikit-optimize: pip install scikit-optimize")
    except Exception as e:
        print(f"   Bayesian optimization skipped: {e}")
    
    # 5. Volatility-based Ranges Example
    print("\n5. Volatility-based Entry/SL/TP Ranges...")
    
    engine = DecisionEngine()
    
    # Get last signal
    current_signal = int(ema_signal.signal.iloc[-1])
    current_strength = float(ema_signal.strength.iloc[-1])
    
    print(f"   Current signal: {current_signal} (strength: {current_strength:.3f})")
    
    if current_signal != 0:
        # Calculate hypothetical plan with ranges
        plan = engine.calculate_hypothetical_plan(
            df=df,
            signal=current_signal,
            signal_strength=abs(current_strength),
            capital=100000.0,
            risk_pct=0.02
        )
        
        if plan.get('has_plan'):
            print(f"\n   Entry Plan:")
            print(f"      Entry Price: ${plan['entry_price']:,.2f}")
            if plan.get('entry_low') and plan.get('entry_high'):
                print(f"      Entry Range: ${plan['entry_low']:,.2f} - ${plan['entry_high']:,.2f}")
                print(f"      Range Width: {plan['entry_range_pct']:.2%}")
            
            print(f"\n   Risk Management:")
            print(f"      Stop Loss: ${plan['stop_loss']:,.2f}")
            if plan.get('sl_low') and plan.get('sl_high'):
                print(f"      SL Range: ${plan['sl_low']:,.2f} - ${plan['sl_high']:,.2f}")
                print(f"      SL Range Width: {plan['sl_range_pct']:.2%}")
            
            print(f"      Take Profit: ${plan['take_profit']:,.2f}")
            if plan.get('tp_low') and plan.get('tp_high'):
                print(f"      TP Range: ${plan['tp_low']:,.2f} - ${plan['tp_high']:,.2f}")
                print(f"      TP Range Width: {plan['tp_range_pct']:.2%}")
            
            print(f"\n   Position Sizing:")
            print(f"      Quantity: {plan['position_size']['quantity']:.8f} BTC")
            print(f"      Notional: ${plan['position_size']['notional']:,.2f}")
            print(f"      Risk Amount: ${plan['position_size']['risk_amount']:,.2f}")
            print(f"      Risk/Reward: {plan['risk_reward_ratio']:.2f}")
    else:
        print("   No directional signal at the moment")
    
    # 6. Strategy List
    print("\n6. Available Strategies:")
    strategies = get_strategy_list()
    for i, strategy in enumerate(strategies, 1):
        print(f"   {i}. {strategy}")
    
    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETED")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run grid search or Bayesian optimization to find best parameters")
    print("2. Use optimized parameters in production trading")
    print("3. Monitor performance and re-optimize periodically")
    print("4. Combine multiple strategies with different parameters for diversification")


if __name__ == "__main__":
    main()

