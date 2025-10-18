"""Trading rules enforcement.

This module implements the specific trading rules:
- One trade per day
- Trading windows (A/B)
- Forced close at end of day
"""
import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime
from app.core.calendar import TradingCalendar


def enforce_one_trade_per_day(signals: pd.Series, timestamps: pd.Series) -> pd.Series:
    """Enforce maximum one trade per day rule.
    
    If multiple signals occur on the same day, only the first is kept.
    
    Args:
        signals: Signal series (1=long, -1=short, 0=flat)
        timestamps: Timestamp series (milliseconds)
        
    Returns:
        Filtered signal series
    """
    # Convert timestamps to dates
    dates = pd.to_datetime(timestamps, unit='ms').dt.date
    
    # Create result series
    filtered_signals = pd.Series(0, index=signals.index)
    
    # Track last signal date
    last_signal_date = None
    in_position = False
    
    for i in range(len(signals)):
        current_date = dates.iloc[i]
        current_signal = signals.iloc[i]
        
        # Entry signal
        if current_signal != 0 and not in_position:
            # Check if we already traded today
            if last_signal_date != current_date:
                filtered_signals.iloc[i] = current_signal
                last_signal_date = current_date
                in_position = True
        
        # Exit signal (when signal becomes 0 or reverses)
        elif in_position and (current_signal == 0 or np.sign(current_signal) != np.sign(filtered_signals.iloc[i-1])):
            filtered_signals.iloc[i] = 0
            in_position = False
    
    return filtered_signals


def filter_by_trading_windows(
    signals: pd.Series,
    timestamps: pd.Series,
    calendar: TradingCalendar
) -> pd.Series:
    """Filter signals to only allow entries during trading windows.
    
    Args:
        signals: Signal series
        timestamps: Timestamp series (milliseconds)
        calendar: TradingCalendar with window definitions
        
    Returns:
        Filtered signal series
    """
    filtered_signals = signals.copy()
    
    for i in range(len(signals)):
        if signals.iloc[i] != 0:  # Only check entry signals
            ts = pd.to_datetime(timestamps.iloc[i], unit='ms').tz_localize('UTC')
            
            # Check if within trading hours
            if not calendar.is_trading_hours(ts):
                filtered_signals.iloc[i] = 0
    
    return filtered_signals


def apply_forced_close(
    signals: pd.Series,
    timestamps: pd.Series,
    calendar: TradingCalendar
) -> pd.Series:
    """Force close all positions at end of day.
    
    Args:
        signals: Signal series
        timestamps: Timestamp series (milliseconds)
        calendar: TradingCalendar with forced close time
        
    Returns:
        Signal series with forced closes
    """
    modified_signals = signals.copy()
    
    in_position = False
    position_type = 0
    
    for i in range(len(signals)):
        current_signal = signals.iloc[i]
        ts = pd.to_datetime(timestamps.iloc[i], unit='ms').tz_localize('UTC')
        
        # Track position state
        if current_signal != 0:
            in_position = True
            position_type = current_signal
        elif current_signal == 0 and in_position:
            in_position = False
            position_type = 0
        
        # Force close if needed
        if in_position and calendar.should_force_close(ts):
            modified_signals.iloc[i] = 0  # Force exit
            in_position = False
            position_type = 0
    
    return modified_signals


def validate_signals(signals: pd.Series) -> tuple[bool, str]:
    """Validate signal series.
    
    Args:
        signals: Signal series
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for valid values
    unique_values = signals.unique()
    valid_values = {-1, 0, 1}
    
    if not set(unique_values).issubset(valid_values):
        invalid = set(unique_values) - valid_values
        return False, f"Invalid signal values: {invalid}. Must be -1, 0, or 1"
    
    # Check for NaN
    if signals.isna().any():
        return False, "Signals contain NaN values"
    
    return True, ""


def count_trades_per_day(signals: pd.Series, timestamps: pd.Series) -> pd.Series:
    """Count number of trades per day.
    
    Args:
        signals: Signal series
        timestamps: Timestamp series
        
    Returns:
        Series with trade counts per day
    """
    dates = pd.to_datetime(timestamps, unit='ms').dt.date
    
    # Count signal changes per day
    signal_changes = (signals != 0) & (signals != signals.shift(1))
    trades_per_day = signal_changes.groupby(dates).sum()
    
    return trades_per_day


def get_trading_statistics(
    signals: pd.Series,
    timestamps: pd.Series,
    calendar: Optional[TradingCalendar] = None
) -> dict:
    """Get trading statistics for signals.
    
    Args:
        signals: Signal series
        timestamps: Timestamp series
        calendar: Optional TradingCalendar
        
    Returns:
        Dictionary with statistics
    """
    # Convert timestamps
    dt_timestamps = pd.to_datetime(timestamps, unit='ms')
    dates = dt_timestamps.dt.date
    
    # Count signals
    total_signals = (signals != 0).sum()
    long_signals = (signals == 1).sum()
    short_signals = (signals == -1).sum()
    
    # Trades per day
    trades_per_day = count_trades_per_day(signals, timestamps)
    max_trades_per_day = trades_per_day.max() if len(trades_per_day) > 0 else 0
    avg_trades_per_day = trades_per_day.mean() if len(trades_per_day) > 0 else 0
    
    # Trading days
    trading_days = len(trades_per_day[trades_per_day > 0])
    total_days = len(trades_per_day)
    
    stats = {
        'total_signals': int(total_signals),
        'long_signals': int(long_signals),
        'short_signals': int(short_signals),
        'max_trades_per_day': int(max_trades_per_day),
        'avg_trades_per_day': float(avg_trades_per_day),
        'trading_days': int(trading_days),
        'total_days': int(total_days),
        'trading_frequency': float(trading_days / total_days) if total_days > 0 else 0
    }
    
    # Window statistics if calendar provided
    if calendar:
        window_a_signals = 0
        window_b_signals = 0
        outside_window_signals = 0
        
        for i in range(len(signals)):
            if signals.iloc[i] != 0:
                ts = dt_timestamps.iloc[i].tz_localize('UTC')
                window = calendar.get_current_window(ts)
                
                if window == "A":
                    window_a_signals += 1
                elif window == "B":
                    window_b_signals += 1
                else:
                    outside_window_signals += 1
        
        stats['window_a_signals'] = window_a_signals
        stats['window_b_signals'] = window_b_signals
        stats['outside_window_signals'] = outside_window_signals
    
    return stats

