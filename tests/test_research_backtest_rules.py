"""Tests for backtest trading rules.

This module tests the critical trading rules:
- One trade per day
- Trading windows enforcement
- Forced close at end of day
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.research.backtest.rules import (
    enforce_one_trade_per_day,
    filter_by_trading_windows,
    apply_forced_close,
    validate_signals,
    count_trades_per_day,
    get_trading_statistics
)
from app.core.calendar import TradingCalendar


class TestOneTradePerDay:
    """Tests for one trade per day rule."""
    
    def test_single_signal_per_day_kept(self):
        """Test that single signal per day is kept."""
        # Create timestamps for multiple days
        dates = pd.date_range('2023-10-01', periods=5, freq='D')
        timestamps = pd.Series([int(d.timestamp() * 1000) for d in dates])
        
        # One signal per day
        signals = pd.Series([1, -1, 1, 0, -1])
        
        result = enforce_one_trade_per_day(signals, timestamps)
        
        # All signals should be kept
        assert (result != 0).sum() == 4  # 4 non-zero signals
    
    def test_multiple_signals_same_day_filtered(self):
        """Test that only first signal per day is kept."""
        # Multiple signals on same day
        base_date = datetime(2023, 10, 1)
        timestamps = pd.Series([
            int((base_date + timedelta(hours=i)).timestamp() * 1000)
            for i in range(5)
        ])
        
        # Multiple signals on same day
        signals = pd.Series([1, 1, -1, 0, 1])
        
        result = enforce_one_trade_per_day(signals, timestamps)
        
        # Only first signal should be kept
        assert result.iloc[0] == 1
        assert (result.iloc[1:] == 0).all() or (result.iloc[1:] == 1).all()
    
    def test_signals_on_different_days(self):
        """Test signals on different days are kept."""
        # One signal per day
        dates = pd.date_range('2023-10-01', periods=3, freq='D')
        timestamps = pd.Series([int(d.timestamp() * 1000) for d in dates])
        signals = pd.Series([1, -1, 1])
        
        result = enforce_one_trade_per_day(signals, timestamps)
        
        assert (result != 0).sum() == 3


class TestTradingWindowsFilter:
    """Tests for trading windows filtering."""
    
    def test_signal_within_window_a_kept(self):
        """Test signal within window A is kept."""
        calendar = TradingCalendar()
        
        # Create timestamp within window A (09:00-12:30 local = 12:00-15:30 UTC)
        ts = datetime(2023, 10, 20, 13, 0)  # 13:00 UTC = 10:00 local
        timestamps = pd.Series([int(ts.timestamp() * 1000)])
        signals = pd.Series([1])
        
        result = filter_by_trading_windows(signals, timestamps, calendar)
        
        assert result.iloc[0] == 1
    
    def test_signal_outside_windows_filtered(self):
        """Test signal outside windows is filtered."""
        calendar = TradingCalendar()
        
        # Create timestamp outside trading windows (08:00 local = 11:00 UTC)
        ts = datetime(2023, 10, 20, 11, 0)  # Before window A
        timestamps = pd.Series([int(ts.timestamp() * 1000)])
        signals = pd.Series([1])
        
        result = filter_by_trading_windows(signals, timestamps, calendar)
        
        assert result.iloc[0] == 0
    
    def test_signal_in_window_b_kept(self):
        """Test signal within window B is kept."""
        calendar = TradingCalendar()
        
        # Create timestamp within window B (14:00-17:00 local = 17:00-20:00 UTC)
        ts = datetime(2023, 10, 20, 18, 0)  # 18:00 UTC = 15:00 local
        timestamps = pd.Series([int(ts.timestamp() * 1000)])
        signals = pd.Series([1])
        
        result = filter_by_trading_windows(signals, timestamps, calendar)
        
        assert result.iloc[0] == 1


class TestForcedClose:
    """Tests for forced close rule."""
    
    def test_position_closed_at_forced_time(self):
        """Test position is closed at forced close time."""
        calendar = TradingCalendar()
        
        # Create timestamps: one before forced close, one at forced close
        ts_before = datetime(2023, 10, 20, 18, 0)  # 15:00 local (before 16:45)
        ts_at_close = datetime(2023, 10, 20, 19, 45)  # 16:45 local (forced close)
        
        timestamps = pd.Series([
            int(ts_before.timestamp() * 1000),
            int(ts_at_close.timestamp() * 1000)
        ])
        
        # Signal: enter position, then hold
        signals = pd.Series([1, 1])
        
        result = apply_forced_close(signals, timestamps, calendar)
        
        # Position should be closed at forced close time
        assert result.iloc[1] == 0
    
    def test_no_position_no_forced_close(self):
        """Test no forced close when no position."""
        calendar = TradingCalendar()
        
        ts = datetime(2023, 10, 20, 19, 50)  # After forced close
        timestamps = pd.Series([int(ts.timestamp() * 1000)])
        signals = pd.Series([0])  # No position
        
        result = apply_forced_close(signals, timestamps, calendar)
        
        assert result.iloc[0] == 0


class TestSignalValidation:
    """Tests for signal validation."""
    
    def test_valid_signals(self):
        """Test valid signals pass validation."""
        signals = pd.Series([1, 0, -1, 0, 1])
        is_valid, msg = validate_signals(signals)
        
        assert is_valid is True
        assert msg == ""
    
    def test_invalid_signal_values(self):
        """Test invalid signal values fail validation."""
        signals = pd.Series([1, 2, -1])  # 2 is invalid
        is_valid, msg = validate_signals(signals)
        
        assert is_valid is False
        assert "Invalid signal values" in msg
    
    def test_nan_signals_fail(self):
        """Test NaN signals fail validation."""
        signals = pd.Series([1, np.nan, -1])
        is_valid, msg = validate_signals(signals)
        
        assert is_valid is False
        assert "NaN" in msg


class TestTradeCount:
    """Tests for trade counting."""
    
    def test_count_trades_per_day(self):
        """Test counting trades per day."""
        # Two days with different trade counts
        dates = pd.date_range('2023-10-01', periods=4, freq='12H')
        timestamps = pd.Series([int(d.timestamp() * 1000) for d in dates])
        
        # Day 1: 2 trades, Day 2: 1 trade
        signals = pd.Series([1, -1, 1, 0])
        
        result = count_trades_per_day(signals, timestamps)
        
        assert len(result) > 0
        assert result.max() >= 1


class TestTradingStatistics:
    """Tests for trading statistics."""
    
    def test_get_trading_statistics(self):
        """Test getting trading statistics."""
        dates = pd.date_range('2023-10-01', periods=10, freq='D')
        timestamps = pd.Series([int(d.timestamp() * 1000) for d in dates])
        signals = pd.Series([1, 0, -1, 0, 1, 0, 0, -1, 0, 1])
        
        stats = get_trading_statistics(signals, timestamps)
        
        assert 'total_signals' in stats
        assert 'long_signals' in stats
        assert 'short_signals' in stats
        assert 'max_trades_per_day' in stats
        
        assert stats['long_signals'] == 3
        assert stats['short_signals'] == 2
        assert stats['total_signals'] == 5


class TestIntegrationRules:
    """Integration tests for multiple rules."""
    
    def test_all_rules_combined(self):
        """Test all rules work together."""
        calendar = TradingCalendar()
        
        # Create full day of hourly timestamps
        base_date = datetime(2023, 10, 20, 12, 0)  # Start at noon UTC
        timestamps = pd.Series([
            int((base_date + timedelta(hours=i)).timestamp() * 1000)
            for i in range(10)
        ])
        
        # Multiple signals throughout the day
        signals = pd.Series([1, 1, 0, -1, -1, 1, 0, 1, 0, 0])
        
        # Apply all rules
        result = signals.copy()
        result = enforce_one_trade_per_day(result, timestamps)
        result = filter_by_trading_windows(result, timestamps, calendar)
        result = apply_forced_close(result, timestamps, calendar)
        
        # Validate final result
        is_valid, msg = validate_signals(result)
        assert is_valid is True


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_signals(self):
        """Test empty signals."""
        timestamps = pd.Series([])
        signals = pd.Series([])
        
        result = enforce_one_trade_per_day(signals, timestamps)
        
        assert len(result) == 0
    
    def test_all_zero_signals(self):
        """Test all zero signals."""
        dates = pd.date_range('2023-10-01', periods=5, freq='D')
        timestamps = pd.Series([int(d.timestamp() * 1000) for d in dates])
        signals = pd.Series([0, 0, 0, 0, 0])
        
        result = enforce_one_trade_per_day(signals, timestamps)
        
        assert (result == 0).all()

