#!/usr/bin/env python3
"""Debug timezone and trading hours."""

from datetime import datetime
from zoneinfo import ZoneInfo
from app.core.calendar import TradingCalendar

def debug_trading_hours():
    """Debug trading hours calculation."""
    print("🔍 DEBUGGING TRADING HOURS")
    print("=" * 50)
    
    # Current time
    now_utc = datetime.now(ZoneInfo("UTC"))
    now_arg = now_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    
    print(f"🕐 Current UTC time: {now_utc}")
    print(f"🕐 Current Argentina time: {now_arg}")
    print(f"🕐 Current Argentina time (formatted): {now_arg.strftime('%H:%M:%S %Z')}")
    
    # Trading calendar
    calendar = TradingCalendar()
    
    print(f"\n📅 Trading Windows:")
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
    print(f"\n🪟 Window A Check:")
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
    
    # Time until next window
    if not is_trading:
        next_window, next_start = calendar.get_next_trading_window(now_utc)
        next_start_arg = next_start.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
        print(f"\n⏰ Next Trading Window:")
        print(f"   Window: {next_window}")
        print(f"   Start (UTC): {next_start}")
        print(f"   Start (Argentina): {next_start_arg}")
        print(f"   Start (Argentina formatted): {next_start_arg.strftime('%H:%M:%S %Z')}")

if __name__ == "__main__":
    debug_trading_hours()

