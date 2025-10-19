#!/usr/bin/env python3
"""Update data to fix the trading hours issue."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from app.data.fetch import DataFetcher
from app.data.store import DataStore
from app.config.settings import settings

def update_data():
    """Update data to get fresh timestamps."""
    print("🔄 UPDATING DATA")
    print("=" * 50)
    
    # Current time
    now_utc = datetime.now(ZoneInfo("UTC"))
    now_arg = now_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    
    print(f"🕐 Current UTC time: {now_utc}")
    print(f"🕐 Current Argentina time: {now_arg}")
    
    try:
        # Initialize fetcher and store
        fetcher = DataFetcher()
        store = DataStore()
        
        # Get current time in milliseconds
        current_timestamp = int(now_utc.timestamp() * 1000)
        
        # Calculate since timestamp (last 7 days)
        since_timestamp = current_timestamp - (7 * 24 * 60 * 60 * 1000)  # 7 days ago
        
        print(f"\n📊 Fetching Data:")
        print(f"   Since: {datetime.fromtimestamp(since_timestamp/1000, tz=ZoneInfo('UTC'))}")
        print(f"   Until: {datetime.fromtimestamp(current_timestamp/1000, tz=ZoneInfo('UTC'))}")
        
        # Fetch data for BTC/USDT 1h
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        print(f"   Symbol: {symbol}")
        print(f"   Timeframe: {timeframe}")
        
        # Fetch incremental data
        bars = fetcher.fetch_incremental(
            symbol=symbol,
            timeframe=timeframe,
            since=since_timestamp,
            until=current_timestamp
        )
        
        print(f"   ✅ Fetched {len(bars)} bars")
        
        if bars:
            # Store data
            store.write_bars(bars)
            print(f"   ✅ Stored {len(bars)} bars")
            
            # Show latest data
            latest_bar = bars[-1]
            latest_utc = datetime.fromtimestamp(latest_bar.timestamp / 1000, tz=ZoneInfo("UTC"))
            latest_arg = latest_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
            
            print(f"\n📈 Latest Data:")
            print(f"   Timestamp: {latest_bar.timestamp}")
            print(f"   UTC: {latest_utc}")
            print(f"   Argentina: {latest_arg}")
            print(f"   Close: {latest_bar.close}")
            
            # Check if data is recent
            time_diff = now_utc - latest_utc
            if time_diff.total_seconds() < 3600:  # Less than 1 hour old
                print(f"   ✅ Data is recent ({time_diff})")
            else:
                print(f"   ⚠️  Data is still old ({time_diff})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_data()
