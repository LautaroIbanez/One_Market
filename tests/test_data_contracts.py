"""Tests for data contracts and validation.

This module tests the Pydantic schemas and data validation logic.
"""
import pytest
from datetime import datetime, timezone
from app.data.schemas import Bar, SnapshotMeta, DataIntegrityCheck


class TestBarSchema:
    """Test Bar schema validation."""
    
    def test_valid_bar_creation(self):
        """Test creating valid bar."""
        bar = Bar(
            ts=1678886400000,
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000.0,
            tf="1h",
            source="binance"
        )
        assert bar.open == 100.0
        assert bar.high == 105.0
        assert bar.low == 98.0
        assert bar.close == 103.0
        assert bar.volume == 1000.0
    
    def test_invalid_high_price(self):
        """Test invalid high price."""
        with pytest.raises(ValueError, match="High must be >= max"):
            Bar(
                ts=1678886400000,
                open=100.0,
                high=95.0,  # High < open
                low=98.0,
                close=103.0,
                volume=1000.0,
                tf="1h",
                source="binance"
            )
    
    def test_invalid_low_price(self):
        """Test invalid low price."""
        with pytest.raises(ValueError, match="Low must be <= min"):
            Bar(
                ts=1678886400000,
                open=100.0,
                high=105.0,
                low=110.0,  # Low > high
                close=103.0,
                volume=1000.0,
                tf="1h",
                source="binance"
            )
    
    def test_invalid_open_price(self):
        """Test invalid open price."""
        with pytest.raises(ValueError, match="Open must be within"):
            Bar(
                ts=1678886400000,
                open=110.0,  # Open > high
                high=105.0,
                low=98.0,
                close=103.0,
                volume=1000.0,
                tf="1h",
                source="binance"
            )
    
    def test_invalid_close_price(self):
        """Test invalid close price."""
        with pytest.raises(ValueError, match="Close must be within"):
            Bar(
                ts=1678886400000,
                open=100.0,
                high=105.0,
                low=98.0,
                close=90.0,  # Close < low
                volume=1000.0,
                tf="1h",
                source="binance"
            )
    
    def test_invalid_timeframe(self):
        """Test invalid timeframe."""
        with pytest.raises(ValueError, match="Invalid timeframe"):
            Bar(
                ts=1678886400000,
                open=100.0,
                high=105.0,
                low=98.0,
                close=103.0,
                volume=1000.0,
                tf="invalid",  # Invalid timeframe
                source="binance"
            )
    
    def test_negative_prices(self):
        """Test negative prices."""
        with pytest.raises(ValueError, match="value is not greater than 0"):
            Bar(
                ts=1678886400000,
                open=-100.0,  # Negative price
                high=105.0,
                low=98.0,
                close=103.0,
                volume=1000.0,
                tf="1h",
                source="binance"
            )
    
    def test_negative_volume(self):
        """Test negative volume."""
        with pytest.raises(ValueError, match="value is not greater than or equal to 0"):
            Bar(
                ts=1678886400000,
                open=100.0,
                high=105.0,
                low=98.0,
                close=103.0,
                volume=-1000.0,  # Negative volume
                tf="1h",
                source="binance"
            )
    
    def test_to_dict_conversion(self):
        """Test to_dict conversion."""
        bar = Bar(
            ts=1678886400000,
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000.0,
            tf="1h",
            source="binance"
        )
        
        bar_dict = bar.to_dict()
        assert bar_dict['timestamp'] == 1678886400000
        assert bar_dict['open'] == 100.0
        assert bar_dict['high'] == 105.0
        assert bar_dict['low'] == 98.0
        assert bar_dict['close'] == 103.0
        assert bar_dict['volume'] == 1000.0
        assert bar_dict['timeframe'] == "1h"
        assert bar_dict['source'] == "binance"
    
    def test_from_dict_conversion(self):
        """Test from_dict conversion."""
        bar_dict = {
            'timestamp': 1678886400000,
            'open': 100.0,
            'high': 105.0,
            'low': 98.0,
            'close': 103.0,
            'volume': 1000.0,
            'timeframe': '1h',
            'source': 'binance'
        }
        
        bar = Bar.from_dict(bar_dict)
        assert bar.ts == 1678886400000
        assert bar.open == 100.0
        assert bar.high == 105.0
        assert bar.low == 98.0
        assert bar.close == 103.0
        assert bar.volume == 1000.0
        assert bar.tf == "1h"
        assert bar.source == "binance"


class TestSnapshotMetaSchema:
    """Test SnapshotMeta schema validation."""
    
    def test_create_from_bars(self):
        """Test creating metadata from bars."""
        bars = [
            Bar(ts=1678886400000, open=100.0, high=105.0, low=98.0, close=103.0, volume=1000.0, tf="1h", source="binance"),
            Bar(ts=1678890000000, open=103.0, high=108.0, low=101.0, close=106.0, volume=1200.0, tf="1h", source="binance")
        ]
        
        meta = SnapshotMeta.create_from_bars("BTC/USDT", "1h", bars)
        
        assert meta.symbol == "BTC/USDT"
        assert meta.tf == "1h"
        assert meta.count == 2
        assert meta.dataset_hash is not None
        assert len(meta.dataset_hash) == 64  # SHA256 hash length
    
    def test_create_from_empty_bars(self):
        """Test creating metadata from empty bars list."""
        with pytest.raises(ValueError, match="Cannot create metadata from empty bars list"):
            SnapshotMeta.create_from_bars("BTC/USDT", "1h", [])
    
    def test_invalid_hash_format(self):
        """Test invalid hash format."""
        with pytest.raises(ValueError, match="dataset_hash must be a 64-character hex string"):
            SnapshotMeta(
                symbol="BTC/USDT",
                tf="1h",
                since=datetime.now(timezone.utc),
                until=datetime.now(timezone.utc),
                count=1,
                dataset_hash="invalid_hash"  # Not 64 characters
            )


class TestDataIntegrityCheck:
    """Test DataIntegrityCheck schema."""
    
    def test_valid_integrity_check(self):
        """Test valid integrity check."""
        check = DataIntegrityCheck(
            symbol="BTC/USDT",
            tf="1h",
            is_valid=True,
            issues=[],
            gaps=[],
            duplicates=[],
            out_of_order=[],
            total_bars=100,
            time_range={"start": 1678886400000, "end": 1678890000000}
        )
        
        assert check.symbol == "BTC/USDT"
        assert check.tf == "1h"
        assert check.is_valid is True
        assert len(check.issues) == 0
        assert check.total_bars == 100
    
    def test_invalid_integrity_check(self):
        """Test invalid integrity check."""
        check = DataIntegrityCheck(
            symbol="BTC/USDT",
            tf="1h",
            is_valid=False,
            issues=["Duplicate timestamps found", "Gaps in data"],
            gaps=[{"index": 10, "expected": 1678890000000, "actual": 1678893600000}],
            duplicates=[{"ts": 1678890000000, "bar": {}}],
            out_of_order=[{"index": 5, "ts": 1678886400000, "prev_ts": 1678890000000}],
            total_bars=100,
            time_range={"start": 1678886400000, "end": 1678890000000}
        )
        
        assert check.is_valid is False
        assert len(check.issues) == 2
        assert len(check.gaps) == 1
        assert len(check.duplicates) == 1
        assert len(check.out_of_order) == 1