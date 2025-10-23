#!/usr/bin/env python3
"""Debug dashboard data specifically."""

from datetime import datetime
from zoneinfo import ZoneInfo
from app.data.store import DataStore
from app.service import DecisionEngine, MarketAdvisor
from app.research.signals import ma_crossover, rsi_regime_pullback, trend_following_ema
from app.research.combine import combine_signals
from app.config.settings import settings
import pandas as pd

def debug_dashboard_data():
    """Debug dashboard data specifically."""
    print("🔍 DEBUGGING DASHBOARD DATA")
    print("=" * 50)
    
    # Current time
    now_utc = datetime.now(ZoneInfo("UTC"))
    now_arg = now_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    
    print(f"🕐 Current UTC time: {now_utc}")
    print(f"🕐 Current Argentina time: {now_arg}")
    print(f"🕐 Is weekend: {now_utc.weekday() >= 5}")
    
    # Load real data
    try:
        store = DataStore()
        symbol = "BTC-USDT"
        timeframe = "1h"
        
        print(f"\n📊 Loading Real Data:")
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
        
        # Generate signals
        print(f"\n🔍 Generating Signals:")
        
        sig1 = ma_crossover(df['close'], fast_period=10, slow_period=20)
        sig2 = rsi_regime_pullback(df['close'])
        sig3 = trend_following_ema(df['close'])
        
        print(f"   MA Crossover signal: {sig1.signal.iloc[-1]}")
        print(f"   RSI Regime signal: {sig2.signal.iloc[-1]}")
        print(f"   Triple EMA signal: {sig3.signal.iloc[-1]}")
        
        # Combine signals
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
        
        # Test DecisionEngine with real data
        print(f"\n🤖 DecisionEngine with Real Data:")
        
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
    debug_dashboard_data()






