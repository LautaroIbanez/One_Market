"""Example usage of research modules: indicators, features, signals, and combine.

This example demonstrates the complete workflow from data loading to signal generation
and combination.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import data modules
from app.data.store import DataStore

# Import research modules
from app.research.indicators import ema, rsi, atr, adx, donchian_channels, macd
from app.research.features import (
    relative_volatility,
    normalized_atr,
    trend_strength,
    distance_from_ma
)
from app.research.signals import (
    ma_crossover,
    rsi_regime_pullback,
    donchian_breakout_adx,
    macd_histogram_atr_filter,
    mean_reversion,
    trend_following_ema,
    get_strategy_list
)
from app.research.combine import (
    simple_average,
    weighted_average,
    sharpe_weighted,
    majority_vote,
    combine_signals
)


def load_sample_data():
    """Load sample OHLCV data."""
    print("\n" + "="*60)
    print("1. LOADING DATA")
    print("="*60)
    
    try:
        store = DataStore()
        
        # Try to load stored data
        symbols = store.list_stored_symbols()
        
        if not symbols:
            print("No stored data found. Please run example_fetch_data.py first.")
            print("Generating synthetic data for demo...")
            return generate_synthetic_data()
        
        # Use first available symbol
        symbol, timeframe = symbols[0]
        print(f"\nLoading: {symbol} {timeframe}")
        
        bars = store.read_bars(symbol, timeframe)
        
        if len(bars) < 100:
            print(f"Insufficient data ({len(bars)} bars). Generating synthetic data...")
            return generate_synthetic_data()
        
        # Convert to DataFrame
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Take last 500 bars for demo
        df = df.tail(500).reset_index(drop=True)
        
        print(f"Loaded {len(df)} bars")
        print(f"Date range: {pd.to_datetime(df['timestamp'].iloc[0], unit='ms')} to {pd.to_datetime(df['timestamp'].iloc[-1], unit='ms')}")
        print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
        
        return df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Generating synthetic data for demo...")
        return generate_synthetic_data()


def generate_synthetic_data():
    """Generate synthetic OHLCV data for demo."""
    np.random.seed(42)
    
    # Generate 500 bars
    n_bars = 500
    
    # Start timestamp (now - 500 hours)
    start_time = datetime.now() - timedelta(hours=n_bars)
    timestamps = [(start_time + timedelta(hours=i)).timestamp() * 1000 for i in range(n_bars)]
    
    # Generate price series with trend and noise
    base_price = 50000
    trend = np.linspace(0, 5000, n_bars)
    noise = np.random.randn(n_bars) * 500
    close = base_price + trend + noise.cumsum()
    
    # Generate OHLCV
    high = close * (1 + abs(np.random.randn(n_bars)) * 0.01)
    low = close * (1 - abs(np.random.randn(n_bars)) * 0.01)
    open_price = close + np.random.randn(n_bars) * 200
    volume = abs(np.random.randn(n_bars)) * 1000000 + 500000
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
        'symbol': 'BTC/USDT',
        'timeframe': '1h'
    })
    
    print("Generated 500 bars of synthetic data")
    print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    return df


def demo_indicators(df):
    """Demonstrate technical indicators."""
    print("\n" + "="*60)
    print("2. TECHNICAL INDICATORS")
    print("="*60)
    
    # Calculate indicators
    ema_20 = ema(df['close'], period=20)
    ema_50 = ema(df['close'], period=50)
    rsi_14 = rsi(df['close'], period=14)
    atr_14 = atr(df['high'], df['low'], df['close'], period=14)
    adx_14 = adx(df['high'], df['low'], df['close'], period=14)
    
    # MACD
    macd_line, signal_line, histogram = macd(df['close'])
    
    # Donchian
    upper, middle, lower = donchian_channels(df['high'], df['low'], period=20)
    
    print(f"\nCurrent values (last bar):")
    print(f"  Price: ${df['close'].iloc[-1]:.2f}")
    print(f"  EMA(20): ${ema_20.iloc[-1]:.2f}")
    print(f"  EMA(50): ${ema_50.iloc[-1]:.2f}")
    print(f"  RSI(14): {rsi_14.iloc[-1]:.2f}")
    print(f"  ATR(14): ${atr_14.iloc[-1]:.2f}")
    print(f"  ADX(14): {adx_14.iloc[-1]:.2f}")
    print(f"  MACD: {macd_line.iloc[-1]:.2f}")
    print(f"  MACD Signal: {signal_line.iloc[-1]:.2f}")
    print(f"  MACD Histogram: {histogram.iloc[-1]:.2f}")
    print(f"  Donchian Upper: ${upper.iloc[-1]:.2f}")
    print(f"  Donchian Lower: ${lower.iloc[-1]:.2f}")


def demo_features(df):
    """Demonstrate feature engineering."""
    print("\n" + "="*60)
    print("3. FEATURE ENGINEERING")
    print("="*60)
    
    # Calculate features
    rel_vol = relative_volatility(df['close'], short_period=10, long_period=50)
    natr = normalized_atr(df['high'], df['low'], df['close'], period=14)
    trend_str = trend_strength(df['close'], period=20)
    dist_ma = distance_from_ma(df['close'], period=20)
    
    print(f"\nCurrent features (last bar):")
    print(f"  Relative Volatility: {rel_vol.iloc[-1]:.2f}")
    print(f"  Normalized ATR: {natr.iloc[-1]:.2f}%")
    print(f"  Trend Strength (R²): {trend_str.iloc[-1]:.2f}")
    print(f"  Distance from MA(20): {dist_ma.iloc[-1]:.2f}%")
    
    # Interpretation
    print(f"\nInterpretation:")
    if rel_vol.iloc[-1] > 1.2:
        print(f"  📈 High volatility regime (rel_vol > 1.2)")
    elif rel_vol.iloc[-1] < 0.8:
        print(f"  📉 Low volatility regime (rel_vol < 0.8)")
    else:
        print(f"  ➡️  Normal volatility regime")
    
    if trend_str.iloc[-1] > 0.6:
        print(f"  📊 Strong trend (R² > 0.6)")
    elif trend_str.iloc[-1] < 0.3:
        print(f"  〰️  Ranging market (R² < 0.3)")
    else:
        print(f"  ➡️  Moderate trend")


def demo_signals(df):
    """Demonstrate signal generation."""
    print("\n" + "="*60)
    print("4. SIGNAL GENERATION")
    print("="*60)
    
    print(f"\nAvailable strategies: {', '.join(get_strategy_list())}")
    
    # Generate signals from different strategies
    signals = {}
    
    print(f"\nGenerating signals...")
    
    # 1. MA Crossover
    sig1 = ma_crossover(df['close'], fast_period=10, slow_period=20)
    signals['ma_cross'] = sig1.signal
    print(f"  ✓ MA Crossover - Current: {sig1.signal.iloc[-1]}")
    
    # 2. RSI Regime
    sig2 = rsi_regime_pullback(df['close'], rsi_period=14, regime_period=50)
    signals['rsi_regime'] = sig2.signal
    print(f"  ✓ RSI Regime - Current: {sig2.signal.iloc[-1]}")
    
    # 3. Donchian Breakout
    sig3 = donchian_breakout_adx(df['high'], df['low'], df['close'])
    signals['donchian'] = sig3.signal
    print(f"  ✓ Donchian+ADX - Current: {sig3.signal.iloc[-1]}")
    
    # 4. MACD Histogram
    sig4 = macd_histogram_atr_filter(df['high'], df['low'], df['close'])
    signals['macd'] = sig4.signal
    print(f"  ✓ MACD+ATR - Current: {sig4.signal.iloc[-1]}")
    
    # 5. Mean Reversion
    sig5 = mean_reversion(df['close'], period=20, std_dev=2.0)
    signals['mean_rev'] = sig5.signal
    print(f"  ✓ Mean Reversion - Current: {sig5.signal.iloc[-1]}")
    
    # 6. Trend Following
    sig6 = trend_following_ema(df['close'])
    signals['trend_ema'] = sig6.signal
    print(f"  ✓ Triple EMA - Current: {sig6.signal.iloc[-1]}")
    
    # Count signals
    signal_df = pd.DataFrame(signals)
    long_count = (signal_df.iloc[-1] == 1).sum()
    short_count = (signal_df.iloc[-1] == -1).sum()
    flat_count = (signal_df.iloc[-1] == 0).sum()
    
    print(f"\nCurrent signal distribution:")
    print(f"  Long: {long_count}/6 strategies")
    print(f"  Short: {short_count}/6 strategies")
    print(f"  Flat: {flat_count}/6 strategies")
    
    return signals


def demo_combination(signals, df):
    """Demonstrate signal combination."""
    print("\n" + "="*60)
    print("5. SIGNAL COMBINATION")
    print("="*60)
    
    # Calculate returns for Sharpe weighting
    returns = df['close'].pct_change()
    
    # Method 1: Simple Average
    print("\nMethod 1: Simple Average")
    combined1 = simple_average(signals)
    print(f"  Combined Signal: {combined1.signal.iloc[-1]}")
    print(f"  Confidence: {combined1.confidence.iloc[-1]:.2f}")
    print(f"  Weights: {list(combined1.weights.values())[0]:.3f} (equal)")
    
    # Method 2: Weighted Average (custom weights)
    print("\nMethod 2: Weighted Average (favor trend strategies)")
    custom_weights = {
        'ma_cross': 0.2,
        'rsi_regime': 0.15,
        'donchian': 0.25,
        'macd': 0.15,
        'mean_rev': 0.1,
        'trend_ema': 0.15
    }
    combined2 = weighted_average(signals, custom_weights)
    print(f"  Combined Signal: {combined2.signal.iloc[-1]}")
    print(f"  Confidence: {combined2.confidence.iloc[-1]:.2f}")
    
    # Method 3: Sharpe Weighted
    print("\nMethod 3: Sharpe-Weighted (90d rolling)")
    try:
        combined3 = sharpe_weighted(signals, returns, lookback_period=90)
        print(f"  Combined Signal: {combined3.signal.iloc[-1]}")
        print(f"  Confidence: {combined3.confidence.iloc[-1]:.2f}")
        print(f"  Top strategy: {max(combined3.weights, key=combined3.weights.get)}")
        print(f"  Top weight: {max(combined3.weights.values()):.2f}")
    except Exception as e:
        print(f"  ⚠️  Insufficient data for Sharpe weighting: {e}")
    
    # Method 4: Majority Vote
    print("\nMethod 4: Majority Vote (50% agreement)")
    combined4 = majority_vote(signals, min_agreement=0.5)
    print(f"  Combined Signal: {combined4.signal.iloc[-1]}")
    print(f"  Confidence (agreement): {combined4.confidence.iloc[-1]:.2f}")
    
    # Method 5: Unified interface
    print("\nMethod 5: Using combine_signals() factory")
    combined5 = combine_signals(
        signals,
        method="simple_average",
        tie_resolution="flat"
    )
    print(f"  Combined Signal: {combined5.signal.iloc[-1]}")
    print(f"  Method: {combined5.metadata['method']}")
    
    # Summary
    print("\n" + "-"*60)
    print("CONSENSUS SIGNAL SUMMARY")
    print("-"*60)
    
    all_combined = [combined1, combined2, combined4]
    consensus = pd.Series([c.signal.iloc[-1] for c in all_combined])
    
    if consensus.mean() > 0.3:
        print("📈 CONSENSUS: LONG")
        print(f"   {(consensus == 1).sum()}/3 methods agree on LONG")
    elif consensus.mean() < -0.3:
        print("📉 CONSENSUS: SHORT")
        print(f"   {(consensus == -1).sum()}/3 methods agree on SHORT")
    else:
        print("➡️  CONSENSUS: NEUTRAL")
        print(f"   No clear consensus")


def main():
    """Run complete demo."""
    print("="*60)
    print("ONE MARKET - Research Modules Demo")
    print("Epic 3: Indicators, Features, Signals & Combination")
    print("="*60)
    
    try:
        # Load data
        df = load_sample_data()
        
        # Demo indicators
        demo_indicators(df)
        
        # Demo features
        demo_features(df)
        
        # Demo signals
        signals = demo_signals(df)
        
        # Demo combination
        demo_combination(signals, df)
        
        print("\n" + "="*60)
        print("Demo completed successfully! ✅")
        print("="*60)
        
        print("\n📚 Next Steps:")
        print("  1. Review EPIC3_PROGRESS.md for detailed documentation")
        print("  2. Check BACKTEST_DESIGN.md for backtest architecture")
        print("  3. Run this example with your own data")
        print("  4. Experiment with different strategy parameters")
        print("  5. Try different combination methods")
        
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

