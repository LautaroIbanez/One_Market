"""Comprehensive tests for data module (Epic 1 - Historia 1.4).

Tests cover:
- Schema validation
- Incremental fetch
- Gap detection
- Duplicate handling
- Storage idempotency
- Partition management
"""
import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import shutil
from app.data.schema import OHLCVBar, DatasetMetadata, StoragePartitionKey, FetchRequest, DataValidationResult
from app.data.store import DataStore
from app.config.settings import get_timeframe_ms


class TestOHLCVBarValidation:
    """Test suite for OHLCVBar schema validation."""
    
    def test_valid_bar_creation(self):
        """Test creating a valid OHLCV bar."""
        bar = OHLCVBar(timestamp=1697500000000, open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.5, symbol="BTC/USDT", timeframe="1h")
        
        assert bar.timestamp == 1697500000000
        assert bar.open == 50000.0
        assert bar.high == 51000.0
        assert bar.low == 49000.0
        assert bar.close == 50500.0
        assert bar.volume == 100.5
        assert bar.symbol == "BTC/USDT"
        assert bar.timeframe == "1h"
    
    def test_high_validation(self):
        """Test that high must be >= open, low, close."""
        with pytest.raises(ValueError):
            OHLCVBar(timestamp=1697500000000, open=50000.0, high=48000.0, low=49000.0, close=50500.0, volume=100.5, symbol="BTC/USDT", timeframe="1h")
    
    def test_low_validation(self):
        """Test that low must be <= open, close."""
        with pytest.raises(ValueError):
            OHLCVBar(timestamp=1697500000000, open=50000.0, high=51000.0, low=51000.0, close=50500.0, volume=100.5, symbol="BTC/USDT", timeframe="1h")
    
    def test_timestamp_future_validation(self):
        """Test that future timestamps are rejected."""
        future_ts = int((datetime.utcnow() + timedelta(days=1)).timestamp() * 1000)
        with pytest.raises(ValueError):
            OHLCVBar(timestamp=future_ts, open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.5, symbol="BTC/USDT", timeframe="1h")
    
    def test_timestamp_too_old_validation(self):
        """Test that timestamps before year 2000 are rejected."""
        old_ts = 946684799000
        with pytest.raises(ValueError):
            OHLCVBar(timestamp=old_ts, open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.5, symbol="BTC/USDT", timeframe="1h")
    
    def test_negative_price_validation(self):
        """Test that negative prices are rejected."""
        with pytest.raises(ValueError):
            OHLCVBar(timestamp=1697500000000, open=-50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.5, symbol="BTC/USDT", timeframe="1h")


class TestStoragePartitionKey:
    """Test suite for storage partition keys."""
    
    def test_partition_path_generation(self):
        """Test partition path string generation."""
        key = StoragePartitionKey(symbol="BTC/USDT", timeframe="1h", year=2024, month=10)
        path = key.to_path()
        
        assert path == "symbol=BTC-USDT/tf=1h/year=2024/month=10"
    
    def test_partition_from_timestamp(self):
        """Test creating partition key from timestamp."""
        ts = int(datetime(2024, 10, 15, 12, 0, 0).timestamp() * 1000)
        key = StoragePartitionKey.from_timestamp("BTC/USDT", "1h", ts)
        
        assert key.symbol == "BTC/USDT"
        assert key.timeframe == "1h"
        assert key.year == 2024
        assert key.month == 10


