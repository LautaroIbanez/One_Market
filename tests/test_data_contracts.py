"""Tests for data contracts and validation.

This module tests the core data schemas and validation logic.
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.data.schemas import Bar, SnapshotMeta, DataSyncRequest, DataSyncResponse


class TestBarValidation:
    """Test Bar schema validation."""
    
    def test_valid_bar(self):
        """Test valid bar creation."""
        bar = Bar(
            ts=1640995200000,  # 2022-01-01 00:00:00 UTC
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=100.5,
            tf="1h",
            source="ccxt"
        )
        
        assert bar.ts == 1640995200000
        assert bar.open == 50000.0
        assert bar.high == 51000.0
        assert bar.low == 49000.0
        assert bar.close == 50500.0
        assert bar.volume == 100.5
        assert bar.tf == "1h"
        assert bar.source == "ccxt"
    
    def test_invalid_high_low(self):
        """Test validation of high/low relationship."""
        with pytest.raises(ValidationError) as exc_info:
            Bar(
                ts=1640995200000,
                open=50000.0,
                high=49000.0,  # High < open (invalid)
                low=49000.0,
                close=50500.0,
                volume=100.5,
                tf="1h",
                source="ccxt"
            )
        
        assert "High must be >= max(low, open, close)" in str(exc_info.value)
    
    def test_invalid_low_high(self):
        """Test validation of low/high relationship."""
        with pytest.raises(ValidationError) as exc_info:
            Bar(
                ts=1640995200000,
                open=50000.0,
                high=51000.0,
                low=52000.0,  # Low > high (invalid)
                close=50500.0,
                volume=100.5,
                tf="1h",
                source="ccxt"
            )
        
        assert "Low must be <= min(high, open, close)" in str(exc_info.value)
    
    def test_invalid_timeframe(self):
        """Test validation of timeframe format."""
        with pytest.raises(ValidationError) as exc_info:
            Bar(
                ts=1640995200000,
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=100.5,
                tf="invalid_tf",  # Invalid timeframe
                source="ccxt"
            )
        
        assert "Invalid timeframe" in str(exc_info.value)
    
    def test_negative_prices(self):
        """Test validation of negative prices."""
        with pytest.raises(ValidationError) as exc_info:
            Bar(
                ts=1640995200000,
                open=-50000.0,  # Negative price
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=100.5,
                tf="1h",
                source="ccxt"
            )
        
        assert "ensure this value is greater than 0" in str(exc_info.value)
    
    def test_negative_volume(self):
        """Test validation of negative volume."""
        with pytest.raises(ValidationError) as exc_info:
            Bar(
                ts=1640995200000,
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=-100.5,  # Negative volume
                tf="1h",
                source="ccxt"
            )
        
        assert "ensure this value is greater than or equal to 0" in str(exc_info.value)
    
    def test_to_dict_from_dict(self):
        """Test conversion to/from dictionary."""
        original_bar = Bar(
            ts=1640995200000,
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=100.5,
            tf="1h",
            source="ccxt"
        )
        
        # Convert to dict
        bar_dict = original_bar.to_dict()
        assert bar_dict["timestamp"] == 1640995200000
        assert bar_dict["open"] == 50000.0
        assert bar_dict["high"] == 51000.0
        assert bar_dict["low"] == 49000.0
        assert bar_dict["close"] == 50500.0
        assert bar_dict["volume"] == 100.5
        assert bar_dict["timeframe"] == "1h"
        assert bar_dict["source"] == "ccxt"
        
        # Convert back from dict
        restored_bar = Bar.from_dict(bar_dict)
        assert restored_bar.ts == original_bar.ts
        assert restored_bar.open == original_bar.open
        assert restored_bar.high == original_bar.high
        assert restored_bar.low == original_bar.low
        assert restored_bar.close == original_bar.close
        assert restored_bar.volume == original_bar.volume
        assert restored_bar.tf == original_bar.tf
        assert restored_bar.source == original_bar.source


class TestSnapshotMeta:
    """Test SnapshotMeta schema."""
    
    def test_valid_snapshot_meta(self):
        """Test valid snapshot metadata creation."""
        meta = SnapshotMeta(
            symbol="BTC/USDT",
            tf="1h",
            since=datetime(2022, 1, 1, tzinfo=timezone.utc),
            until=datetime(2022, 1, 2, tzinfo=timezone.utc),
            count=24,
            dataset_hash="a" * 64  # 64-character hex string
        )
        
        assert meta.symbol == "BTC/USDT"
        assert meta.tf == "1h"
        assert meta.count == 24
        assert len(meta.dataset_hash) == 64
    
    def test_invalid_hash_format(self):
        """Test validation of hash format."""
        with pytest.raises(ValidationError) as exc_info:
            SnapshotMeta(
                symbol="BTC/USDT",
                tf="1h",
                since=datetime(2022, 1, 1, tzinfo=timezone.utc),
                until=datetime(2022, 1, 2, tzinfo=timezone.utc),
                count=24,
                dataset_hash="invalid_hash"  # Not 64 characters
            )
        
        assert "dataset_hash must be a 64-character hex string" in str(exc_info.value)
    
    def test_create_from_bars(self):
        """Test creating metadata from bars."""
        bars = [
            Bar(
                ts=1640995200000,  # 2022-01-01 00:00:00 UTC
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=100.5,
                tf="1h",
                source="BTC/USDT"
            ),
            Bar(
                ts=1640998800000,  # 2022-01-01 01:00:00 UTC
                open=50500.0,
                high=51500.0,
                low=49500.0,
                close=51000.0,
                volume=120.0,
                tf="1h",
                source="BTC/USDT"
            )
        ]
        
        meta = SnapshotMeta.create_from_bars("BTC/USDT", "1h", bars)
        
        assert meta.symbol == "BTC/USDT"
        assert meta.tf == "1h"
        assert meta.count == 2
        assert len(meta.dataset_hash) == 64
        assert meta.since == datetime(2022, 1, 1, tzinfo=timezone.utc)
        assert meta.until == datetime(2022, 1, 1, 1, tzinfo=timezone.utc)
    
    def test_create_from_empty_bars(self):
        """Test creating metadata from empty bars list."""
        with pytest.raises(ValueError) as exc_info:
            SnapshotMeta.create_from_bars("BTC/USDT", "1h", [])
        
        assert "Cannot create metadata from empty bars list" in str(exc_info.value)


class TestDataSyncRequest:
    """Test DataSyncRequest schema."""
    
    def test_valid_sync_request(self):
        """Test valid sync request creation."""
        request = DataSyncRequest(
            symbol="BTC/USDT",
            tf="1h",
            since=datetime(2022, 1, 1, tzinfo=timezone.utc),
            until=datetime(2022, 1, 2, tzinfo=timezone.utc),
            force_refresh=True
        )
        
        assert request.symbol == "BTC/USDT"
        assert request.tf == "1h"
        assert request.since == datetime(2022, 1, 1, tzinfo=timezone.utc)
        assert request.until == datetime(2022, 1, 2, tzinfo=timezone.utc)
        assert request.force_refresh is True
    
    def test_minimal_sync_request(self):
        """Test minimal sync request (only required fields)."""
        request = DataSyncRequest(
            symbol="BTC/USDT",
            tf="1h"
        )
        
        assert request.symbol == "BTC/USDT"
        assert request.tf == "1h"
        assert request.since is None
        assert request.until is None
        assert request.force_refresh is False


class TestDataSyncResponse:
    """Test DataSyncResponse schema."""
    
    def test_valid_sync_response(self):
        """Test valid sync response creation."""
        meta = SnapshotMeta(
            symbol="BTC/USDT",
            tf="1h",
            since=datetime(2022, 1, 1, tzinfo=timezone.utc),
            until=datetime(2022, 1, 2, tzinfo=timezone.utc),
            count=24,
            dataset_hash="a" * 64
        )
        
        response = DataSyncResponse(
            success=True,
            symbol="BTC/USDT",
            tf="1h",
            meta=meta,
            message="Sync completed successfully",
            bars_added=24,
            bars_updated=0
        )
        
        assert response.success is True
        assert response.symbol == "BTC/USDT"
        assert response.tf == "1h"
        assert response.meta == meta
        assert response.message == "Sync completed successfully"
        assert response.bars_added == 24
        assert response.bars_updated == 0
    
    def test_error_sync_response(self):
        """Test error sync response creation."""
        response = DataSyncResponse(
            success=False,
            symbol="BTC/USDT",
            tf="1h",
            meta=None,
            message="Sync failed: Connection error",
            bars_added=0,
            bars_updated=0
        )
        
        assert response.success is False
        assert response.symbol == "BTC/USDT"
        assert response.tf == "1h"
        assert response.meta is None
        assert response.message == "Sync failed: Connection error"
        assert response.bars_added == 0
        assert response.bars_updated == 0
