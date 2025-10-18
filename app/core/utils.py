"""General utility functions for the trading platform.

This module provides timezone helpers, lookahead bias prevention,
numerical validations, and other reusable utilities.
"""
from datetime import datetime, timezone
from typing import Optional, Union, List, Any
import pandas as pd
import numpy as np
from zoneinfo import ZoneInfo


# Timezone constants
UTC = ZoneInfo("UTC")
ARG_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is in UTC timezone.
    
    Args:
        dt: Datetime object (may be naive or aware)
        
    Returns:
        Timezone-aware datetime in UTC
    """
    if dt.tzinfo is None:
        # Assume naive datetime is already UTC
        return dt.replace(tzinfo=UTC)
    elif dt.tzinfo != UTC:
        # Convert to UTC
        return dt.astimezone(UTC)
    return dt


def ensure_timezone(dt: datetime, tz: Union[str, ZoneInfo] = UTC) -> datetime:
    """Ensure datetime has the specified timezone.
    
    Args:
        dt: Datetime object (may be naive or aware)
        tz: Target timezone (ZoneInfo or string)
        
    Returns:
        Timezone-aware datetime in specified timezone
    """
    if isinstance(tz, str):
        tz = ZoneInfo(tz)
    
    if dt.tzinfo is None:
        # Assume naive datetime is in target timezone
        return dt.replace(tzinfo=tz)
    elif dt.tzinfo != tz:
        # Convert to target timezone
        return dt.astimezone(tz)
    return dt


def convert_timezone(dt: datetime, target_tz: Union[str, ZoneInfo]) -> datetime:
    """Convert datetime to target timezone.
    
    Args:
        dt: Datetime object (must be timezone-aware)
        target_tz: Target timezone
        
    Returns:
        Datetime in target timezone
        
    Raises:
        ValueError: If datetime is timezone-naive
    """
    if dt.tzinfo is None:
        raise ValueError("Cannot convert timezone-naive datetime. Use ensure_timezone() first.")
    
    if isinstance(target_tz, str):
        target_tz = ZoneInfo(target_tz)
    
    return dt.astimezone(target_tz)


def timestamp_to_datetime(timestamp_ms: int, tz: Optional[Union[str, ZoneInfo]] = None) -> datetime:
    """Convert millisecond timestamp to datetime.
    
    Args:
        timestamp_ms: Timestamp in milliseconds
        tz: Target timezone (defaults to UTC)
        
    Returns:
        Timezone-aware datetime
    """
    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    
    if tz is not None:
        if isinstance(tz, str):
            tz = ZoneInfo(tz)
        dt = dt.astimezone(tz)
    
    return dt


def datetime_to_timestamp(dt: datetime) -> int:
    """Convert datetime to millisecond timestamp.
    
    Args:
        dt: Datetime object
        
    Returns:
        Timestamp in milliseconds
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    
    return int(dt.timestamp() * 1000)


def shift_series(series: pd.Series, periods: int = 1) -> pd.Series:
    """Shift series to prevent lookahead bias.
    
    This is a wrapper around pandas shift() to make lookahead prevention explicit.
    
    Args:
        series: Series to shift
        periods: Number of periods to shift (positive = backward)
        
    Returns:
        Shifted series
        
    Note:
        Always use positive periods to shift data backward (into the past).
        This ensures you're not using future data in calculations.
    """
    if periods < 0:
        raise ValueError(f"Negative periods ({periods}) can cause lookahead bias. Use positive values.")
    
    return series.shift(periods)


