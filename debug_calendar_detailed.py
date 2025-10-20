#!/usr/bin/env python3
"""Debug TradingCalendar in detail."""

from datetime import datetime
from zoneinfo import ZoneInfo
from app.core.calendar import TradingCalendar

def debug_calendar_detailed():
    """Debug TradingCalendar in detail."""
    print("🔍 DEBUGGING TRADING CALENDAR - DETAILED")
    print("=" * 60)
    
    # Current time
    now_utc = datetime.now(ZoneInfo("UTC"))
    now_arg = now_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    
    print(f"🕐 Current UTC time: {now_utc}")
    print(f"🕐 Current Argentina time: {now_arg}")
    print(f"🕐 Is weekend: {now_utc.weekday() >= 5}")
    
    # Trading calendar
    calendar = TradingCalendar()
    
    print(f"\n📅 Trading Windows Configuration:")
    print(f"   Window A: {calendar.window_a.start_time} - {calendar.window_a.end_time} (Argentina)")
    print(f"   Window B: {calendar.window_b.start_time} - {calendar.window_b.end_time} (Argentina)")
    print(f"   Forced Close: {calendar.forced_close_time} (Argentina)")
    
    # Test with different times
    test_times = [
        now_utc,
        now_utc.replace(hour=10, minute=0, second=0),  # 10:00 UTC = 7:00 Argentina
        now_utc.replace(hour=12, minute=0, second=0),  # 12:00 UTC = 9:00 Argentina
        now_utc.replace(hour=15, minute=0, second=0),  # 15:00 UTC = 12:00 Argentina
        now_utc.replace(hour=17, minute=0, second=0),  # 17:00 UTC = 14:00 Argentina
        now_utc.replace(hour=20, minute=0, second=0),  # 20:00 UTC = 17:00 Argentina
    ]
    
    print(f"\n🧪 Testing Different Times:")
    for test_time in test_times:
        test_arg = test_time.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
        
        is_trading = calendar.is_trading_hours(test_time)
        current_window = calendar.get_current_window(test_time)
        is_valid_entry = calendar.is_valid_entry_time(test_time)
        
        print(f"   {test_time} ({test_arg.strftime('%H:%M')} ARG):")
        print(f"     Is Trading: {is_trading}")
        print(f"     Window: {current_window}")
        print(f"     Valid Entry: {is_valid_entry}")
        
        # Test window A specifically
        window_a_check = calendar.window_a.is_within_window(test_time)
        print(f"     Window A: {window_a_check}")
        
        # Test window B specifically
        window_b_check = calendar.window_b.is_within_window(test_time)
        print(f"     Window B: {window_b_check}")
        print()
    
    # Test the specific issue
    print(f"\n🔍 Specific Issue Debug:")
    print(f"   Current time: {now_utc}")
    print(f"   Current Argentina: {now_arg}")
    print(f"   Current Argentina time: {now_arg.time()}")
    
    # Check window A manually
    window_a_start = calendar.window_a.start_time
    window_a_end = calendar.window_a.end_time
    current_time = now_arg.time()
    
    print(f"   Window A start: {window_a_start}")
    print(f"   Window A end: {window_a_end}")
    print(f"   Current time: {current_time}")
    print(f"   Manual check: {window_a_start <= current_time <= window_a_end}")
    
    # Check if it's weekend
    from app.core.calendar import is_weekend
    is_weekend_check = is_weekend(now_utc)
    print(f"   Is weekend: {is_weekend_check}")
    
    # Check if there's any weekend logic in the calendar
    print(f"\n🔍 Calendar Methods:")
    print(f"   is_trading_hours: {calendar.is_trading_hours(now_utc)}")
    print(f"   get_current_window: {calendar.get_current_window(now_utc)}")
    print(f"   is_valid_entry_time: {calendar.is_valid_entry_time(now_utc)}")
    print(f"   should_force_close: {calendar.should_force_close(now_utc)}")

if __name__ == "__main__":
    debug_calendar_detailed()


