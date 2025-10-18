"""Tests for core.calendar module."""
import pytest
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from app.core.calendar import (
    TradingWindow,
    TradingCalendar,
    utc_to_local,
    local_to_utc,
    get_trading_day_bounds,
    is_weekend,
    get_next_trading_day,
    validate_timestamp_order,
    UTC_TZ,
    ARG_TZ,
    DEFAULT_WINDOW_A_START,
    DEFAULT_WINDOW_A_END,
    DEFAULT_WINDOW_B_START,
    DEFAULT_WINDOW_B_END,
    DEFAULT_FORCED_CLOSE_TIME
)


class TestTradingWindow:
    """Tests for TradingWindow class."""
    
    def test_trading_window_creation(self):
        """Test creating a trading window."""
        window = TradingWindow(
            name="Test Window",
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        assert window.name == "Test Window"
        assert window.start_time == time(9, 0)
        assert window.end_time == time(12, 0)
        assert window.enabled is True
    
    def test_is_within_window(self):
        """Test checking if time is within window."""
        window = TradingWindow(
            name="Morning",
            start_time=time(9, 0),
            end_time=time(12, 0),
            timezone="America/Argentina/Buenos_Aires"
        )
        
        # Time within window (10:00 local = 13:00 UTC)
        check_time = datetime(2023, 10, 20, 13, 0, tzinfo=UTC_TZ)
        assert window.is_within_window(check_time) is True
        
        # Time outside window (14:00 local = 17:00 UTC)
        check_time = datetime(2023, 10, 20, 17, 0, tzinfo=UTC_TZ)
        assert window.is_within_window(check_time) is False
    
    def test_disabled_window(self):
        """Test that disabled window returns False."""
        window = TradingWindow(
            name="Test",
            start_time=time(9, 0),
            end_time=time(12, 0),
            enabled=False
        )
        
        check_time = datetime(2023, 10, 20, 10, 0, tzinfo=ARG_TZ)
        assert window.is_within_window(check_time) is False
    
    def test_get_next_window_start(self):
        """Test getting next window start."""
        window = TradingWindow(
            name="Test",
            start_time=time(9, 0),
            end_time=time(12, 0),
            timezone="America/Argentina/Buenos_Aires"
        )
        
        # Before window start
        from_time = datetime(2023, 10, 20, 8, 0, tzinfo=ARG_TZ)
        next_start = window.get_next_window_start(from_time)
        
        assert next_start.hour == 9
        assert next_start.minute == 0
    
    def test_get_window_end(self):
        """Test getting window end."""
        window = TradingWindow(
            name="Test",
            start_time=time(9, 0),
            end_time=time(12, 0),
            timezone="America/Argentina/Buenos_Aires"
        )
        
        ref_time = datetime(2023, 10, 20, 10, 0, tzinfo=ARG_TZ)
        window_end = window.get_window_end(ref_time)
        
        assert window_end.hour == 12
        assert window_end.minute == 0


class TestTradingCalendar:
    """Tests for TradingCalendar class."""
    
    def test_calendar_creation_defaults(self):
        """Test creating calendar with default windows."""
        calendar = TradingCalendar()
        
        assert calendar.window_a.start_time == DEFAULT_WINDOW_A_START
        assert calendar.window_a.end_time == DEFAULT_WINDOW_A_END
        assert calendar.window_b.start_time == DEFAULT_WINDOW_B_START
        assert calendar.window_b.end_time == DEFAULT_WINDOW_B_END
        assert calendar.forced_close_time == DEFAULT_FORCED_CLOSE_TIME
    
    def test_calendar_creation_custom(self):
        """Test creating calendar with custom windows."""
        calendar = TradingCalendar(
            window_a_start=time(8, 0),
            window_a_end=time(11, 0),
            forced_close_time=time(18, 0)
        )
        
        assert calendar.window_a.start_time == time(8, 0)
        assert calendar.window_a.end_time == time(11, 0)
        assert calendar.forced_close_time == time(18, 0)
    
    def test_is_trading_hours_window_a(self):
        """Test checking if in window A."""
        calendar = TradingCalendar()
        
        # 10:00 local (13:00 UTC) - should be in window A (09:00-12:30)
        check_time = datetime(2023, 10, 20, 13, 0, tzinfo=UTC_TZ)
        assert calendar.is_trading_hours(check_time) is True
    
    def test_is_trading_hours_window_b(self):
        """Test checking if in window B."""
        calendar = TradingCalendar()
        
        # 15:00 local (18:00 UTC) - should be in window B (14:00-17:00)
        check_time = datetime(2023, 10, 20, 18, 0, tzinfo=UTC_TZ)
        assert calendar.is_trading_hours(check_time) is True
    
    def test_is_trading_hours_outside(self):
        """Test checking outside trading hours."""
        calendar = TradingCalendar()
        
        # 08:00 local (11:00 UTC) - before any window
        check_time = datetime(2023, 10, 20, 11, 0, tzinfo=UTC_TZ)
        assert calendar.is_trading_hours(check_time) is False
    
    def test_get_current_window(self):
        """Test getting current window name."""
        calendar = TradingCalendar()
        
        # Window A
        check_time = datetime(2023, 10, 20, 13, 0, tzinfo=UTC_TZ)
        assert calendar.get_current_window(check_time) == "A"
        
        # Window B
        check_time = datetime(2023, 10, 20, 18, 0, tzinfo=UTC_TZ)
        assert calendar.get_current_window(check_time) == "B"
        
        # Outside
        check_time = datetime(2023, 10, 20, 11, 0, tzinfo=UTC_TZ)
        assert calendar.get_current_window(check_time) is None
    
    def test_should_force_close(self):
        """Test forced close detection."""
        calendar = TradingCalendar(forced_close_time=time(16, 45))
        
        # Before forced close (15:00 local = 18:00 UTC)
        check_time = datetime(2023, 10, 20, 18, 0, tzinfo=UTC_TZ)
        assert calendar.should_force_close(check_time) is False
        
        # At forced close (16:45 local = 19:45 UTC)
        check_time = datetime(2023, 10, 20, 19, 45, tzinfo=UTC_TZ)
        assert calendar.should_force_close(check_time) is True
        
        # After forced close (17:00 local = 20:00 UTC)
        check_time = datetime(2023, 10, 20, 20, 0, tzinfo=UTC_TZ)
        assert calendar.should_force_close(check_time) is True
    
    def test_time_until_forced_close(self):
        """Test calculating time until forced close."""
        calendar = TradingCalendar(forced_close_time=time(16, 45))
        
        # 1 hour before forced close (15:45 local = 18:45 UTC)
        check_time = datetime(2023, 10, 20, 18, 45, tzinfo=UTC_TZ)
        time_until = calendar.time_until_forced_close(check_time)
        
        assert time_until.total_seconds() == 3600  # 1 hour
    
    def test_is_valid_entry_time(self):
        """Test checking if valid time to enter trade."""
        calendar = TradingCalendar(forced_close_time=time(16, 45))
        
        # In trading hours, enough time before close (14:00 local)
        check_time = datetime(2023, 10, 20, 17, 0, tzinfo=UTC_TZ)
        assert calendar.is_valid_entry_time(check_time, min_time_before_close_minutes=30) is True
        
        # Too close to forced close (16:30 local)
        check_time = datetime(2023, 10, 20, 19, 30, tzinfo=UTC_TZ)
        assert calendar.is_valid_entry_time(check_time, min_time_before_close_minutes=30) is False
        
        # Outside trading hours
        check_time = datetime(2023, 10, 20, 11, 0, tzinfo=UTC_TZ)
        assert calendar.is_valid_entry_time(check_time) is False
    
    def test_get_next_trading_window(self):
        """Test getting next trading window."""
        calendar = TradingCalendar()
        
        # Before window A (08:00 local)
        from_time = datetime(2023, 10, 20, 11, 0, tzinfo=UTC_TZ)
        window_name, start_time = calendar.get_next_trading_window(from_time)
        
        assert window_name in ["A", "B"]
        assert isinstance(start_time, datetime)


class TestTimezoneConversions:
    """Tests for timezone conversion utilities."""
    
    def test_utc_to_local(self):
        """Test UTC to local conversion."""
        utc_time = datetime(2023, 10, 20, 12, 0, tzinfo=UTC_TZ)
        local_time = utc_to_local(utc_time)
        
        # UTC-3: 12:00 UTC = 09:00 local
        assert local_time.hour == 9
        assert local_time.tzinfo == ARG_TZ
    
    def test_local_to_utc(self):
        """Test local to UTC conversion."""
        local_time = datetime(2023, 10, 20, 9, 0, tzinfo=ARG_TZ)
        utc_time = local_to_utc(local_time)
        
        # UTC-3: 09:00 local = 12:00 UTC
        assert utc_time.hour == 12
        assert utc_time.tzinfo == UTC_TZ
    
    def test_utc_to_local_naive(self):
        """Test UTC to local with naive datetime."""
        naive_time = datetime(2023, 10, 20, 12, 0)
        local_time = utc_to_local(naive_time)
        
        assert local_time.hour == 9
        assert local_time.tzinfo == ARG_TZ
    
    def test_local_to_utc_naive(self):
        """Test local to UTC with naive datetime."""
        naive_time = datetime(2023, 10, 20, 9, 0)
        utc_time = local_to_utc(naive_time)
        
        assert utc_time.hour == 12
        assert utc_time.tzinfo == UTC_TZ


class TestTradingDayBounds:
    """Tests for trading day bound calculations."""
    
    def test_get_trading_day_bounds(self):
        """Test getting trading day bounds."""
        ref_date = datetime(2023, 10, 20, 14, 30, tzinfo=ARG_TZ)
        start_utc, end_utc = get_trading_day_bounds(ref_date)
        
        # Start should be 00:00 local (03:00 UTC)
        assert start_utc.hour == 3
        assert start_utc.minute == 0
        assert start_utc.second == 0
        
        # End should be 23:59:59.999999 local
        assert end_utc > start_utc
    
    def test_get_trading_day_bounds_default(self):
        """Test getting trading day bounds with defaults."""
        start_utc, end_utc = get_trading_day_bounds()
        
        assert start_utc < end_utc
        assert start_utc.tzinfo == UTC_TZ
        assert end_utc.tzinfo == UTC_TZ


class TestWeekendDetection:
    """Tests for weekend detection."""
    
    def test_is_weekend_saturday(self):
        """Test Saturday detection."""
        saturday = datetime(2023, 10, 21, 12, 0, tzinfo=UTC_TZ)  # Saturday
        assert is_weekend(saturday) is True
    
    def test_is_weekend_sunday(self):
        """Test Sunday detection."""
        sunday = datetime(2023, 10, 22, 12, 0, tzinfo=UTC_TZ)  # Sunday
        assert is_weekend(sunday) is True
    
    def test_is_weekend_weekday(self):
        """Test weekday detection."""
        friday = datetime(2023, 10, 20, 12, 0, tzinfo=UTC_TZ)  # Friday
        assert is_weekend(friday) is False
    
    def test_get_next_trading_day(self):
        """Test getting next trading day."""
        friday = datetime(2023, 10, 20, 12, 0, tzinfo=UTC_TZ)  # Friday
        next_day = get_next_trading_day(friday, skip_weekends=True)
        
        # Next trading day should be Monday (3 days later)
        assert next_day.weekday() == 0  # Monday
    
    def test_get_next_trading_day_no_skip(self):
        """Test getting next day without skipping weekends."""
        friday = datetime(2023, 10, 20, 12, 0, tzinfo=UTC_TZ)  # Friday
        next_day = get_next_trading_day(friday, skip_weekends=False)
        
        # Next day should be Saturday
        assert next_day.weekday() == 5  # Saturday


class TestTimestampValidation:
    """Tests for timestamp validation."""
    
    def test_validate_timestamp_order_valid(self):
        """Test valid timestamp sequence."""
        timestamps = [1697810400000, 1697814000000, 1697817600000]  # Every hour
        is_valid, msg = validate_timestamp_order(timestamps, 3600000, allow_gaps=True)
        
        assert is_valid is True
        assert msg == ""
    
    def test_validate_timestamp_order_empty(self):
        """Test empty timestamp list."""
        is_valid, msg = validate_timestamp_order([], 3600000)
        assert is_valid is True
    
    def test_validate_timestamp_order_single(self):
        """Test single timestamp."""
        is_valid, msg = validate_timestamp_order([1697810400000], 3600000)
        assert is_valid is True
    
    def test_validate_timestamp_order_not_ascending(self):
        """Test non-ascending timestamps."""
        timestamps = [1697814000000, 1697810400000]  # Reversed
        is_valid, msg = validate_timestamp_order(timestamps, 3600000)
        
        assert is_valid is False
        assert "not in ascending order" in msg
    
    def test_validate_timestamp_order_with_gap(self):
        """Test timestamps with gap."""
        timestamps = [1697810400000, 1697817600000]  # 2 hour gap
        is_valid, msg = validate_timestamp_order(timestamps, 3600000, allow_gaps=True)
        
        assert is_valid is True
    
    def test_validate_timestamp_order_gap_not_allowed(self):
        """Test gap detection when not allowed."""
        timestamps = [1697810400000, 1697817600000]  # 2 hour gap
        is_valid, msg = validate_timestamp_order(timestamps, 3600000, allow_gaps=False)
        
        assert is_valid is False
        assert "Gap detected" in msg
    
    def test_validate_timestamp_order_invalid_spacing(self):
        """Test invalid timestamp spacing."""
        timestamps = [1697810400000, 1697812200000]  # 30 min gap (not multiple of 1h)
        is_valid, msg = validate_timestamp_order(timestamps, 3600000, allow_gaps=True)
        
        assert is_valid is False
        assert "not a multiple" in msg


class TestDefaultConstants:
    """Tests for default calendar constants."""
    
    def test_default_window_times(self):
        """Test that default window times are defined."""
        assert DEFAULT_WINDOW_A_START == time(9, 0)
        assert DEFAULT_WINDOW_A_END == time(12, 30)
        assert DEFAULT_WINDOW_B_START == time(14, 0)
        assert DEFAULT_WINDOW_B_END == time(17, 0)
        assert DEFAULT_FORCED_CLOSE_TIME == time(16, 45)
    
    def test_timezone_constants(self):
        """Test timezone constants."""
        assert UTC_TZ == ZoneInfo("UTC")
        assert ARG_TZ == ZoneInfo("America/Argentina/Buenos_Aires")

