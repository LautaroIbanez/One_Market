#!/usr/bin/env python3
"""Debug timestamp issue in DecisionEngine."""

from datetime import datetime
from zoneinfo import ZoneInfo
from app.data.store import DataStore
from app.service import DecisionEngine
import pandas as pd

def debug_timestamp_issue():
    """Debug timestamp issue in DecisionEngine."""
    print("🔍 DEBUGGING TIMESTAMP ISSUE")
    print("=" * 50)
    
    # Current time
    now_utc = datetime.now(ZoneInfo("UTC"))
    now_arg = now_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    
    print(f"🕐 Current UTC time: {now_utc}")
    print(f"🕐 Current Argentina time: {now_arg}")
    
    try:
        # Load data
        store = DataStore()
        symbol = "BTC-USDT"
        timeframe = "1h"
        
        bars = store.read_bars(symbol, timeframe)
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        df = df.tail(500).reset_index(drop=True)
        
        # Get latest timestamp from data
        latest_idx = len(df) - 1
        current_timestamp = int(df['timestamp'].iloc[latest_idx])
        data_time_utc = datetime.fromtimestamp(current_timestamp / 1000, tz=ZoneInfo("UTC"))
        data_time_arg = data_time_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
        
        print(f"\n📊 Data Timestamp:")
        print(f"   Latest data timestamp: {current_timestamp}")
        print(f"   Data UTC time: {data_time_utc}")
        print(f"   Data Argentina time: {data_time_arg}")
        
        # Test DecisionEngine with data timestamp
        print(f"\n🤖 DecisionEngine with Data Timestamp:")
        
        decision_engine = DecisionEngine()
        
        # Mock signals
        import numpy as np
        mock_signals = pd.Series([1] * len(df), index=df.index)
        mock_confidence = pd.Series([0.5] * len(df), index=df.index)
        
        decision = decision_engine.make_decision(
            df=df,
            signals=mock_signals,
            signal_strength=mock_confidence,
            signal_source="test",
            capital=100000.0,
            risk_pct=0.02
        )
        
        print(f"   Signal: {decision.signal}")
        print(f"   Skip reason: {decision.skip_reason}")
        print(f"   Should execute: {decision.should_execute}")
        print(f"   Window: {decision.window}")
        print(f"   Decision date: {decision.decision_date}")
        
        # Test with current time
        print(f"\n🤖 DecisionEngine with Current Time:")
        
        decision2 = decision_engine.make_decision(
            df=df,
            signals=mock_signals,
            signal_strength=mock_confidence,
            signal_source="test",
            capital=100000.0,
            risk_pct=0.02,
            current_time=now_utc
        )
        
        print(f"   Signal: {decision2.signal}")
        print(f"   Skip reason: {decision2.skip_reason}")
        print(f"   Should execute: {decision2.should_execute}")
        print(f"   Window: {decision2.window}")
        print(f"   Decision date: {decision2.decision_date}")
        
        # Test with data timestamp as current time
        print(f"\n🤖 DecisionEngine with Data Timestamp as Current Time:")
        
        decision3 = decision_engine.make_decision(
            df=df,
            signals=mock_signals,
            signal_strength=mock_confidence,
            signal_source="test",
            capital=100000.0,
            risk_pct=0.02,
            current_time=data_time_utc
        )
        
        print(f"   Signal: {decision3.signal}")
        print(f"   Skip reason: {decision3.skip_reason}")
        print(f"   Should execute: {decision3.should_execute}")
        print(f"   Window: {decision3.window}")
        print(f"   Decision date: {decision3.decision_date}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_timestamp_issue()


