"""Tests for data contract compatibility.

This module tests the compatibility between tf/timeframe aliases
and ensures backward compatibility with existing data structures.
"""
import pytest
from datetime import datetime, timezone
from app.data.schema import OHLCVBar


class TestDataContracts:
    """Test data contract compatibility."""
    
    def test_ohlcv_bar_tf_alias(self):
        """Test that OHLCVBar accepts both tf and timeframe."""
        # Test with tf alias
        bar1 = OHLCVBar(
            timestamp=1704067200000,
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=1000.0,
            symbol="BTC/USDT",
            tf="1h"  # Using tf alias
        )
        
        # Test with timeframe field
        bar2 = OHLCVBar(
            timestamp=1704067200000,
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=1000.0,
            symbol="BTC/USDT",
            timeframe="1h"  # Using timeframe field
        )
        
        # Both should be equivalent
        assert bar1.timeframe == bar2.timeframe
        assert bar1.tf == bar2.tf
        assert bar1.tf == "1h"
        assert bar1.timeframe == "1h"
    
    def test_ohlcv_bar_ts_alias(self):
        """Test that OHLCVBar provides ts alias for timestamp."""
        bar = OHLCVBar(
            timestamp=1704067200000,
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=1000.0,
            symbol="BTC/USDT",
            timeframe="1h"
        )
        
        # Test ts alias
        assert bar.ts == bar.timestamp
        assert bar.ts == 1704067200000
        assert bar.timestamp == 1704067200000
    
    def test_ohlcv_bar_property_access(self):
        """Test that both tf and timeframe properties work."""
        bar = OHLCVBar(
            timestamp=1704067200000,
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=1000.0,
            symbol="BTC/USDT",
            timeframe="4h"
        )
        
        # Test property access
        assert bar.tf == "4h"
        assert bar.timeframe == "4h"
        assert bar.tf == bar.timeframe
        
        # Test ts property
        assert bar.ts == 1704067200000
        assert bar.timestamp == 1704067200000
        assert bar.ts == bar.timestamp
    
    def test_ohlcv_bar_dict_serialization(self):
        """Test that dict serialization includes both tf and timeframe."""
        bar = OHLCVBar(
            timestamp=1704067200000,
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=1000.0,
            symbol="BTC/USDT",
            timeframe="1d"
        )
        
        # Test dict conversion
        bar_dict = bar.dict()
        
        # Should include timeframe
        assert "timeframe" in bar_dict
        assert bar_dict["timeframe"] == "1d"
        
        # Test with by_alias=True
        bar_dict_alias = bar.dict(by_alias=True)
        assert "tf" in bar_dict_alias
        assert bar_dict_alias["tf"] == "1d"
    
    def test_ohlcv_bar_from_dict_with_tf(self):
        """Test creating OHLCVBar from dict with tf field."""
        bar_dict = {
            "timestamp": 1704067200000,
            "open": 50000.0,
            "high": 51000.0,
            "low": 49000.0,
            "close": 50500.0,
            "volume": 1000.0,
            "symbol": "BTC/USDT",
            "tf": "1h",  # Using tf field
            "source": "exchange"
        }
        
        bar = OHLCVBar(**bar_dict)
        
        # Should work with tf field
        assert bar.timeframe == "1h"
        assert bar.tf == "1h"
        assert bar.symbol == "BTC/USDT"
    
    def test_ohlcv_bar_from_dict_with_timeframe(self):
        """Test creating OHLCVBar from dict with timeframe field."""
        bar_dict = {
            "timestamp": 1704067200000,
            "open": 50000.0,
            "high": 51000.0,
            "low": 49000.0,
            "close": 50500.0,
            "volume": 1000.0,
            "symbol": "BTC/USDT",
            "timeframe": "4h",  # Using timeframe field
            "source": "exchange"
        }
        
        bar = OHLCVBar(**bar_dict)
        
        # Should work with timeframe field
        assert bar.timeframe == "4h"
        assert bar.tf == "4h"
        assert bar.symbol == "BTC/USDT"
    
    def test_ohlcv_bar_validation_with_tf(self):
        """Test that validation works with tf field."""
        # This should work without errors
        bar = OHLCVBar(
            timestamp=1704067200000,
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=1000.0,
            symbol="BTC/USDT",
            tf="1h"
        )
        
        assert bar.timeframe == "1h"
        assert bar.tf == "1h"
    
    def test_ohlcv_bar_validation_with_timeframe(self):
        """Test that validation works with timeframe field."""
        # This should work without errors
        bar = OHLCVBar(
            timestamp=1704067200000,
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=1000.0,
            symbol="BTC/USDT",
            timeframe="1h"
        )
        
        assert bar.timeframe == "1h"
        assert bar.tf == "1h"
    
    def test_ohlcv_bar_mixed_fields(self):
        """Test that both tf and timeframe can be used together."""
        # This should work - tf takes precedence due to alias
        bar = OHLCVBar(
            timestamp=1704067200000,
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=1000.0,
            symbol="BTC/USDT",
            tf="1h",
            timeframe="4h"  # This should be ignored in favor of tf
        )
        
        # tf should take precedence
        assert bar.timeframe == "1h"
        assert bar.tf == "1h"
    
    def test_ohlcv_bar_json_serialization(self):
        """Test JSON serialization with both tf and timeframe."""
        bar = OHLCVBar(
            timestamp=1704067200000,
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=1000.0,
            symbol="BTC/USDT",
            timeframe="1h"
        )
        
        # Test JSON serialization
        bar_json = bar.json()
        assert "timeframe" in bar_json
        
        # Test with by_alias=True
        bar_json_alias = bar.json(by_alias=True)
        assert "tf" in bar_json_alias


if __name__ == "__main__":
    pytest.main([__file__])