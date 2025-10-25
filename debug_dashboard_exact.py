#!/usr/bin/env python3
"""Debug dashboard with exact parameters."""

from datetime import datetime
from zoneinfo import ZoneInfo
from app.data.store import DataStore
from app.service import DecisionEngine, MarketAdvisor
from app.research.signals import ma_crossover, rsi_regime_pullback, trend_following_ema
from app.research.combine import combine_signals
import pandas as pd

def debug_dashboard_exact():
    """Debug dashboard with exact parameters."""
    print("🔍 DEBUGGING DASHBOARD - EXACT PARAMETERS")
    print("=" * 60)
    
    # Current time
    now_utc = datetime.now(ZoneInfo("UTC"))
    now_arg = now_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    
    print(f"🕐 Current UTC time: {now_utc}")
    print(f"🕐 Current Argentina time: {now_arg}")
    
    try:
        # Load data exactly like dashboard
        store = DataStore()
        symbol = "BTC-USDT"
        timeframe = "1h"
        
        bars = store.read_bars(symbol, timeframe)
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        df = df.tail(500).reset_index(drop=True)
        
        print(f"\n📊 Data loaded: {len(df)} bars")
        
        # Generate signals exactly like dashboard
        sig1 = ma_crossover(df['close'], fast_period=10, slow_period=20)
        sig2 = rsi_regime_pullback(df['close'])
        sig3 = trend_following_ema(df['close'])
        
        returns = df['close'].pct_change()
        combined = combine_signals(
            {
                'ma_cross': sig1.signal,
                'rsi_regime': sig2.signal,
                'triple_ema': sig3.signal
            },
            method='simple_average',
            returns=returns
        )
        
        print(f"   Combined signal: {combined.signal.iloc[-1]}")
        print(f"   Combined confidence: {combined.confidence.iloc[-1]}")
        
        # Test DecisionEngine with exact dashboard parameters
        print(f"\n🤖 DecisionEngine (Dashboard Params):")
        
        decision_engine = DecisionEngine()
        decision = decision_engine.make_decision(
            df=df,
            signals=combined.signal,
            signal_strength=combined.confidence,
            signal_source="combined",
            capital=100000.0,
            risk_pct=0.02,
            current_time=datetime.now(ZoneInfo("UTC"))
        )
        
        print(f"   Signal: {decision.signal}")
        print(f"   Skip reason: {decision.skip_reason}")
        print(f"   Should execute: {decision.should_execute}")
        print(f"   Window: {decision.window}")
        print(f"   Decision date: {decision.decision_date}")
        
        # Test with different current times
        print(f"\n🧪 Testing Different Current Times:")
        
        test_times = [
            datetime.now(ZoneInfo("UTC")),
            datetime.now(ZoneInfo("UTC")).replace(hour=15, minute=0, second=0),  # 15:00 UTC = 12:00 Argentina
            datetime.now(ZoneInfo("UTC")).replace(hour=17, minute=0, second=0),  # 17:00 UTC = 14:00 Argentina
        ]
        
        for i, test_time in enumerate(test_times):
            test_arg = test_time.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
            
            decision_test = decision_engine.make_decision(
                df=df,
                signals=combined.signal,
                signal_strength=combined.confidence,
                signal_source="combined",
                capital=100000.0,
                risk_pct=0.02,
                current_time=test_time
            )
            
            print(f"   Test {i+1}: {test_time} ({test_arg.strftime('%H:%M')} ARG)")
            print(f"     Signal: {decision_test.signal}")
            print(f"     Skip reason: {decision_test.skip_reason}")
            print(f"     Should execute: {decision_test.should_execute}")
            print(f"     Window: {decision_test.window}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_dashboard_exact()