class TestDataStore:
    """Test suite for DataStore parquet operations."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def store(self, temp_storage):
        """Create DataStore instance with temp storage."""
        return DataStore(storage_path=temp_storage)
    
    @pytest.fixture
    def sample_bars(self):
        """Generate sample OHLCV bars."""
        base_ts = int(datetime(2024, 10, 1, 0, 0, 0).timestamp() * 1000)
        timeframe_ms = get_timeframe_ms("1h")
        
        bars = []
        for i in range(100):
            ts = base_ts + (i * timeframe_ms)
            bar = OHLCVBar(timestamp=ts, open=50000.0 + i, high=50100.0 + i, low=49900.0 + i, close=50050.0 + i, volume=100.0 + i, symbol="BTC/USDT", timeframe="1h")
            bars.append(bar)
        
        return bars
    
    def test_write_and_read_bars(self, store, sample_bars):
        """Test writing and reading bars."""
        stats = store.write_bars(sample_bars)
        assert len(stats) > 0
        
        read_bars = store.read_bars("BTC/USDT", "1h")
        assert len(read_bars) == len(sample_bars)
        assert read_bars[0].timestamp == sample_bars[0].timestamp
    
    def test_idempotent_writes(self, store, sample_bars):
        """Test that writing same data twice doesn't duplicate."""
        store.write_bars(sample_bars, mode="append")
        store.write_bars(sample_bars, mode="append")
        
        read_bars = store.read_bars("BTC/USDT", "1h")
        assert len(read_bars) == len(sample_bars)
    
    def test_timestamp_filtering(self, store, sample_bars):
        """Test reading with timestamp filters."""
        store.write_bars(sample_bars)
        
        start_ts = sample_bars[10].timestamp
        end_ts = sample_bars[20].timestamp
        
        filtered = store.read_bars("BTC/USDT", "1h", start_timestamp=start_ts, end_timestamp=end_ts)
        
        assert len(filtered) <= 11
        assert all(start_ts <= b.timestamp <= end_ts for b in filtered)
    
    def test_metadata_creation(self, store, sample_bars):
        """Test metadata is created after writing."""
        store.write_bars(sample_bars)
        
        metadata = store.get_metadata("BTC/USDT", "1h")
        assert metadata is not None
        assert metadata.record_count == len(sample_bars)
        assert metadata.symbol == "BTC/USDT"
        assert metadata.timeframe == "1h"
    
    def test_partition_management(self, store, sample_bars):
        """Test partition creation across months."""
        base_ts_jan = int(datetime(2024, 1, 1, 0, 0, 0).timestamp() * 1000)
        base_ts_feb = int(datetime(2024, 2, 1, 0, 0, 0).timestamp() * 1000)
        timeframe_ms = get_timeframe_ms("1h")
        
        jan_bars = [OHLCVBar(timestamp=base_ts_jan + (i * timeframe_ms), open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0, symbol="BTC/USDT", timeframe="1h") for i in range(10)]
        
        feb_bars = [OHLCVBar(timestamp=base_ts_feb + (i * timeframe_ms), open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0, symbol="BTC/USDT", timeframe="1h") for i in range(10)]
        
        stats = store.write_bars(jan_bars + feb_bars)
        assert len(stats) >= 2
    
    def test_list_stored_symbols(self, store, sample_bars):
        """Test listing stored symbols."""
        store.write_bars(sample_bars)
        
        symbols = store.list_stored_symbols()
        assert ("BTC/USDT", "1h") in symbols
    
    def test_delete_symbol_data(self, store, sample_bars):
        """Test deleting symbol data."""
        store.write_bars(sample_bars)
        assert len(store.read_bars("BTC/USDT", "1h")) > 0
        
        store.delete_symbol_data("BTC/USDT", "1h")
        assert len(store.read_bars("BTC/USDT", "1h")) == 0


class TestGapDetection:
    """Test suite for gap detection in OHLCV data."""
    
    @pytest.fixture
    def bars_with_gaps(self):
        """Generate bars with intentional gaps."""
        base_ts = int(datetime(2024, 10, 1, 0, 0, 0).timestamp() * 1000)
        timeframe_ms = get_timeframe_ms("1h")
        
        bars = []
        for i in range(10):
            ts = base_ts + (i * timeframe_ms)
            bar = OHLCVBar(timestamp=ts, open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0, symbol="BTC/USDT", timeframe="1h")
            bars.append(bar)
        
        for i in range(20, 30):
            ts = base_ts + (i * timeframe_ms)
            bar = OHLCVBar(timestamp=ts, open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0, symbol="BTC/USDT", timeframe="1h")
            bars.append(bar)
        
        return bars
    
    def test_gap_detection(self, bars_with_gaps):
        """Test that gaps are detected correctly."""
        from app.data.fetch import DataFetcher
        fetcher = DataFetcher()
        
        validation = fetcher.validate_data(bars_with_gaps)
        
        assert validation.has_gaps is True
        assert validation.gap_count > 0


class TestDuplicateHandling:
    """Test suite for duplicate timestamp handling."""
    
    def test_duplicate_detection(self):
        """Test duplicate timestamp detection."""
        base_ts = int(datetime(2024, 10, 1, 0, 0, 0).timestamp() * 1000)
        
        bars = [OHLCVBar(timestamp=base_ts, open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0, symbol="BTC/USDT", timeframe="1h"), OHLCVBar(timestamp=base_ts, open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0, symbol="BTC/USDT", timeframe="1h"), OHLCVBar(timestamp=base_ts + get_timeframe_ms("1h"), open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0, symbol="BTC/USDT", timeframe="1h")]
        
        from app.data.fetch import DataFetcher
        fetcher = DataFetcher()
        validation = fetcher.validate_data(bars)
        
        assert validation.has_duplicates is True
        assert validation.duplicate_count == 1


class TestFetchRequest:
    """Test suite for FetchRequest validation."""
    
    def test_valid_fetch_request(self):
        """Test creating valid fetch request."""
        request = FetchRequest(symbol="BTC/USDT", timeframe="1h", since=1697500000000, limit=500)
        
        assert request.symbol == "BTC/USDT"
        assert request.timeframe == "1h"
        assert request.limit == 500
    
    def test_limit_validation(self):
        """Test that limit is constrained."""
        with pytest.raises(ValueError):
            FetchRequest(symbol="BTC/USDT", timeframe="1h", limit=5000)


class TestTimeframeConversion:
    """Test suite for timeframe conversion utilities."""
    
    def test_timeframe_to_milliseconds(self):
        """Test timeframe string to milliseconds conversion."""
        assert get_timeframe_ms("1m") == 60 * 1000
        assert get_timeframe_ms("1h") == 60 * 60 * 1000
        assert get_timeframe_ms("1d") == 24 * 60 * 60 * 1000
    
    def test_invalid_timeframe(self):
        """Test invalid timeframe raises error."""
        with pytest.raises(ValueError):
            get_timeframe_ms("invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


