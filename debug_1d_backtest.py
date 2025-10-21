#!/usr/bin/env python3
"""Debug script to test 1d backtest issues."""

from app.service.strategy_orchestrator import StrategyOrchestrator
from app.data.store import DataStore
import pandas as pd

def test_1d_data():
    """Test 1d data loading and signal generation."""
    print("=== Testing 1d Data Loading ===")
    
    store = DataStore()
    bars = store.read_bars('BTC/USDT', '1d', max_bars=730)
    print(f"Loaded {len(bars)} bars for 1d")
    
    if not bars:
        print("❌ No bars loaded!")
        return
    
    df = pd.DataFrame([bar.to_dict() for bar in bars])
    df = df.sort_values('timestamp').reset_index(drop=True)
    print(f"DataFrame shape: {df.shape}")
    
    # Test date range
    start_date = pd.to_datetime(df.timestamp.iloc[0], unit='ms')
    end_date = pd.to_datetime(df.timestamp.iloc[-1], unit='ms')
    print(f"Date range: {start_date} to {end_date}")
    print(f"Close prices: {df.close.iloc[0]:.2f} to {df.close.iloc[-1]:.2f}")
    
    # Test signal generation
    from app.research.signals import ma_crossover
    signals = ma_crossover(df['close'], fast_period=10, slow_period=20)
    print(f"Signals generated: {len(signals.signal)}")
    print(f"Signal values: {signals.signal.value_counts()}")
    print(f"Non-zero signals: {(signals.signal != 0).sum()}")
    
    # Test backtest
    print("\n=== Testing Backtest ===")
    orchestrator = StrategyOrchestrator()
    results = orchestrator.run_all_backtests('BTC/USDT', '1d')
    print(f"Backtest results: {len(results)} strategies")
    
    for result in results:
        print(f"- {result.strategy_name}: {result.total_trades} trades, Sharpe={result.sharpe_ratio:.2f}")

if __name__ == "__main__":
    test_1d_data()
