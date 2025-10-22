#!/usr/bin/env python3
"""Debug timestamps in real data."""

from datetime import datetime
from zoneinfo import ZoneInfo
from app.data.store import DataStore
import pandas as pd

def debug_timestamps():
    """Debug timestamps in real data."""
    print("🔍 DEBUGGING TIMESTAMPS")
    print("=" * 50)
    
    # Current time
    now_utc = datetime.now(ZoneInfo("UTC"))
    now_arg = now_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    
    print(f"🕐 Current UTC time: {now_utc}")
    print(f"🕐 Current Argentina time: {now_arg}")
    print(f"🕐 Current UTC timestamp: {int(now_utc.timestamp() * 1000)}")
    
    # Load real data
    try:
        store = DataStore()
        symbol = "BTC-USDT"
        timeframe = "1h"
        
        bars = store.read_bars(symbol, timeframe)
        
        if not bars:
            print("❌ No data available")
            return
        
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        df = df.tail(10).reset_index(drop=True)  # Last 10 bars
        
        print(f"\n📊 Real Data Timestamps:")
        for i, row in df.iterrows():
            timestamp_ms = row['timestamp']
            timestamp_utc = datetime.fromtimestamp(timestamp_ms / 1000, tz=ZoneInfo("UTC"))
            timestamp_arg = timestamp_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
            
            print(f"   Bar {i}: {timestamp_ms} -> {timestamp_utc} -> {timestamp_arg}")
        
        # Check if timestamps are recent
        latest_timestamp = df['timestamp'].iloc[-1]
        latest_utc = datetime.fromtimestamp(latest_timestamp / 1000, tz=ZoneInfo("UTC"))
        latest_arg = latest_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
        
        print(f"\n🕐 Latest Data:")
        print(f"   Latest timestamp: {latest_timestamp}")
        print(f"   Latest UTC: {latest_utc}")
        print(f"   Latest Argentina: {latest_arg}")
        print(f"   Time difference: {now_utc - latest_utc}")
        
        # Check if data is too old
        time_diff = now_utc - latest_utc
        if time_diff.total_seconds() > 3600:  # More than 1 hour old
            print(f"   ⚠️  Data is {time_diff} old - might be causing issues")
        else:
            print(f"   ✅ Data is recent")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_timestamps()




