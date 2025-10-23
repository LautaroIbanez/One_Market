"""Tests for automatic data refresh functionality.

This module tests the automatic data refresh mechanism when stale data
is detected in the recommendation service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from app.service.daily_recommendation import DailyRecommendationService
from app.service.recommendation_contract import Recommendation, PlanDirection
from app.data.schema import OHLCVBar


class TestDataRefresh:
    """Test automatic data refresh functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = DailyRecommendationService()
        self.symbol = "BTC/USDT"
        self.date = "2024-01-01"
        self.timeframes = ["1h", "4h", "1d"]
        
        # Mock store
        self.mock_store = Mock()
        self.service.store = self.mock_store
    
    def test_refresh_timeframe_data_success(self):
        """Test successful data refresh for a timeframe."""
        # Mock successful sync result
        mock_sync_result = {
            "success": True,
            "bars_added": 10,
            "message": "Successfully synced BTC/USDT 1h"
        }
        
        with patch('app.service.daily_recommendation.DataFetcher') as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.sync_symbol_timeframe.return_value = mock_sync_result
            mock_fetcher_class.return_value = mock_fetcher
            
            # Test refresh
            result = self.service._refresh_timeframe_data(
                self.symbol, "1h", 1704067200000  # Mock timestamp
            )
            
            # Verify result
            assert result["success"] is True
            assert result["bars_added"] == 10
            assert result["timeframe"] == "1h"
            assert result["symbol"] == self.symbol
            assert "Refreshed BTC/USDT 1h with 10 new bars" in result["message"]
            
            # Verify fetcher was called with correct parameters
            mock_fetcher.sync_symbol_timeframe.assert_called_once_with(
                self.symbol, "1h", force_refresh=True
            )
    
    def test_refresh_timeframe_data_failure(self):
        """Test data refresh failure handling."""
        # Mock failed sync result
        mock_sync_result = {
            "success": False,
            "bars_added": 0,
            "message": "Network error"
        }
        
        with patch('app.service.daily_recommendation.DataFetcher') as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.sync_symbol_timeframe.return_value = mock_sync_result
            mock_fetcher_class.return_value = mock_fetcher
            
            # Test refresh
            result = self.service._refresh_timeframe_data(
                self.symbol, "1h", 1704067200000
            )
            
            # Verify result
            assert result["success"] is False
            assert result["bars_added"] == 0
            assert result["error"] == "Network error"
            assert "Failed to refresh BTC/USDT 1h: Network error" in result["message"]
    
    def test_refresh_timeframe_data_exception(self):
        """Test data refresh exception handling."""
        with patch('app.service.daily_recommendation.DataFetcher') as mock_fetcher_class:
            mock_fetcher_class.side_effect = Exception("Fetcher initialization failed")
            
            # Test refresh
            result = self.service._refresh_timeframe_data(
                self.symbol, "1h", 1704067200000
            )
            
            # Verify result
            assert result["success"] is False
            assert result["bars_added"] == 0
            assert "Fetcher initialization failed" in result["error"]
    
    def test_signal_based_recommendation_with_stale_data_refresh(self):
        """Test that stale data triggers automatic refresh."""
        # Mock stale data scenario
        stale_bars = [
            OHLCVBar(
                timestamp=1704067200000,  # Old timestamp (2+ hours ago)
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=1000.0,
                symbol="BTC/USDT",
                timeframe="1h"
            )
        ]
        
        # Mock fresh data after refresh
        fresh_bars = [
            OHLCVBar(
                timestamp=1704067200000,
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=1000.0,
                symbol="BTC/USDT",
                timeframe="1h"
            ),
            OHLCVBar(
                timestamp=int((datetime.now(timezone.utc) - timedelta(minutes=30)).timestamp() * 1000),  # Recent
                open=50500.0,
                high=51500.0,
                low=50000.0,
                close=51000.0,
                volume=1200.0,
                symbol="BTC/USDT",
                timeframe="1h"
            )
        ]
        
        # Mock store responses
        self.mock_store.read_bars.side_effect = [stale_bars, fresh_bars]
        
        # Mock successful refresh
        mock_refresh_result = {
            "success": True,
            "bars_added": 5,
            "message": "Successfully refreshed"
        }
        
        with patch.object(self.service, '_refresh_timeframe_data', return_value=mock_refresh_result):
            with patch.object(self.service, '_get_current_price', return_value=51000.0):
                # Generate recommendation
                recommendation = self.service._get_signal_based_recommendation(
                    self.symbol, self.date, self.timeframes
                )
                
                # Verify recommendation was generated (not HOLD due to stale data)
                assert recommendation is not None
                assert recommendation.symbol == self.symbol
                assert recommendation.date == self.date
                # Should not be HOLD due to data freshness issues
                assert "Data freshness issues" not in recommendation.rationale
    
    def test_signal_based_recommendation_stale_data_after_refresh_failure(self):
        """Test HOLD recommendation when refresh fails."""
        # Mock stale data
        stale_bars = [
            OHLCVBar(
                timestamp=1704067200000,  # Old timestamp
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=1000.0,
                symbol="BTC/USDT",
                timeframe="1h"
            )
        ]
        
        self.mock_store.read_bars.return_value = stale_bars
        
        # Mock failed refresh
        mock_refresh_result = {
            "success": False,
            "bars_added": 0,
            "error": "Network timeout"
        }
        
        with patch.object(self.service, '_refresh_timeframe_data', return_value=mock_refresh_result):
            # Generate recommendation
            recommendation = self.service._get_signal_based_recommendation(
                self.symbol, self.date, self.timeframes
            )
            
            # Verify HOLD recommendation due to refresh failure
            assert recommendation is not None
            assert recommendation.direction == PlanDirection.HOLD
            assert "Data still stale after refresh attempt" in recommendation.rationale
            assert "Network timeout" in recommendation.rationale
    
    def test_validate_data_freshness_with_stale_data(self):
        """Test data freshness validation with stale data."""
        # Mock stale data (3 hours old)
        stale_timestamp = int((datetime.now(timezone.utc) - timedelta(hours=3)).timestamp() * 1000)
        stale_bars = [
            OHLCVBar(
                timestamp=stale_timestamp,
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=1000.0,
                symbol="BTC/USDT",
                timeframe="1h"
            )
        ]
        
        self.mock_store.read_bars.return_value = stale_bars
        
        # Test freshness validation
        freshness_result = self.service._validate_data_freshness(
            self.symbol, self.date, ["1h"]
        )
        
        # Verify stale data detection
        assert freshness_result["is_fresh"] is False
        assert freshness_result["overall_status"] in ["stale", "stale_with_warnings"]
        assert len(freshness_result["warnings"]) > 0
        assert "1h" in freshness_result["timeframe_status"]
        
        tf_status = freshness_result["timeframe_status"]["1h"]
        assert tf_status["status"] == "stale"
        assert tf_status["is_fresh"] is False
        assert tf_status["hours_old"] > 2  # Should be > 2 hours old
    
    def test_validate_data_freshness_with_fresh_data(self):
        """Test data freshness validation with fresh data."""
        # Mock fresh data (30 minutes old)
        fresh_timestamp = int((datetime.now(timezone.utc) - timedelta(minutes=30)).timestamp() * 1000)
        fresh_bars = [
            OHLCVBar(
                timestamp=fresh_timestamp,
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=1000.0,
                symbol="BTC/USDT",
                timeframe="1h"
            )
        ]
        
        self.mock_store.read_bars.return_value = fresh_bars
        
        # Test freshness validation
        freshness_result = self.service._validate_data_freshness(
            self.symbol, self.date, ["1h"]
        )
        
        # Verify fresh data detection
        assert freshness_result["is_fresh"] is True
        assert freshness_result["overall_status"] == "fresh"
        assert len(freshness_result["warnings"]) == 0
        assert "1h" in freshness_result["timeframe_status"]
        
        tf_status = freshness_result["timeframe_status"]["1h"]
        assert tf_status["status"] == "fresh"
        assert tf_status["is_fresh"] is True
        assert tf_status["hours_old"] < 2  # Should be < 2 hours old
    
    def test_validate_data_freshness_no_data(self):
        """Test data freshness validation with no data."""
        # Mock no data
        self.mock_store.read_bars.return_value = []
        
        # Test freshness validation
        freshness_result = self.service._validate_data_freshness(
            self.symbol, self.date, ["1h"]
        )
        
        # Verify no data detection
        assert freshness_result["is_fresh"] is False
        assert freshness_result["overall_status"] in ["stale", "stale_with_warnings"]
        # No data should generate warnings
        assert len(freshness_result["warnings"]) >= 0
        assert "1h" in freshness_result["timeframe_status"]
        
        tf_status = freshness_result["timeframe_status"]["1h"]
        assert tf_status["status"] == "no_data"
        assert tf_status["is_fresh"] is False


