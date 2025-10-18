"""Tests for core.timeframes module."""
import pytest
from datetime import timedelta
from app.core.timeframes import (
    Timeframe,
    get_timeframe_ms,
    get_timeframe_seconds,
    get_timeframe_minutes,
    get_timeframe_hours,
    get_timeframe_days,
    parse_timeframe,
    is_valid_timeframe,
    get_bars_per_day,
    get_bars_per_period,
    convert_bars_between_timeframes,
    get_timeframe_multiplier,
    align_timestamp_to_timeframe,
    get_supported_timeframes,
    is_intraday,
    is_daily_or_higher,
    TIMEFRAME_TO_MS,
    PRIMARY_TIMEFRAMES
)


class TestTimeframeEnum:
    """Tests for Timeframe enum."""
    
    def test_timeframe_values(self):
        """Test that timeframe enum has correct string values."""
        assert Timeframe.M1.value == "1m"
        assert Timeframe.H1.value == "1h"
        assert Timeframe.D1.value == "1d"
    
    def test_timeframe_str(self):
        """Test that timeframe converts to string correctly."""
        assert str(Timeframe.M15) == "15m"
        assert str(Timeframe.H4) == "4h"
    
    def test_timeframe_milliseconds(self):
        """Test milliseconds property."""
        assert Timeframe.M1.milliseconds == 60 * 1000
        assert Timeframe.H1.milliseconds == 3600 * 1000
        assert Timeframe.D1.milliseconds == 86400 * 1000
    
    def test_timeframe_seconds(self):
        """Test seconds property."""
        assert Timeframe.M1.seconds == 60
        assert Timeframe.H1.seconds == 3600
    
    def test_timeframe_minutes(self):
        """Test minutes property."""
        assert Timeframe.M15.minutes == 15
        assert Timeframe.H1.minutes == 60
    
    def test_timeframe_hours(self):
        """Test hours property."""
        assert Timeframe.H1.hours == 1
        assert Timeframe.H4.hours == 4
        assert Timeframe.D1.hours == 24
    
    def test_timeframe_days(self):
        """Test days property."""
        assert Timeframe.D1.days == 1
        assert Timeframe.W1.days == 7
    
    def test_timeframe_timedelta(self):
        """Test timedelta property."""
        assert Timeframe.M1.timedelta == timedelta(minutes=1)
        assert Timeframe.H1.timedelta == timedelta(hours=1)
        assert Timeframe.D1.timedelta == timedelta(days=1)
    
    def test_to_higher_timeframe(self):
        """Test getting next higher timeframe."""
        assert Timeframe.M15.to_higher_timeframe() == Timeframe.M30
        assert Timeframe.H1.to_higher_timeframe() == Timeframe.H2
        assert Timeframe.W1.to_higher_timeframe() is None
    
    def test_to_lower_timeframe(self):
        """Test getting next lower timeframe."""
        assert Timeframe.M15.to_lower_timeframe() == Timeframe.M5
        assert Timeframe.H1.to_lower_timeframe() == Timeframe.M30
        assert Timeframe.M1.to_lower_timeframe() is None


class TestTimeframeConversions:
    """Tests for timeframe conversion functions."""
    
    def test_get_timeframe_ms(self):
        """Test millisecond conversion."""
        assert get_timeframe_ms("1m") == 60_000
        assert get_timeframe_ms("1h") == 3_600_000
        assert get_timeframe_ms("1d") == 86_400_000
    
    def test_get_timeframe_ms_invalid(self):
        """Test that invalid timeframe raises error."""
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            get_timeframe_ms("invalid")
    
    def test_get_timeframe_seconds(self):
        """Test seconds conversion."""
        assert get_timeframe_seconds("1m") == 60
        assert get_timeframe_seconds("1h") == 3600
    
    def test_get_timeframe_minutes(self):
        """Test minutes conversion."""
        assert get_timeframe_minutes("15m") == 15
        assert get_timeframe_minutes("1h") == 60
    
    def test_get_timeframe_hours(self):
        """Test hours conversion."""
        assert get_timeframe_hours("1h") == 1
        assert get_timeframe_hours("4h") == 4
        assert get_timeframe_hours("1d") == 24
    
    def test_get_timeframe_days(self):
        """Test days conversion."""
        assert get_timeframe_days("1d") == 1
        assert get_timeframe_days("1w") == 7


class TestTimeframeValidation:
    """Tests for timeframe validation."""
    
    def test_parse_timeframe_valid(self):
        """Test parsing valid timeframe strings."""
        assert parse_timeframe("1m") == Timeframe.M1
        assert parse_timeframe("15m") == Timeframe.M15
        assert parse_timeframe("1h") == Timeframe.H1
        assert parse_timeframe("1d") == Timeframe.D1
    
    def test_parse_timeframe_invalid(self):
        """Test parsing invalid timeframe string."""
        with pytest.raises(ValueError, match="Invalid timeframe"):
            parse_timeframe("invalid")
    
    def test_is_valid_timeframe(self):
        """Test timeframe validation."""
        assert is_valid_timeframe("1m") is True
        assert is_valid_timeframe("1h") is True
        assert is_valid_timeframe("1d") is True
        assert is_valid_timeframe("invalid") is False
    
    def test_get_supported_timeframes(self):
        """Test getting list of supported timeframes."""
        supported = get_supported_timeframes()
        assert "1m" in supported
        assert "1h" in supported
        assert "1d" in supported
        assert len(supported) == len(TIMEFRAME_TO_MS)


