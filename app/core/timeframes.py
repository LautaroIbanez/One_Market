"""Timeframe definitions and conversion utilities.

This module provides enums, constants, and utility functions for working with
different trading timeframes. It ensures type safety and consistency across the platform.
"""
from enum import Enum
from typing import Optional, List
from datetime import timedelta


class Timeframe(str, Enum):
    """Supported trading timeframes."""
    
    # Minutes
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    
    # Hours
    H1 = "1h"
    H2 = "2h"
    H4 = "4h"
    H6 = "6h"
    H8 = "8h"
    H12 = "12h"
    
    # Days
    D1 = "1d"
    D3 = "3d"
    
    # Week
    W1 = "1w"
    
    def __str__(self) -> str:
        """Return the string value of the timeframe."""
        return self.value
    
    @property
    def milliseconds(self) -> int:
        """Get milliseconds for this timeframe."""
        return TIMEFRAME_TO_MS[self.value]
    
    @property
    def seconds(self) -> int:
        """Get seconds for this timeframe."""
        return self.milliseconds // 1000
    
    @property
    def minutes(self) -> float:
        """Get minutes for this timeframe."""
        return self.seconds / 60
    
    @property
    def hours(self) -> float:
        """Get hours for this timeframe."""
        return self.minutes / 60
    
    @property
    def days(self) -> float:
        """Get days for this timeframe."""
        return self.hours / 24
    
    @property
    def timedelta(self) -> timedelta:
        """Get timedelta for this timeframe."""
        return timedelta(milliseconds=self.milliseconds)
    
    def to_higher_timeframe(self) -> Optional['Timeframe']:
        """Get the next higher timeframe in the hierarchy."""
        hierarchy = [
            Timeframe.M1, Timeframe.M3, Timeframe.M5, Timeframe.M15, Timeframe.M30,
            Timeframe.H1, Timeframe.H2, Timeframe.H4, Timeframe.H6, Timeframe.H8,
            Timeframe.H12, Timeframe.D1, Timeframe.D3, Timeframe.W1
        ]
        try:
            idx = hierarchy.index(self)
            if idx < len(hierarchy) - 1:
                return hierarchy[idx + 1]
        except ValueError:
            pass
        return None
    
    def to_lower_timeframe(self) -> Optional['Timeframe']:
        """Get the next lower timeframe in the hierarchy."""
        hierarchy = [
            Timeframe.M1, Timeframe.M3, Timeframe.M5, Timeframe.M15, Timeframe.M30,
            Timeframe.H1, Timeframe.H2, Timeframe.H4, Timeframe.H6, Timeframe.H8,
            Timeframe.H12, Timeframe.D1, Timeframe.D3, Timeframe.W1
        ]
        try:
            idx = hierarchy.index(self)
            if idx > 0:
                return hierarchy[idx - 1]
        except ValueError:
            pass
        return None


# Timeframe to milliseconds mapping
TIMEFRAME_TO_MS = {
    "1m": 60 * 1000,
    "3m": 3 * 60 * 1000,
    "5m": 5 * 60 * 1000,
    "15m": 15 * 60 * 1000,
    "30m": 30 * 60 * 1000,
    "1h": 60 * 60 * 1000,
    "2h": 2 * 60 * 60 * 1000,
    "4h": 4 * 60 * 60 * 1000,
    "6h": 6 * 60 * 60 * 1000,
    "8h": 8 * 60 * 60 * 1000,
    "12h": 12 * 60 * 60 * 1000,
    "1d": 24 * 60 * 60 * 1000,
    "3d": 3 * 24 * 60 * 60 * 1000,
    "1w": 7 * 24 * 60 * 60 * 1000,
}

# Primary timeframes for the platform
PRIMARY_TIMEFRAMES = [Timeframe.M15, Timeframe.H1, Timeframe.H4, Timeframe.D1]

# Intraday timeframes (< 1 day)
INTRADAY_TIMEFRAMES = [
    Timeframe.M1, Timeframe.M3, Timeframe.M5, Timeframe.M15, Timeframe.M30,
    Timeframe.H1, Timeframe.H2, Timeframe.H4, Timeframe.H6, Timeframe.H8, Timeframe.H12
]

# Daily and higher timeframes
DAILY_AND_HIGHER = [Timeframe.D1, Timeframe.D3, Timeframe.W1]


def get_timeframe_ms(timeframe: str) -> int:
    """Get milliseconds for a timeframe string.
    
    Args:
        timeframe: Timeframe string (e.g., '1h', '1d')
        
    Returns:
        Milliseconds for the timeframe
        
    Raises:
        ValueError: If timeframe is not supported
    """
    if timeframe not in TIMEFRAME_TO_MS:
        raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(TIMEFRAME_TO_MS.keys())}")
    return TIMEFRAME_TO_MS[timeframe]


def get_timeframe_seconds(timeframe: str) -> int:
    """Get seconds for a timeframe string.
    
    Args:
        timeframe: Timeframe string (e.g., '1h', '1d')
        
    Returns:
        Seconds for the timeframe
    """
    return get_timeframe_ms(timeframe) // 1000


def get_timeframe_minutes(timeframe: str) -> float:
    """Get minutes for a timeframe string.
    
    Args:
        timeframe: Timeframe string (e.g., '1h', '1d')
        
    Returns:
        Minutes for the timeframe
    """
    return get_timeframe_seconds(timeframe) / 60