class TestDataRefreshIntegration:
    """Integration tests for data refresh with API endpoint."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.symbol = "BTC/USDT"
        self.date = "2024-01-01"
    
    def test_api_endpoint_with_data_refresh(self):
        """Test API endpoint response includes data refresh information."""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Mock the recommendation service to simulate stale data scenario
        with patch('app.api.routes.recommendation.DailyRecommendationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock recommendation with stale data
            mock_recommendation = Mock()
            mock_recommendation.direction = "LONG"
            mock_recommendation.rationale = "Based on fresh data after refresh"
            mock_recommendation.model_dump.return_value = {
                "direction": "LONG",
                "rationale": "Based on fresh data after refresh"
            }
            
            mock_service.get_daily_recommendation.return_value = mock_recommendation
            
            # Mock freshness check that indicates stale data was refreshed
            mock_freshness = {
                "is_fresh": True,
                "overall_status": "fresh",
                "warnings": [],
                "timeframe_status": {
                    "1h": {"status": "fresh", "is_fresh": True}
                }
            }
            mock_service._validate_data_freshness.return_value = mock_freshness
            
            # Make API request
            response = client.get(
                "/recommendation/daily",
                params={
                    "symbol": self.symbol,
                    "date": self.date,
                    "include_freshness": True
                }
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            # Check that data refresh information is included
            assert "data_refresh" in data
            assert "data_freshness" in data
            
            refresh_info = data["data_refresh"]
            assert "refresh_attempted" in refresh_info
            assert "final_status" in refresh_info
            assert "message" in refresh_info


if __name__ == "__main__":
    pytest.main([__file__])