class TestBarsCalculations:
    """Tests for bar count calculations."""
    
    def test_get_bars_per_day(self):
        """Test bars per day calculation."""
        assert get_bars_per_day("1m") == 1440  # 24 * 60
        assert get_bars_per_day("15m") == 96   # 24 * 4
        assert get_bars_per_day("1h") == 24
        assert get_bars_per_day("4h") == 6
        assert get_bars_per_day("1d") == 1
    
    def test_get_bars_per_period(self):
        """Test bars per period calculation."""
        assert get_bars_per_period("1h", 1) == 24
        assert get_bars_per_period("1h", 7) == 168  # 7 days
        assert get_bars_per_period("15m", 1) == 96
    
    def test_convert_bars_between_timeframes(self):
        """Test converting bars between timeframes."""
        # 1 day = 24 hours
        assert convert_bars_between_timeframes("1h", "1d", 24) == 1
        
        # 1 hour = 4x 15min bars
        assert convert_bars_between_timeframes("15m", "1h", 4) == 1
        
        # 1 day = 24 hours
        assert convert_bars_between_timeframes("1d", "1h", 1) == 24


class TestTimeframeMultiplier:
    """Tests for timeframe multiplier calculations."""
    
    def test_get_timeframe_multiplier(self):
        """Test getting multiplier between timeframes."""
        assert get_timeframe_multiplier("15m", "1h") == 4
        assert get_timeframe_multiplier("1h", "4h") == 4
        assert get_timeframe_multiplier("1h", "1d") == 24
    
    def test_get_timeframe_multiplier_invalid_order(self):
        """Test that lower to higher validation works."""
        with pytest.raises(ValueError, match="not higher than"):
            get_timeframe_multiplier("1h", "15m")
    
    def test_get_timeframe_multiplier_not_clean(self):
        """Test that non-clean multiples raise error."""
        with pytest.raises(ValueError, match="not a clean multiple"):
            get_timeframe_multiplier("15m", "2h")


class TestTimestampAlignment:
    """Tests for timestamp alignment."""
    
    def test_align_timestamp_to_timeframe_hour(self):
        """Test aligning timestamp to hour."""
        # 2023-10-20 14:35:42.123
        ts = 1697813742123
        aligned = align_timestamp_to_timeframe(ts, "1h")
        
        # Should align to 14:00:00.000
        expected = 1697810400000
        assert aligned == expected
    
    def test_align_timestamp_to_timeframe_day(self):
        """Test aligning timestamp to day."""
        # 2023-10-20 14:35:42
        ts = 1697813742000
        aligned = align_timestamp_to_timeframe(ts, "1d")
        
        # Should align to start of day (UTC)
        expected = (ts // 86400000) * 86400000
        assert aligned == expected
    
    def test_align_timestamp_to_timeframe_15m(self):
        """Test aligning timestamp to 15 minutes."""
        # 2023-10-20 14:35:42
        ts = 1697813742000
        aligned = align_timestamp_to_timeframe(ts, "15m")
        
        # Should align to 14:30:00
        expected = (ts // 900000) * 900000
        assert aligned == expected


class TestTimeframeClassification:
    """Tests for timeframe classification."""
    
    def test_is_intraday(self):
        """Test intraday classification."""
        assert is_intraday("1m") is True
        assert is_intraday("15m") is True
        assert is_intraday("1h") is True
        assert is_intraday("4h") is True
        assert is_intraday("1d") is False
        assert is_intraday("1w") is False
    
    def test_is_daily_or_higher(self):
        """Test daily or higher classification."""
        assert is_daily_or_higher("1m") is False
        assert is_daily_or_higher("1h") is False
        assert is_daily_or_higher("1d") is True
        assert is_daily_or_higher("1w") is True


class TestPrimaryTimeframes:
    """Tests for primary timeframes constant."""
    
    def test_primary_timeframes_defined(self):
        """Test that primary timeframes are defined."""
        assert Timeframe.M15 in PRIMARY_TIMEFRAMES
        assert Timeframe.H1 in PRIMARY_TIMEFRAMES
        assert Timeframe.H4 in PRIMARY_TIMEFRAMES
        assert Timeframe.D1 in PRIMARY_TIMEFRAMES
    
    def test_primary_timeframes_count(self):
        """Test primary timeframes count."""
        assert len(PRIMARY_TIMEFRAMES) == 4