def shift_dataframe(df: pd.DataFrame, periods: int = 1, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Shift dataframe columns to prevent lookahead bias.
    
    Args:
        df: DataFrame to shift
        periods: Number of periods to shift (positive = backward)
        columns: Specific columns to shift (None = all columns)
        
    Returns:
        DataFrame with shifted columns
        
    Note:
        Always use positive periods to shift data backward (into the past).
    """
    if periods < 0:
        raise ValueError(f"Negative periods ({periods}) can cause lookahead bias. Use positive values.")
    
    df_shifted = df.copy()
    
    if columns is None:
        columns = df.columns.tolist()
    
    for col in columns:
        if col in df.columns:
            df_shifted[col] = df[col].shift(periods)
    
    return df_shifted


def prevent_lookahead(df: pd.DataFrame, signal_column: str = 'signal', shift_periods: int = 1) -> pd.DataFrame:
    """Shift signal column to prevent lookahead bias in backtesting.
    
    Args:
        df: DataFrame with signals
        signal_column: Name of signal column
        shift_periods: Number of periods to shift
        
    Returns:
        DataFrame with shifted signals
        
    Note:
        This ensures signals generated on bar N are only acted upon on bar N+1.
    """
    df = df.copy()
    
    if signal_column in df.columns:
        df[signal_column] = shift_series(df[signal_column], shift_periods)
    
    return df


def validate_numeric(value: Any, min_value: Optional[float] = None, max_value: Optional[float] = None, allow_none: bool = False) -> bool:
    """Validate that a value is numeric and within bounds.
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        allow_none: Whether None is acceptable
        
    Returns:
        True if valid, False otherwise
    """
    if value is None:
        return allow_none
    
    try:
        num_value = float(value)
        
        # Check for NaN or infinity
        if not np.isfinite(num_value):
            return False
        
        # Check bounds
        if min_value is not None and num_value < min_value:
            return False
        
        if max_value is not None and num_value > max_value:
            return False
        
        return True
    except (ValueError, TypeError):
        return False


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, avoiding division by zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Value to return if division is invalid
        
    Returns:
        Result of division or default value
    """
    if denominator == 0 or not np.isfinite(denominator):
        return default
    
    result = numerator / denominator
    
    if not np.isfinite(result):
        return default
    
    return result


def safe_percentage(part: float, total: float, default: float = 0.0) -> float:
    """Safely calculate percentage, avoiding division by zero.
    
    Args:
        part: Part value
        total: Total value
        default: Value to return if calculation is invalid
        
    Returns:
        Percentage (0.0 to 1.0) or default value
    """
    if total == 0 or not np.isfinite(total):
        return default
    
    pct = part / total
    
    if not np.isfinite(pct):
        return default
    
    return pct


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp value between min and max.
    
    Args:
        value: Value to clamp
        min_value: Minimum value
        max_value: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_value, min(max_value, value))


def normalize(value: float, min_value: float, max_value: float) -> float:
    """Normalize value to 0-1 range.
    
    Args:
        value: Value to normalize
        min_value: Minimum value in range
        max_value: Maximum value in range
        
    Returns:
        Normalized value (0.0 to 1.0)
        
    Note:
        Returns 0.0 if min_value == max_value
    """
    if max_value == min_value:
        return 0.0
    
    return (value - min_value) / (max_value - min_value)


def is_nan_or_inf(value: Any) -> bool:
    """Check if value is NaN or infinity.
    
    Args:
        value: Value to check
        
    Returns:
        True if NaN or infinity, False otherwise
    """
    try:
        return not np.isfinite(float(value))
    except (ValueError, TypeError):
        return True


def clean_numeric_series(series: pd.Series, fill_method: str = 'ffill', fill_value: Optional[float] = None) -> pd.Series:
    """Clean numeric series by handling NaN and infinity values.
    
    Args:
        series: Series to clean
        fill_method: Method to fill missing values ('ffill', 'bfill', 'value', 'interpolate', 'drop')
        fill_value: Value to use if fill_method is 'value'
        
    Returns:
        Cleaned series
    """
    series = series.copy()
    
    # Replace infinity with NaN
    series = series.replace([np.inf, -np.inf], np.nan)
    
    # Fill NaN based on method
    if fill_method == 'ffill':
        series = series.ffill()
    elif fill_method == 'bfill':
        series = series.bfill()
    elif fill_method == 'value':
        if fill_value is None:
            fill_value = 0.0
        series = series.fillna(fill_value)
    elif fill_method == 'interpolate':
        series = series.interpolate(method='linear')
    elif fill_method == 'drop':
        series = series.dropna()
    
    return series


