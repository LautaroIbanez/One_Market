#!/usr/bin/env python3
"""Debug DecisionEngine with exact dashboard parameters."""

from datetime import datetime
from zoneinfo import ZoneInfo
from app.data.store import DataStore
from app.service import DecisionEngine, MarketAdvisor
from app.research.signals import ma_crossover, rsi_regime_pullback, trend_following_ema
from app.research.combine import combine_signals
import pandas as pd

def debug_decision_exact():
    """Debug DecisionEngine with exact dashboard parameters."""
    print("🔍 DEBUGGING DECISION ENGINE - EXACT DASHBOARD PARAMS")
    print("=" * 70)
    
    # Current time
    now_utc = datetime.now(ZoneInfo("UTC"))
    now_arg = now_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    
    print(f"🕐 Current UTC time: {now_utc}")
    print(f"🕐 Current Argentina time: {now_arg}")
    print(f"🕐 Is weekend: {now_utc.weekday() >= 5}")
    
    try:
        # Load data exactly like dashboard
        store = DataStore()
        symbol = "BTC-USDT"  # Dashboard uses this format
        timeframe = "1h"
        
        print(f"\n📊 Loading Data (Dashboard Format):")
        print(f"   Symbol: {symbol}")
        print(f"   Timeframe: {timeframe}")
        
        bars = store.read_bars(symbol, timeframe)
        
        if not bars:
            print("   ❌ No data available")
            return
        
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        df = df.tail(500).reset_index(drop=True)
        
        print(f"   ✅ Data loaded: {len(df)} bars")
        print(f"   Last timestamp: {df['timestamp'].iloc[-1]}")
        print(f"   Last close: {df['close'].iloc[-1]}")
        
        # Generate signals exactly like dashboard
        print(f"\n🔍 Generating Signals (Dashboard Method):")
        
        sig1 = ma_crossover(df['close'], fast_period=10, slow_period=20)
        sig2 = rsi_regime_pullback(df['close'])
        sig3 = trend_following_ema(df['close'])
        
        print(f"   MA Crossover signal: {sig1.signal.iloc[-1]}")
        print(f"   RSI Regime signal: {sig2.signal.iloc[-1]}")
        print(f"   Triple EMA signal: {sig3.signal.iloc[-1]}")
        
        # Combine signals exactly like dashboard
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
        print(f"\n🤖 DecisionEngine (Exact Dashboard Params):")
        
        decision_engine = DecisionEngine()
        decision = decision_engine.make_decision(
            df=df,
            signals=combined.signal,
            signal_strength=combined.confidence,
            signal_source="combined",
            capital=100000.0,
            risk_pct=0.02
        )
        
        print(f"   Signal: {decision.signal}")
        print(f"   Skip reason: {decision.skip_reason}")
        print(f"   Should execute: {decision.should_execute}")
        print(f"   Window: {decision.window}")
        print(f"   Trading day: {decision.trading_day}")
        print(f"   Decision date: {decision.decision_date}")
        
        # Test with explicit current_time
        print(f"\n🤖 DecisionEngine (With Explicit Current Time):")
        
        decision2 = decision_engine.make_decision(
            df=df,
            signals=combined.signal,
            signal_strength=combined.confidence,
            signal_source="combined",
            capital=100000.0,
            risk_pct=0.02,
            current_time=now_utc
        )
        
        print(f"   Signal: {decision2.signal}")
        print(f"   Skip reason: {decision2.skip_reason}")
        print(f"   Should execute: {decision2.should_execute}")
        print(f"   Window: {decision2.window}")
        print(f"   Trading day: {decision2.trading_day}")
        print(f"   Decision date: {decision2.decision_date}")
        
        # Test MarketAdvisor
        print(f"\n🧠 MarketAdvisor Test:")
        
        advisor = MarketAdvisor(default_risk_pct=0.02)
        advice = advisor.get_advice(
            df_intraday=df,
            current_signal=combined.signal.iloc[-1],
            signal_strength=abs(combined.signal.iloc[-1]),
            symbol=symbol
        )
        
        print(f"   Short term timing: {advice.short_term.entry_timing}")
        print(f"   Short term volatility: {advice.short_term.volatility_state}")
        print(f"   Short term risk rec: {advice.short_term.recommended_risk_pct}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_decision_exact()

