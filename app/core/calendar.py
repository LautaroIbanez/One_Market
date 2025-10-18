"""Trading calendar and session management utilities.

This module handles trading windows, session A/B management, forced close times,
and timezone conversions between UTC and local time (UTC-3).
"""
from datetime import datetime, time, timedelta
from typing import Optional, Tuple, Literal
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field


# Timezone definitions
UTC_TZ = ZoneInfo("UTC")
ARG_TZ = ZoneInfo("America/Argentina/Buenos_Aires")  # UTC-3

# Default trading windows (in local time UTC-3)
DEFAULT_WINDOW_A_START = time(9, 0)   # 09:00 local (12:00 UTC)
DEFAULT_WINDOW_A_END = time(12, 30)   # 12:30 local (15:30 UTC)
DEFAULT_WINDOW_B_START = time(14, 0)  # 14:00 local (17:00 UTC)
DEFAULT_WINDOW_B_END = time(17, 0)    # 17:00 local (20:00 UTC)

# Forced close time (in local time UTC-3)
DEFAULT_FORCED_CLOSE_TIME = time(16, 45)  # 16:45 local (19:45 UTC)


class TradingWindow(BaseModel):
    """Definition of a trading window with start and end times."""
    
    name: str = Field(..., description="Window name (e.g., 'Window A', 'Window B')")
    start_time: time = Field(..., description="Start time in local timezone")
    end_time: time = Field(..., description="End time in local timezone")
    timezone: str = Field(default="America/Argentina/Buenos_Aires", description="Timezone for the window")
    enabled: bool = Field(default=True, description="Whether this window is active")
    
    def is_within_window(self, check_time: datetime) -> bool:
        """Check if a datetime falls within this trading window.
        
        Args:
            check_time: Datetime to check (timezone-aware)
            
        Returns:
            True if within window, False otherwise
        """
        if not self.enabled:
            return False
        
        # Convert to local timezone
        local_time = check_time.astimezone(ZoneInfo(self.timezone))
        current_time = local_time.time()
        
        # Handle windows that cross midnight
        if self.start_time <= self.end_time:
            return self.start_time <= current_time <= self.end_time
        else:
            return current_time >= self.start_time or current_time <= self.end_time
    
    def get_next_window_start(self, from_time: datetime) -> datetime:
        """Get the next occurrence of this window's start time.
        
        Args:
            from_time: Reference datetime (timezone-aware)
            
        Returns:
            Next window start datetime
        """
        local_time = from_time.astimezone(ZoneInfo(self.timezone))
        window_start = local_time.replace(
            hour=self.start_time.hour,
            minute=self.start_time.minute,
            second=0,
            microsecond=0
        )
        
        # If window start is in the past today, move to tomorrow
        if window_start <= local_time:
            window_start += timedelta(days=1)
        
        return window_start
    
    def get_window_end(self, reference_time: datetime) -> datetime:
        """Get the end time of this window for a given reference time.
        
        Args:
            reference_time: Reference datetime (timezone-aware)
            
        Returns:
            Window end datetime
        """
        local_time = reference_time.astimezone(ZoneInfo(self.timezone))
        window_end = local_time.replace(
            hour=self.end_time.hour,
            minute=self.end_time.minute,
            second=0,
            microsecond=0
        )
        
        # Handle windows that cross midnight
        if self.end_time < self.start_time:
            window_end += timedelta(days=1)
        
        return window_end


