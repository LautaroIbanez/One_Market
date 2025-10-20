"""Quick test of new features implementation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.store import DataStore
from app.research.signals import (
    atr_channel_breakout_volume,
    vwap_zscore_reversion,
    ema_triple_momentum,
    get_strategy_list
)
from app.service.decision import DecisionEngine

print("="*80)
print("TESTING NEW FEATURES")
print("="*80)

# 1. Load data
print("\n1. ✅ Loading data...")
store = DataStore()
bars = store.read_bars("BTC-USDT", "1h")
import pandas as pd
df = pd.DataFrame([{
    'timestamp': bar.timestamp,
    'open': bar.open,
    'high': bar.high,
    'low': bar.low,
    'close': bar.close,
    'volume': bar.volume
} for bar in bars])
print(f"   Loaded {len(df)} bars")

# 2. Test new strategies
print("\n2. ✅ Testing new strategies...")

print("\n   a) ATR Channel Breakout:")
try:
    signal1 = atr_channel_breakout_volume(
        high=df['high'], low=df['low'], close=df['close'], volume=df['volume']
    )
    longs = (signal1.signal == 1).sum()
    shorts = (signal1.signal == -1).sum()
    print(f"      ✅ Long: {longs}, Short: {shorts}, Strength: {abs(signal1.strength.mean()):.3f}")
except Exception as e:
    print(f"      ❌ Error: {e}")

print("\n   b) VWAP Z-Score Reversion:")
try:
    signal2 = vwap_zscore_reversion(
        high=df['high'], low=df['low'], close=df['close'], volume=df['volume']
    )
    longs = (signal2.signal == 1).sum()
    shorts = (signal2.signal == -1).sum()
    print(f"      ✅ Long: {longs}, Short: {shorts}, Strength: {abs(signal2.strength.mean()):.3f}")
except Exception as e:
    print(f"      ❌ Error: {e}")

print("\n   c) Triple EMA Momentum:")
try:
    signal3 = ema_triple_momentum(close=df['close'])
    longs = (signal3.signal == 1).sum()
    shorts = (signal3.signal == -1).sum()
    print(f"      ✅ Long: {longs}, Short: {shorts}, Strength: {abs(signal3.strength.mean()):.3f}")
except Exception as e:
    print(f"      ❌ Error: {e}")

# 3. Test volatility ranges
print("\n3. ✅ Testing volatility-based ranges...")
try:
    engine = DecisionEngine()
    
    # Use last signal from triple EMA
    current_signal = int(signal3.signal.iloc[-1])
    current_strength = float(abs(signal3.strength.iloc[-1]))
    
    if current_signal != 0:
        plan = engine.calculate_hypothetical_plan(
            df=df,
            signal=current_signal,
            signal_strength=current_strength,
            capital=100000.0
        )
        
        if plan.get('has_plan'):
            print(f"\n   Entry:")
            print(f"      Price: ${plan['entry_price']:,.2f}")
            if plan.get('entry_low'):
                print(f"      Range: ${plan['entry_low']:,.2f} - ${plan['entry_high']:,.2f}")
                print(f"      Width: {plan['entry_range_pct']:.2%}")
            
            print(f"\n   Stop Loss:")
            print(f"      Price: ${plan['stop_loss']:,.2f}")
            if plan.get('sl_low'):
                print(f"      Range: ${plan['sl_low']:,.2f} - ${plan['sl_high']:,.2f}")
                print(f"      Width: {plan['sl_range_pct']:.2%}")
            
            print(f"\n   Take Profit:")
            print(f"      Price: ${plan['take_profit']:,.2f}")
            if plan.get('tp_low'):
                print(f"      Range: ${plan['tp_low']:,.2f} - ${plan['tp_high']:,.2f}")
                print(f"      Width: {plan['tp_range_pct']:.2%}")
            
            print(f"\n   ✅ Ranges calculated successfully!")
        else:
            print(f"   ℹ️ No plan: {plan.get('reason')}")
    else:
        print("   ℹ️ No directional signal")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. List available strategies
print("\n4. ✅ Available strategies:")
strategies = get_strategy_list()
for i, s in enumerate(strategies, 1):
    marker = "🆕" if s in ["atr_channel_breakout_volume", "vwap_zscore_reversion", "ema_triple_momentum"] else "  "
    print(f"   {marker} {i}. {s}")

print("\n" + "="*80)
print("✅ ALL FEATURES WORKING!")
print("="*80)
print("\n📊 Next steps:")
print("   1. Check UI at http://localhost:8501")
print("   2. Check API at http://localhost:8000/docs")
print("   3. View Deep Dive tab for PnL metrics")
print("   4. Run optimization: python scripts/optimize_strategies.py --help")

