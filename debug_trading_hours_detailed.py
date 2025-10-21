#!/usr/bin/env python3
"""Detailed debug of trading hours issue."""

from datetime import datetime
from zoneinfo import ZoneInfo
from app.core.calendar import TradingCalendar
from app.service import DecisionEngine

def debug_trading_hours_detailed():
    """Detailed debug of trading hours calculation."""
    print("🔍 DEBUGGING TRADING HOURS - DETAILED")
    print("=" * 60)
    
    # Current time
    now_utc = datetime.now(ZoneInfo("UTC"))
    now_arg = now_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    
    print(f"🕐 Current UTC time: {now_utc}")
    print(f"🕐 Current Argentina time: {now_arg}")
    print(f"🕐 Current Argentina time (formatted): {now_arg.strftime('%H:%M:%S %Z')}")
    print(f"🕐 Current Argentina time (time only): {now_arg.time()}")
    
    # Trading calendar
    calendar = TradingCalendar()
    
    print(f"\n📅 Trading Windows Configuration:")
    print(f"   Window A: {calendar.window_a.start_time} - {calendar.window_a.end_time} (Argentina)")
    print(f"   Window B: {calendar.window_b.start_time} - {calendar.window_b.end_time} (Argentina)")
    print(f"   Forced Close: {calendar.forced_close_time} (Argentina)")
    
    # Check trading hours
    is_trading = calendar.is_trading_hours(now_utc)
    current_window = calendar.get_current_window(now_utc)
    should_force_close = calendar.should_force_close(now_utc)
    is_valid_entry = calendar.is_valid_entry_time(now_utc)
    
    print(f"\n✅ Trading Status:")
    print(f"   Is Trading Hours: {is_trading}")
    print(f"   Current Window: {current_window}")
    print(f"   Should Force Close: {should_force_close}")
    print(f"   Is Valid Entry: {is_valid_entry}")
    
    # Check window A specifically
    window_a_check = calendar.window_a.is_within_window(now_utc)
    print(f"\n🪟 Window A Detailed Check:")
    print(f"   Is within Window A: {window_a_check}")
    print(f"   Current time: {now_arg.time()}")
    print(f"   Window A start: {calendar.window_a.start_time}")
    print(f"   Window A end: {calendar.window_a.end_time}")
    
    # Manual check
    current_time = now_arg.time()
    window_a_start = calendar.window_a.start_time
    window_a_end = calendar.window_a.end_time
    
    manual_check = window_a_start <= current_time <= window_a_end
    print(f"\n🔧 Manual Check:")
    print(f"   {window_a_start} <= {current_time} <= {window_a_end}")
    print(f"   Result: {manual_check}")
    
    # Test DecisionEngine directly
    print(f"\n🤖 DecisionEngine Test:")
    try:
        decision_engine = DecisionEngine()
        
        # Create mock data
        import pandas as pd
        import numpy as np
        
        # Mock OHLCV data
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='1H')
        mock_data = pd.DataFrame({
            'timestamp': dates,
            'open': 100 + np.random.randn(len(dates)) * 0.01,
            'high': 100 + np.random.randn(len(dates)) * 0.01,
            'low': 100 + np.random.randn(len(dates)) * 0.01,
            'close': 100 + np.random.randn(len(dates)) * 0.01,
            'volume': np.random.randint(1000, 10000, len(dates))
        })
        
        # Mock signals
        mock_signals = pd.Series([-1] * len(dates), index=dates)
        mock_confidence = pd.Series([0.5] * len(dates), index=dates)
        
        # Make decision
        decision = decision_engine.make_decision(
            df=mock_data,
            signals=mock_signals,
            signal_strength=mock_confidence,
            signal_source="test",
            capital=100000.0,
            risk_pct=0.02
        )
        
        print(f"   Decision signal: {decision.signal}")
        print(f"   Decision skip_reason: {decision.skip_reason}")
        print(f"   Decision should_execute: {decision.should_execute}")
        print(f"   Decision window: {decision.window}")
        
    except Exception as e:
        print(f"   Error in DecisionEngine: {e}")
    
    # Check timezone conversion
    print(f"\n🌍 Timezone Conversion Test:")
    print(f"   UTC to Argentina: {now_utc.astimezone(ZoneInfo('America/Argentina/Buenos_Aires'))}")
    print(f"   Argentina to UTC: {now_arg.astimezone(ZoneInfo('UTC'))}")
    
    # Check if it's weekend
    from app.core.calendar import is_weekend
    is_weekend_check = is_weekend(now_utc)
    print(f"\n📅 Weekend Check:")
    print(f"   Is weekend: {is_weekend_check}")
    print(f"   Weekday: {now_utc.strftime('%A')}")

if __name__ == "__main__":
    debug_trading_hours_detailed()