class TradingCalendar:
    """Trading calendar manager for session A/B windows and forced close times."""
    
    def __init__(
        self,
        window_a_start: time = DEFAULT_WINDOW_A_START,
        window_a_end: time = DEFAULT_WINDOW_A_END,
        window_b_start: time = DEFAULT_WINDOW_B_START,
        window_b_end: time = DEFAULT_WINDOW_B_END,
        forced_close_time: time = DEFAULT_FORCED_CLOSE_TIME,
        local_timezone: str = "America/Argentina/Buenos_Aires"
    ):
        """Initialize trading calendar with custom windows.
        
        Args:
            window_a_start: Start time for Window A (local time)
            window_a_end: End time for Window A (local time)
            window_b_start: Start time for Window B (local time)
            window_b_end: End time for Window B (local time)
            forced_close_time: Time to force close all positions (local time)
            local_timezone: Local timezone name
        """
        self.local_tz = ZoneInfo(local_timezone)
        self.forced_close_time = forced_close_time
        
        self.window_a = TradingWindow(
            name="Window A",
            start_time=window_a_start,
            end_time=window_a_end,
            timezone=local_timezone
        )
        
        self.window_b = TradingWindow(
            name="Window B",
            start_time=window_b_start,
            end_time=window_b_end,
            timezone=local_timezone
        )
    
    def is_trading_hours(self, check_time: Optional[datetime] = None) -> bool:
        """Check if current time is within any trading window.
        
        Args:
            check_time: Datetime to check (defaults to now in UTC)
            
        Returns:
            True if within trading hours, False otherwise
        """
        if check_time is None:
            check_time = datetime.now(UTC_TZ)
        
        # Ensure timezone-aware
        if check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=UTC_TZ)
        
        return self.window_a.is_within_window(check_time) or self.window_b.is_within_window(check_time)
    
    def get_current_window(self, check_time: Optional[datetime] = None) -> Optional[Literal["A", "B"]]:
        """Get the current trading window (A or B).
        
        Args:
            check_time: Datetime to check (defaults to now in UTC)
            
        Returns:
            "A", "B", or None if outside trading hours
        """
        if check_time is None:
            check_time = datetime.now(UTC_TZ)
        
        if check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=UTC_TZ)
        
        if self.window_a.is_within_window(check_time):
            return "A"
        elif self.window_b.is_within_window(check_time):
            return "B"
        return None
    
    def should_force_close(self, check_time: Optional[datetime] = None) -> bool:
        """Check if positions should be force-closed at this time.
        
        Args:
            check_time: Datetime to check (defaults to now in UTC)
            
        Returns:
            True if should force close, False otherwise
        """
        if check_time is None:
            check_time = datetime.now(UTC_TZ)
        
        if check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=UTC_TZ)
        
        local_time = check_time.astimezone(self.local_tz)
        current_time = local_time.time()
        
        # Check if current time is at or past forced close time
        return current_time >= self.forced_close_time
    
    def time_until_forced_close(self, check_time: Optional[datetime] = None) -> timedelta:
        """Get time remaining until forced close.
        
        Args:
            check_time: Datetime to check (defaults to now in UTC)
            
        Returns:
            Timedelta until forced close (negative if past close time)
        """
        if check_time is None:
            check_time = datetime.now(UTC_TZ)
        
        if check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=UTC_TZ)
        
        local_time = check_time.astimezone(self.local_tz)
        
        # Create forced close datetime for today
        close_dt = local_time.replace(
            hour=self.forced_close_time.hour,
            minute=self.forced_close_time.minute,
            second=0,
            microsecond=0
        )
        
        # If already past close time today, use tomorrow's close
        if close_dt <= local_time:
            close_dt += timedelta(days=1)
        
        return close_dt - local_time
    
    def get_next_trading_window(self, from_time: Optional[datetime] = None) -> Tuple[Literal["A", "B"], datetime]:
        """Get the next trading window and its start time.
        
        Args:
            from_time: Reference datetime (defaults to now in UTC)
            
        Returns:
            Tuple of (window_name, start_datetime)
        """
        if from_time is None:
            from_time = datetime.now(UTC_TZ)
        
        if from_time.tzinfo is None:
            from_time = from_time.replace(tzinfo=UTC_TZ)
        
        # Get next start times for both windows
        next_a = self.window_a.get_next_window_start(from_time)
        next_b = self.window_b.get_next_window_start(from_time)
        
        # Return the earliest one
        if next_a <= next_b:
            return ("A", next_a)
        else:
            return ("B", next_b)
    
    def is_valid_entry_time(self, check_time: Optional[datetime] = None, min_time_before_close_minutes: int = 30) -> bool:
        """Check if it's valid to enter a new trade.
        
        Valid entry requires:
        1. Within trading hours
        2. Not too close to forced close time
        
        Args:
            check_time: Datetime to check (defaults to now in UTC)
            min_time_before_close_minutes: Minimum minutes before forced close to allow entry
            
        Returns:
            True if valid entry time, False otherwise
        """
        if check_time is None:
            check_time = datetime.now(UTC_TZ)
        
        if check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=UTC_TZ)
        
        # Must be within trading hours
        if not self.is_trading_hours(check_time):
            return False
        
        # Must have enough time before forced close
        time_until_close = self.time_until_forced_close(check_time)
        min_time_required = timedelta(minutes=min_time_before_close_minutes)
        
        return time_until_close >= min_time_required


