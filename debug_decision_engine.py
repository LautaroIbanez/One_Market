#!/usr/bin/env python3
"""Debug DecisionEngine specifically."""

from datetime import datetime
from zoneinfo import ZoneInfo
from app.service import DecisionEngine
import pandas as pd
import numpy as np

def debug_decision_engine():
    """Debug DecisionEngine specifically."""
    print("🔍 DEBUGGING DECISION ENGINE")
    print("=" * 50)
    
    # Current time
    now_utc = datetime.now(ZoneInfo("UTC"))
    now_arg = now_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    
    print(f"🕐 Current UTC time: {now_utc}")
    print(f"🕐 Current Argentina time: {now_arg}")
    print(f"🕐 Is weekend: {now_utc.weekday() >= 5}")
    
    # Create mock data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='1H')
    mock_data = pd.DataFrame({
        'timestamp': [int(d.timestamp() * 1000) for d in dates],  # Convert to milliseconds
        'open': 100 + np.random.randn(len(dates)) * 0.01,
        'high': 100 + np.random.randn(len(dates)) * 0.01,
        'low': 100 + np.random.randn(len(dates)) * 0.01,
        'close': 100 + np.random.randn(len(dates)) * 0.01,
        'volume': np.random.randint(1000, 10000, len(dates))
    })
    
    # Mock signals
    mock_signals = pd.Series([-1] * len(dates), index=dates)
    mock_confidence = pd.Series([0.5] * len(dates), index=dates)
    
    print(f"\n📊 Mock Data:")
    print(f"   Data shape: {mock_data.shape}")
    print(f"   Signals shape: {mock_signals.shape}")
    print(f"   Last signal: {mock_signals.iloc[-1]}")
    print(f"   Last confidence: {mock_confidence.iloc[-1]}")
    
    # Test DecisionEngine
    try:
        decision_engine = DecisionEngine()
        
        print(f"\n🤖 DecisionEngine Test:")
        print(f"   Calendar type: {type(decision_engine.calendar)}")
        
        # Check calendar methods
        calendar = decision_engine.calendar
        is_trading = calendar.is_trading_hours(now_utc)
        current_window = calendar.get_current_window(now_utc)
        is_valid_entry = calendar.is_valid_entry_time(now_utc)
        
        print(f"   Calendar is_trading_hours: {is_trading}")
        print(f"   Calendar get_current_window: {current_window}")
        print(f"   Calendar is_valid_entry_time: {is_valid_entry}")
        
        # Make decision
        decision = decision_engine.make_decision(
            df=mock_data,
            signals=mock_signals,
            signal_strength=mock_confidence,
            signal_source="test",
            capital=100000.0,
            risk_pct=0.02,
            current_time=now_utc
        )
        
        print(f"\n📋 Decision Result:")
        print(f"   Signal: {decision.signal}")
        print(f"   Skip reason: {decision.skip_reason}")
        print(f"   Should execute: {decision.should_execute}")
        print(f"   Window: {decision.window}")
        print(f"   Trading day: {decision.trading_day}")
        
    except Exception as e:
        print(f"   Error in DecisionEngine: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_decision_engine()




