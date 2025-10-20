"""Integration tests for data synchronization system."""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from app.data.last_update import LastUpdateTracker, record_data_update, get_data_summary
from scripts.sync_data import sync_data


class TestDataSync:
    """Test data synchronization and update tracking."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_update_tracker_basic(self):
        """Test basic update tracking functionality."""
        tracker = LastUpdateTracker(storage_path=self.temp_path)
        
        # Record an update
        tracker.record_update(
            symbol="BTC/USDT",
            timeframe="1h",
            bars_count=100,
            latest_timestamp=1234567890000,
            latest_price=50000.0,
            success=True
        )
        
        # Check that it was recorded
        record = tracker.get_last_update("BTC/USDT", "1h")
        assert record is not None
        assert record.symbol == "BTC/USDT"
        assert record.timeframe == "1h"
        assert record.bars_count == 100
        assert record.latest_timestamp == 1234567890000
        assert record.latest_price == 50000.0
        assert record.success is True
    
    def test_update_tracker_freshness(self):
        """Test data freshness checking."""
        tracker = LastUpdateTracker(storage_path=self.temp_path)
        
        # Record recent update
        tracker.record_update(
            symbol="BTC/USDT",
            timeframe="1h",
            bars_count=50,
            success=True
        )
        
        # Should be fresh (within 24 hours)
        assert tracker.is_data_fresh("BTC/USDT", "1h", max_age_hours=24) is True
        
        # Record old update (manually set old timestamp)
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        record = tracker.get_last_update("BTC/USDT", "1h")
        record.last_update = old_time
        tracker._updates["BTC/USDT_1h"] = record
        tracker._save_updates()
        
        # Should be stale
        assert tracker.is_data_fresh("BTC/USDT", "1h", max_age_hours=24) is False
    
    def test_update_tracker_stale_data(self):
        """Test getting stale data records."""
        tracker = LastUpdateTracker(storage_path=self.temp_path)
        
        # Add multiple records
        tracker.record_update("BTC/USDT", "1h", bars_count=100, success=True)
        tracker.record_update("ETH/USDT", "1h", bars_count=50, success=True)
        tracker.record_update("BTC/USDT", "4h", bars_count=25, success=True)
        
        # Make one stale
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        record = tracker.get_last_update("BTC/USDT", "1h")
        record.last_update = old_time
        tracker._updates["BTC/USDT_1h"] = record
        tracker._save_updates()
        
        # Get stale data
        stale = tracker.get_stale_data(max_age_hours=24)
        assert len(stale) == 1
        assert "BTC/USDT_1h" in stale
    
    def test_update_tracker_summary(self):
        """Test data summary generation."""
        tracker = LastUpdateTracker(storage_path=self.temp_path)
        
        # Add various records
        tracker.record_update("BTC/USDT", "1h", bars_count=100, success=True)
        tracker.record_update("ETH/USDT", "1h", bars_count=50, success=True)
        tracker.record_update("BTC/USDT", "4h", bars_count=25, success=False, error="API error")
        
        summary = tracker.get_data_summary()
        
        assert summary['total_records'] == 3
        assert summary['successful_records'] == 2
        assert summary['failed_records'] == 1
        assert summary['fresh_data'] >= 0  # Depends on timing
        assert summary['last_update_overall'] is not None
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Use temporary directory for testing
        with patch('app.data.last_update.settings') as mock_settings:
            mock_settings.STORAGE_PATH = self.temp_path
            
            # Record update using convenience function
            record_data_update(
                symbol="BTC/USDT",
                timeframe="1h",
                bars_count=100,
                latest_timestamp=1234567890000,
                latest_price=50000.0,
                success=True
            )
            
            # Check summary
            summary = get_data_summary()
            assert summary['total_records'] >= 1
    
    @patch('scripts.sync_data.DataFetcher')
    @patch('scripts.sync_data.DataStore')
    def test_sync_data_integration(self, mock_store, mock_fetcher):
        """Test sync_data function integration."""
        # Mock data fetcher
        mock_bar = Mock()
        mock_bar.timestamp = 1234567890000
        mock_bar.close = 50000.0
        
        mock_fetcher_instance = mock_fetcher.return_value
        mock_fetcher_instance.fetch_incremental.return_value = [mock_bar]
        
        # Mock data store
        mock_store_instance = mock_store.return_value
        
        # Test sync
        result = sync_data(
            symbol="BTC/USDT",
            timeframe="1h",
            days_back=7,
            dry_run=False,
            verbose=False
        )
        
        # Verify result
        assert result['symbol'] == "BTC/USDT"
        assert result['timeframe'] == "1h"
        assert result['success'] is True
        assert result['bars_fetched'] == 1
        assert result['bars_stored'] == 1
        assert result['latest_timestamp'] == 1234567890000
        assert result['latest_price'] == 50000.0
        
        # Verify store was called
        mock_store_instance.write_bars.assert_called_once_with([mock_bar])
    
    @patch('scripts.sync_data.DataFetcher')
    def test_sync_data_error_handling(self, mock_fetcher):
        """Test sync_data error handling."""
        # Mock fetcher to raise exception
        mock_fetcher_instance = mock_fetcher.return_value
        mock_fetcher_instance.fetch_incremental.side_effect = Exception("API Error")
        
        # Test sync with error
        result = sync_data(
            symbol="BTC/USDT",
            timeframe="1h",
            days_back=7,
            dry_run=False,
            verbose=False
        )
        
        # Verify error handling
        assert result['symbol'] == "BTC/USDT"
        assert result['timeframe'] == "1h"
        assert result['success'] is False
        assert result['error'] == "API Error"
        assert result['bars_fetched'] == 0
        assert result['bars_stored'] == 0
    
    def test_sync_data_dry_run(self):
        """Test sync_data dry run mode."""
        with patch('scripts.sync_data.DataFetcher') as mock_fetcher:
            # Mock data
            mock_bar = Mock()
            mock_bar.timestamp = 1234567890000
            mock_bar.close = 50000.0
            
            mock_fetcher_instance = mock_fetcher.return_value
            mock_fetcher_instance.fetch_incremental.return_value = [mock_bar]
            
            # Test dry run
            result = sync_data(
                symbol="BTC/USDT",
                timeframe="1h",
                days_back=7,
                dry_run=True,
                verbose=False
            )
            
            # Verify dry run behavior
            assert result['success'] is True
            assert result['bars_fetched'] == 1
            assert result['bars_stored'] == 0  # Should not store in dry run


if __name__ == "__main__":
    pytest.main([__file__])