def utc_to_local(utc_time: datetime, local_tz: str = "America/Argentina/Buenos_Aires") -> datetime:
    """Convert UTC datetime to local timezone.
    
    Args:
        utc_time: Datetime in UTC
        local_tz: Target timezone name
        
    Returns:
        Datetime in local timezone
    """
    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=UTC_TZ)
    
    return utc_time.astimezone(ZoneInfo(local_tz))


def local_to_utc(local_time: datetime, local_tz: str = "America/Argentina/Buenos_Aires") -> datetime:
    """Convert local datetime to UTC.
    
    Args:
        local_time: Datetime in local timezone
        local_tz: Source timezone name
        
    Returns:
        Datetime in UTC
    """
    if local_time.tzinfo is None:
        local_time = local_time.replace(tzinfo=ZoneInfo(local_tz))
    
    return local_time.astimezone(UTC_TZ)


def get_trading_day_bounds(
    reference_date: Optional[datetime] = None,
    local_tz: str = "America/Argentina/Buenos_Aires"
) -> Tuple[datetime, datetime]:
    """Get start and end bounds for a trading day in UTC.
    
    Args:
        reference_date: Reference date (defaults to today)
        local_tz: Local timezone name
        
    Returns:
        Tuple of (day_start_utc, day_end_utc)
    """
    if reference_date is None:
        reference_date = datetime.now(ZoneInfo(local_tz))
    
    if reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=ZoneInfo(local_tz))
    
    # Start of day in local timezone
    day_start_local = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # End of day in local timezone
    day_end_local = day_start_local + timedelta(days=1) - timedelta(microseconds=1)
    
    # Convert to UTC
    day_start_utc = day_start_local.astimezone(UTC_TZ)
    day_end_utc = day_end_local.astimezone(UTC_TZ)
    
    return (day_start_utc, day_end_utc)


def is_weekend(check_time: Optional[datetime] = None) -> bool:
    """Check if a datetime falls on a weekend.
    
    Args:
        check_time: Datetime to check (defaults to now)
        
    Returns:
        True if Saturday or Sunday, False otherwise
    """
    if check_time is None:
        check_time = datetime.now(UTC_TZ)
    
    # 5 = Saturday, 6 = Sunday
    return check_time.weekday() >= 5


def get_next_trading_day(from_date: Optional[datetime] = None, skip_weekends: bool = True) -> datetime:
    """Get the next trading day.
    
    Args:
        from_date: Reference date (defaults to today)
        skip_weekends: Whether to skip weekends
        
    Returns:
        Next trading day datetime
    """
    if from_date is None:
        from_date = datetime.now(UTC_TZ)
    
    if from_date.tzinfo is None:
        from_date = from_date.replace(tzinfo=UTC_TZ)
    
    next_day = from_date + timedelta(days=1)
    
    if skip_weekends:
        while is_weekend(next_day):
            next_day += timedelta(days=1)
    
    return next_day


def validate_timestamp_order(timestamps: list[int], timeframe_ms: int, allow_gaps: bool = True) -> Tuple[bool, str]:
    """Validate that timestamps are properly ordered and spaced.
    
    Args:
        timestamps: List of timestamps in milliseconds
        timeframe_ms: Expected timeframe in milliseconds
        allow_gaps: Whether to allow gaps in the sequence
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not timestamps:
        return (True, "")
    
    if len(timestamps) == 1:
        return (True, "")
    
    for i in range(1, len(timestamps)):
        prev_ts = timestamps[i - 1]
        curr_ts = timestamps[i]
        
        # Check ordering
        if curr_ts <= prev_ts:
            return (False, f"Timestamps not in ascending order at index {i}: {prev_ts} >= {curr_ts}")
        
        # Check spacing
        diff = curr_ts - prev_ts
        
        if not allow_gaps and diff != timeframe_ms:
            return (False, f"Gap detected at index {i}: expected {timeframe_ms}ms, got {diff}ms")
        
        if diff % timeframe_ms != 0:
            return (False, f"Invalid spacing at index {i}: {diff}ms is not a multiple of {timeframe_ms}ms")
    
    return (True, "")