def get_timeframe_hours(timeframe: str) -> float:
    """Get hours for a timeframe string.
    
    Args:
        timeframe: Timeframe string (e.g., '1h', '1d')
        
    Returns:
        Hours for the timeframe
    """
    return get_timeframe_minutes(timeframe) / 60


def get_timeframe_days(timeframe: str) -> float:
    """Get days for a timeframe string.
    
    Args:
        timeframe: Timeframe string (e.g., '1h', '1d')
        
    Returns:
        Days for the timeframe
    """
    return get_timeframe_hours(timeframe) / 24


def parse_timeframe(timeframe_str: str) -> Timeframe:
    """Parse a timeframe string to a Timeframe enum.
    
    Args:
        timeframe_str: Timeframe string (e.g., '1h', '1d')
        
    Returns:
        Timeframe enum
        
    Raises:
        ValueError: If timeframe string is invalid
    """
    try:
        return Timeframe(timeframe_str)
    except ValueError:
        raise ValueError(f"Invalid timeframe: {timeframe_str}. Supported: {[tf.value for tf in Timeframe]}")


def is_valid_timeframe(timeframe_str: str) -> bool:
    """Check if a timeframe string is valid.
    
    Args:
        timeframe_str: Timeframe string to validate
        
    Returns:
        True if valid, False otherwise
    """
    return timeframe_str in TIMEFRAME_TO_MS


def get_bars_per_day(timeframe: str) -> int:
    """Get the number of bars per day for a timeframe.
    
    Args:
        timeframe: Timeframe string (e.g., '1h', '1d')
        
    Returns:
        Number of bars in a 24-hour period
        
    Note:
        For timeframes >= 1d, returns 1 as we consider the daily close
    """
    tf_ms = get_timeframe_ms(timeframe)
    day_ms = 24 * 60 * 60 * 1000
    
    if tf_ms >= day_ms:
        return 1
    
    return day_ms // tf_ms


def get_bars_per_period(timeframe: str, period_days: int) -> int:
    """Get the number of bars in a period of days.
    
    Args:
        timeframe: Timeframe string (e.g., '1h', '1d')
        period_days: Number of days in the period
        
    Returns:
        Approximate number of bars in the period
    """
    bars_per_day = get_bars_per_day(timeframe)
    return bars_per_day * period_days


def convert_bars_between_timeframes(
    source_timeframe: str,
    target_timeframe: str,
    num_bars: int
) -> int:
    """Convert number of bars from one timeframe to another.
    
    Args:
        source_timeframe: Source timeframe string
        target_timeframe: Target timeframe string
        num_bars: Number of bars in source timeframe
        
    Returns:
        Equivalent number of bars in target timeframe
        
    Example:
        convert_bars_between_timeframes('1h', '1d', 24) -> 1
        convert_bars_between_timeframes('1d', '1h', 1) -> 24
    """
    source_ms = get_timeframe_ms(source_timeframe)
    target_ms = get_timeframe_ms(target_timeframe)
    
    total_time_ms = source_ms * num_bars
    target_bars = total_time_ms / target_ms
    
    return int(target_bars)


def get_timeframe_multiplier(base_timeframe: str, higher_timeframe: str) -> int:
    """Get the multiplier between two timeframes.
    
    Args:
        base_timeframe: Base timeframe (e.g., '15m')
        higher_timeframe: Higher timeframe (e.g., '1h')
        
    Returns:
        Multiplier (e.g., 4 for 15m -> 1h)
        
    Raises:
        ValueError: If higher_timeframe is not actually higher than base_timeframe
    """
    base_ms = get_timeframe_ms(base_timeframe)
    higher_ms = get_timeframe_ms(higher_timeframe)
    
    if higher_ms < base_ms:
        raise ValueError(f"{higher_timeframe} is not higher than {base_timeframe}")
    
    if higher_ms % base_ms != 0:
        raise ValueError(f"{higher_timeframe} is not a clean multiple of {base_timeframe}")
    
    return higher_ms // base_ms


def align_timestamp_to_timeframe(timestamp_ms: int, timeframe: str) -> int:
    """Align a timestamp to the start of its timeframe period.
    
    Args:
        timestamp_ms: Timestamp in milliseconds
        timeframe: Timeframe string
        
    Returns:
        Aligned timestamp in milliseconds
        
    Example:
        align_timestamp_to_timeframe(1697810999000, '1h')
        -> Returns timestamp at start of the hour
    """
    tf_ms = get_timeframe_ms(timeframe)
    return (timestamp_ms // tf_ms) * tf_ms


def get_supported_timeframes() -> List[str]:
    """Get list of all supported timeframe strings.
    
    Returns:
        List of supported timeframe strings
    """
    return [tf.value for tf in Timeframe]


def is_intraday(timeframe: str) -> bool:
    """Check if a timeframe is intraday (< 1 day).
    
    Args:
        timeframe: Timeframe string
        
    Returns:
        True if intraday, False otherwise
    """
    tf_enum = parse_timeframe(timeframe)
    return tf_enum in INTRADAY_TIMEFRAMES


def is_daily_or_higher(timeframe: str) -> bool:
    """Check if a timeframe is daily or higher.
    
    Args:
        timeframe: Timeframe string
        
    Returns:
        True if daily or higher, False otherwise
    """
    tf_enum = parse_timeframe(timeframe)
    return tf_enum in DAILY_AND_HIGHER