def validate_ohlc_consistency(open_price: float, high: float, low: float, close: float) -> tuple[bool, str]:
    """Validate OHLC price consistency.
    
    Args:
        open_price: Open price
        high: High price
        low: Low price
        close: Close price
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check all values are positive
    if not all(validate_numeric(p, min_value=0) for p in [open_price, high, low, close]):
        return (False, "All OHLC prices must be positive numbers")
    
    # Check high is highest
    if high < max(open_price, close, low):
        return (False, f"High ({high}) must be >= open, close, and low")
    
    # Check low is lowest
    if low > min(open_price, close, high):
        return (False, f"Low ({low}) must be <= open, close, and high")
    
    return (True, "")


def round_to_tick_size(price: float, tick_size: float) -> float:
    """Round price to nearest tick size.
    
    Args:
        price: Price to round
        tick_size: Minimum price increment
        
    Returns:
        Rounded price
    """
    if tick_size <= 0:
        return price
    
    return round(price / tick_size) * tick_size


def round_to_lot_size(quantity: float, lot_size: float) -> float:
    """Round quantity to nearest lot size.
    
    Args:
        quantity: Quantity to round
        lot_size: Minimum quantity increment
        
    Returns:
        Rounded quantity
    """
    if lot_size <= 0:
        return quantity
    
    return round(quantity / lot_size) * lot_size


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format value as percentage string.
    
    Args:
        value: Value to format (0.01 = 1%)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def format_currency(value: float, symbol: str = "$", decimals: int = 2) -> str:
    """Format value as currency string.
    
    Args:
        value: Value to format
        symbol: Currency symbol
        decimals: Number of decimal places
        
    Returns:
        Formatted currency string
    """
    return f"{symbol}{value:,.{decimals}f}"


def calculate_pnl(entry_price: float, exit_price: float, quantity: float, side: str) -> float:
    """Calculate profit/loss for a trade.
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        quantity: Position quantity
        side: Position side ('long' or 'short')
        
    Returns:
        PnL (positive = profit, negative = loss)
    """
    side = side.lower()
    
    if side == 'long':
        pnl = (exit_price - entry_price) * quantity
    elif side == 'short':
        pnl = (entry_price - exit_price) * quantity
    else:
        raise ValueError(f"Invalid side: {side}. Must be 'long' or 'short'")
    
    return pnl


def calculate_pnl_percentage(entry_price: float, exit_price: float, side: str) -> float:
    """Calculate profit/loss percentage for a trade.
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        side: Position side ('long' or 'short')
        
    Returns:
        PnL percentage (0.01 = 1%)
    """
    side = side.lower()
    
    if entry_price == 0:
        return 0.0
    
    if side == 'long':
        pnl_pct = (exit_price - entry_price) / entry_price
    elif side == 'short':
        pnl_pct = (entry_price - exit_price) / entry_price
    else:
        raise ValueError(f"Invalid side: {side}. Must be 'long' or 'short'")
    
    return pnl_pct


def exponential_moving_average(series: pd.Series, span: int) -> pd.Series:
    """Calculate exponential moving average.
    
    Args:
        series: Input series
        span: EMA span
        
    Returns:
        EMA series
    """
    return series.ewm(span=span, adjust=False).mean()


def simple_moving_average(series: pd.Series, window: int) -> pd.Series:
    """Calculate simple moving average.
    
    Args:
        series: Input series
        window: SMA window
        
    Returns:
        SMA series
    """
    return series.rolling(window=window).mean()


def calculate_returns(prices: pd.Series, method: str = 'simple') -> pd.Series:
    """Calculate returns from price series.
    
    Args:
        prices: Series of prices
        method: Return calculation method ('simple' or 'log')
        
    Returns:
        Series of returns
    """
    if method == 'simple':
        returns = prices.pct_change()
    elif method == 'log':
        returns = np.log(prices / prices.shift(1))
    else:
        raise ValueError(f"Unknown return method: {method}. Use 'simple' or 'log'")
    
    return returns


def resample_ohlcv(df: pd.DataFrame, target_timeframe: str, timestamp_col: str = 'timestamp') -> pd.DataFrame:
    """Resample OHLCV data to a different timeframe.
    
    Args:
        df: DataFrame with OHLCV data
        target_timeframe: Target timeframe (pandas freq string, e.g., '1H', '1D')
        timestamp_col: Name of timestamp column
        
    Returns:
        Resampled DataFrame
    """
    df = df.copy()
    
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], unit='ms')
    
    # Set timestamp as index
    df = df.set_index(timestamp_col)
    
    # Resample
    resampled = df.resample(target_timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    # Drop rows with NaN (gaps in data)
    resampled = resampled.dropna()
    
    # Reset index
    resampled = resampled.reset_index()
    
    return resampled


def validate_timestamp_sequence(timestamps: List[int], tolerance_ms: int = 1000) -> tuple[bool, str]:
    """Validate that timestamps are in ascending order.
    
    Args:
        timestamps: List of timestamps in milliseconds
        tolerance_ms: Tolerance for timestamp differences
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(timestamps) <= 1:
        return (True, "")
    
    for i in range(1, len(timestamps)):
        if timestamps[i] <= timestamps[i-1]:
            return (False, f"Timestamp {i} ({timestamps[i]}) is not after previous ({timestamps[i-1]})")
        
        # Check if timestamps are too close
        diff = timestamps[i] - timestamps[i-1]
        if diff < tolerance_ms:
            return (False, f"Timestamps {i-1} and {i} are too close ({diff}ms < {tolerance_ms}ms)")
    
    return (True, "")

