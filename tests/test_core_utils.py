"""Tests for core.utils module."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from app.core.utils import (
    ensure_utc,
    ensure_timezone,
    convert_timezone,
    timestamp_to_datetime,
    datetime_to_timestamp,
    shift_series,
    shift_dataframe,
    prevent_lookahead,
    validate_numeric,
    safe_divide,
    safe_percentage,
    clamp,
    normalize,
    is_nan_or_inf,
    clean_numeric_series,
    validate_ohlc_consistency,
    round_to_tick_size,
    round_to_lot_size,
    format_percentage,
    format_currency,
    calculate_pnl,
    calculate_pnl_percentage,
    exponential_moving_average,
    simple_moving_average,
    calculate_returns,
    resample_ohlcv,
    validate_timestamp_sequence,
    UTC,
    ARG_TZ
)


class TestTimezoneUtils:
    """Tests for timezone utility functions."""
    
    def test_ensure_utc_naive(self):
        """Test ensuring UTC with naive datetime."""
        naive_dt = datetime(2023, 10, 20, 12, 0)
        utc_dt = ensure_utc(naive_dt)
        
        assert utc_dt.tzinfo == UTC
        assert utc_dt.hour == 12
    
    def test_ensure_utc_already_utc(self):
        """Test ensuring UTC with already UTC datetime."""
        utc_dt = datetime(2023, 10, 20, 12, 0, tzinfo=UTC)
        result = ensure_utc(utc_dt)
        
        assert result == utc_dt
    
    def test_ensure_utc_conversion(self):
        """Test ensuring UTC with non-UTC datetime."""
        arg_dt = datetime(2023, 10, 20, 9, 0, tzinfo=ARG_TZ)
        utc_dt = ensure_utc(arg_dt)
        
        assert utc_dt.tzinfo == UTC
        assert utc_dt.hour == 12  # 9:00 ARG = 12:00 UTC
    
    def test_ensure_timezone_naive(self):
        """Test ensuring timezone with naive datetime."""
        naive_dt = datetime(2023, 10, 20, 12, 0)
        arg_dt = ensure_timezone(naive_dt, ARG_TZ)
        
        assert arg_dt.tzinfo == ARG_TZ
    
    def test_convert_timezone(self):
        """Test converting between timezones."""
        utc_dt = datetime(2023, 10, 20, 12, 0, tzinfo=UTC)
        arg_dt = convert_timezone(utc_dt, ARG_TZ)
        
        assert arg_dt.tzinfo == ARG_TZ
        assert arg_dt.hour == 9
    
    def test_convert_timezone_naive_raises(self):
        """Test that converting naive datetime raises error."""
        naive_dt = datetime(2023, 10, 20, 12, 0)
        
        with pytest.raises(ValueError, match="timezone-naive"):
            convert_timezone(naive_dt, UTC)
    
    def test_timestamp_to_datetime(self):
        """Test converting timestamp to datetime."""
        timestamp_ms = 1697810400000  # 2023-10-20 12:00:00 UTC
        dt = timestamp_to_datetime(timestamp_ms)
        
        assert dt.year == 2023
        assert dt.month == 10
        assert dt.day == 20
        assert dt.tzinfo == timezone.utc
    
    def test_timestamp_to_datetime_with_tz(self):
        """Test converting timestamp with target timezone."""
        timestamp_ms = 1697810400000
        dt = timestamp_to_datetime(timestamp_ms, tz=ARG_TZ)
        
        assert dt.hour == 9  # 12:00 UTC = 09:00 ARG
        assert dt.tzinfo == ARG_TZ
    
    def test_datetime_to_timestamp(self):
        """Test converting datetime to timestamp."""
        dt = datetime(2023, 10, 20, 12, 0, tzinfo=UTC)
        timestamp = datetime_to_timestamp(dt)
        
        assert timestamp == 1697810400000
    
    def test_datetime_to_timestamp_naive(self):
        """Test converting naive datetime to timestamp."""
        dt = datetime(2023, 10, 20, 12, 0)
        timestamp = datetime_to_timestamp(dt)
        
        assert isinstance(timestamp, int)


class TestLookaheadPrevention:
    """Tests for lookahead bias prevention."""
    
    def test_shift_series(self):
        """Test shifting series."""
        series = pd.Series([1, 2, 3, 4, 5])
        shifted = shift_series(series, periods=1)
        
        assert shifted.iloc[0] == pytest.approx(np.nan, nan_ok=True)
        assert shifted.iloc[1] == 1
        assert shifted.iloc[2] == 2
    
    def test_shift_series_negative_raises(self):
        """Test that negative shift raises error."""
        series = pd.Series([1, 2, 3])
        
        with pytest.raises(ValueError, match="lookahead bias"):
            shift_series(series, periods=-1)
    
    def test_shift_dataframe(self):
        """Test shifting dataframe."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        shifted = shift_dataframe(df, periods=1)
        
        assert pd.isna(shifted['a'].iloc[0])
        assert shifted['a'].iloc[1] == 1
    
    def test_shift_dataframe_specific_columns(self):
        """Test shifting specific columns."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        shifted = shift_dataframe(df, periods=1, columns=['a'])
        
        assert pd.isna(shifted['a'].iloc[0])
        assert shifted['b'].iloc[0] == 4  # Not shifted
    
    def test_prevent_lookahead(self):
        """Test preventing lookahead in signals."""
        df = pd.DataFrame({
            'price': [100, 101, 102, 103],
            'signal': [0, 1, -1, 0]
        })
        
        result = prevent_lookahead(df, signal_column='signal', shift_periods=1)
        
        assert pd.isna(result['signal'].iloc[0])
        assert result['signal'].iloc[1] == 0


class TestNumericValidation:
    """Tests for numeric validation utilities."""
    
    def test_validate_numeric_valid(self):
        """Test validating valid numeric values."""
        assert validate_numeric(10.5) is True
        assert validate_numeric(0) is True
        assert validate_numeric(-5.2) is True
    
    def test_validate_numeric_with_bounds(self):
        """Test validation with bounds."""
        assert validate_numeric(5, min_value=0, max_value=10) is True
        assert validate_numeric(-1, min_value=0) is False
        assert validate_numeric(11, max_value=10) is False
    
    def test_validate_numeric_nan(self):
        """Test that NaN is invalid."""
        assert validate_numeric(np.nan) is False
        assert validate_numeric(float('nan')) is False
    
    def test_validate_numeric_inf(self):
        """Test that infinity is invalid."""
        assert validate_numeric(float('inf')) is False
        assert validate_numeric(float('-inf')) is False
    
    def test_validate_numeric_none(self):
        """Test None validation."""
        assert validate_numeric(None, allow_none=True) is True
        assert validate_numeric(None, allow_none=False) is False
    
    def test_validate_numeric_non_numeric(self):
        """Test non-numeric values."""
        assert validate_numeric("not a number") is False
        assert validate_numeric([1, 2, 3]) is False


class TestSafeMath:
    """Tests for safe mathematical operations."""
    
    def test_safe_divide(self):
        """Test safe division."""
        assert safe_divide(10, 2) == 5
        assert safe_divide(10, 0) == 0  # Default
        assert safe_divide(10, 0, default=99) == 99
    
    def test_safe_divide_inf(self):
        """Test safe division with infinity."""
        assert safe_divide(10, float('inf'), default=0) == 0
        assert safe_divide(float('inf'), 10, default=0) == 0
    
    def test_safe_percentage(self):
        """Test safe percentage calculation."""
        assert safe_percentage(25, 100) == 0.25
        assert safe_percentage(10, 0) == 0  # Default
        assert safe_percentage(10, 0, default=1.0) == 1.0
    
    def test_clamp(self):
        """Test clamping values."""
        assert clamp(5, 0, 10) == 5
        assert clamp(-5, 0, 10) == 0
        assert clamp(15, 0, 10) == 10
    
    def test_normalize(self):
        """Test normalization."""
        assert normalize(5, 0, 10) == 0.5
        assert normalize(0, 0, 10) == 0.0
        assert normalize(10, 0, 10) == 1.0
    
    def test_normalize_same_bounds(self):
        """Test normalization with same min/max."""
        assert normalize(5, 5, 5) == 0.0


class TestNaNInfChecking:
    """Tests for NaN and infinity checking."""
    
    def test_is_nan_or_inf(self):
        """Test NaN and infinity detection."""
        assert is_nan_or_inf(np.nan) is True
        assert is_nan_or_inf(float('nan')) is True
        assert is_nan_or_inf(float('inf')) is True
        assert is_nan_or_inf(float('-inf')) is True
        assert is_nan_or_inf(10.5) is False
        assert is_nan_or_inf("not a number") is True
    
    def test_clean_numeric_series_ffill(self):
        """Test cleaning series with forward fill."""
        series = pd.Series([1, np.nan, 3, np.inf, 5])
        cleaned = clean_numeric_series(series, fill_method='ffill')
        
        assert not cleaned.isna().any()
        assert not np.isinf(cleaned).any()
    
    def test_clean_numeric_series_value(self):
        """Test cleaning series with value fill."""
        series = pd.Series([1, np.nan, 3, np.inf, 5])
        cleaned = clean_numeric_series(series, fill_method='value', fill_value=0)
        
        assert cleaned.iloc[1] == 0
        assert cleaned.iloc[3] == 0


class TestOHLCValidation:
    """Tests for OHLC validation."""
    
    def test_validate_ohlc_valid(self):
        """Test validating valid OHLC."""
        is_valid, msg = validate_ohlc_consistency(100, 105, 98, 102)
        
        assert is_valid is True
        assert msg == ""
    
    def test_validate_ohlc_high_too_low(self):
        """Test that low high price fails."""
        is_valid, msg = validate_ohlc_consistency(100, 99, 98, 102)
        
        assert is_valid is False
        assert "High" in msg
    
    def test_validate_ohlc_low_too_high(self):
        """Test that high low price fails."""
        is_valid, msg = validate_ohlc_consistency(100, 105, 103, 102)
        
        assert is_valid is False
        assert "Low" in msg
    
    def test_validate_ohlc_negative_price(self):
        """Test that negative prices fail."""
        is_valid, msg = validate_ohlc_consistency(-100, 105, 98, 102)
        
        assert is_valid is False


class TestRounding:
    """Tests for rounding utilities."""
    
    def test_round_to_tick_size(self):
        """Test rounding to tick size."""
        assert round_to_tick_size(50123.45, 0.1) == 50123.4
        assert round_to_tick_size(50123.45, 1.0) == 50123.0
        assert round_to_tick_size(50123.45, 10.0) == 50120.0
    
    def test_round_to_lot_size(self):
        """Test rounding to lot size."""
        assert round_to_lot_size(1.234, 0.01) == 1.23
        assert round_to_lot_size(1.234, 0.1) == 1.2
        assert round_to_lot_size(1.234, 1.0) == 1.0


class TestFormatting:
    """Tests for formatting utilities."""
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        assert format_percentage(0.0125, decimals=2) == "1.25%"
        assert format_percentage(0.5, decimals=1) == "50.0%"
    
    def test_format_currency(self):
        """Test currency formatting."""
        assert format_currency(1234.56) == "$1,234.56"
        assert format_currency(1234.56, symbol="€") == "€1,234.56"
        assert format_currency(1234.56, decimals=0) == "$1,235"


class TestPnLCalculations:
    """Tests for PnL calculations."""
    
    def test_calculate_pnl_long_profit(self):
        """Test PnL for profitable long."""
        pnl = calculate_pnl(entry_price=50000, exit_price=51000, quantity=1.0, side='long')
        assert pnl == 1000
    
    def test_calculate_pnl_long_loss(self):
        """Test PnL for losing long."""
        pnl = calculate_pnl(entry_price=50000, exit_price=49000, quantity=1.0, side='long')
        assert pnl == -1000
    
    def test_calculate_pnl_short_profit(self):
        """Test PnL for profitable short."""
        pnl = calculate_pnl(entry_price=50000, exit_price=49000, quantity=1.0, side='short')
        assert pnl == 1000
    
    def test_calculate_pnl_short_loss(self):
        """Test PnL for losing short."""
        pnl = calculate_pnl(entry_price=50000, exit_price=51000, quantity=1.0, side='short')
        assert pnl == -1000
    
    def test_calculate_pnl_invalid_side(self):
        """Test that invalid side raises error."""
        with pytest.raises(ValueError, match="Invalid side"):
            calculate_pnl(50000, 51000, 1.0, 'invalid')
    
    def test_calculate_pnl_percentage_long(self):
        """Test percentage PnL for long."""
        pnl_pct = calculate_pnl_percentage(entry_price=50000, exit_price=51000, side='long')
        assert pnl_pct == 0.02  # 2%
    
    def test_calculate_pnl_percentage_short(self):
        """Test percentage PnL for short."""
        pnl_pct = calculate_pnl_percentage(entry_price=50000, exit_price=49000, side='short')
        assert pnl_pct == 0.02  # 2%


class TestMovingAverages:
    """Tests for moving average calculations."""
    
    def test_exponential_moving_average(self):
        """Test EMA calculation."""
        series = pd.Series([100, 101, 102, 103, 104, 105])
        ema = exponential_moving_average(series, span=3)
        
        assert len(ema) == len(series)
        assert ema.iloc[-1] > series.iloc[0]
    
    def test_simple_moving_average(self):
        """Test SMA calculation."""
        series = pd.Series([100, 101, 102, 103, 104, 105])
        sma = simple_moving_average(series, window=3)
        
        assert len(sma) == len(series)
        assert pd.isna(sma.iloc[0])  # First values are NaN
        assert sma.iloc[2] == 101  # Mean of [100, 101, 102]


class TestReturnsCalculation:
    """Tests for returns calculation."""
    
    def test_calculate_returns_simple(self):
        """Test simple returns calculation."""
        prices = pd.Series([100, 101, 99, 102])
        returns = calculate_returns(prices, method='simple')
        
        assert pd.isna(returns.iloc[0])
        assert returns.iloc[1] == pytest.approx(0.01)
        assert returns.iloc[2] == pytest.approx(-0.0198, rel=1e-3)
    
    def test_calculate_returns_log(self):
        """Test log returns calculation."""
        prices = pd.Series([100, 101, 99, 102])
        returns = calculate_returns(prices, method='log')
        
        assert pd.isna(returns.iloc[0])
        assert returns.iloc[1] > 0
    
    def test_calculate_returns_invalid_method(self):
        """Test that invalid method raises error."""
        prices = pd.Series([100, 101, 102])
        
        with pytest.raises(ValueError, match="Unknown return method"):
            calculate_returns(prices, method='invalid')


class TestResampleOHLCV:
    """Tests for OHLCV resampling."""
    
    def test_resample_ohlcv(self):
        """Test resampling OHLCV data."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2023-10-20', periods=24, freq='1H'),
            'open': range(100, 124),
            'high': range(101, 125),
            'low': range(99, 123),
            'close': range(100, 124),
            'volume': [1000] * 24
        })
        
        resampled = resample_ohlcv(df, target_timeframe='4H')
        
        assert len(resampled) == 6  # 24 hours / 4 hours
        assert 'open' in resampled.columns
        assert 'high' in resampled.columns


class TestTimestampSequenceValidation:
    """Tests for timestamp sequence validation."""
    
    def test_validate_timestamp_sequence_valid(self):
        """Test valid timestamp sequence."""
        timestamps = [1000000, 2000000, 3000000]
        is_valid, msg = validate_timestamp_sequence(timestamps, tolerance_ms=1000)
        
        assert is_valid is True
        assert msg == ""
    
    def test_validate_timestamp_sequence_not_ascending(self):
        """Test non-ascending sequence."""
        timestamps = [3000000, 2000000, 1000000]
        is_valid, msg = validate_timestamp_sequence(timestamps)
        
        assert is_valid is False
        assert "not after" in msg
    
    def test_validate_timestamp_sequence_too_close(self):
        """Test timestamps too close together."""
        timestamps = [1000000, 1000100]
        is_valid, msg = validate_timestamp_sequence(timestamps, tolerance_ms=1000)
        
        assert is_valid is False
        assert "too close" in msg
    
    def test_validate_timestamp_sequence_empty(self):
        """Test empty sequence."""
        is_valid, msg = validate_timestamp_sequence([])
        assert is_valid is True

