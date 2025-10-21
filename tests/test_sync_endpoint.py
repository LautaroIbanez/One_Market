"""Tests for data sync endpoint.

This module tests the /data/sync API endpoint functionality.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.routes.data import router
from app.data.schemas import DataSyncRequest, DataSyncResponse, SnapshotMeta


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestDataSyncEndpoint:
    """Test data sync endpoint functionality."""
    
    @patch('app.api.routes.data.get_data_fetcher')
    @patch('app.api.routes.data.get_data_store')
    def test_sync_success(self, mock_get_store, mock_get_fetcher):
        """Test successful data sync."""
        # Mock fetcher
        mock_fetcher = Mock()
        mock_fetcher.validate_symbol.return_value = True
        mock_fetcher.get_supported_timeframes.return_value = ["1m", "5m", "1h", "1d"]
        mock_fetcher.sync_symbol_timeframe.return_value = {
            "success": True,
            "message": "Sync completed successfully",
            "bars_added": 100,
            "meta": SnapshotMeta(
                symbol="BTC/USDT",
                tf="1h",
                since=datetime(2022, 1, 1, tzinfo=timezone.utc),
                until=datetime(2022, 1, 2, tzinfo=timezone.utc),
                count=100,
                dataset_hash="a" * 64
            )
        }
        mock_get_fetcher.return_value = mock_fetcher
        
        # Mock store
        mock_store = Mock()
        mock_get_store.return_value = mock_store
        
        # Test request
        request_data = {
            "symbol": "BTC/USDT",
            "tf": "1h",
            "since": "2022-01-01T00:00:00Z",
            "until": "2022-01-02T00:00:00Z",
            "force_refresh": False
        }
        
        response = client.post("/data/sync", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["symbol"] == "BTC/USDT"
        assert data["tf"] == "1h"
        assert data["bars_added"] == 100
        assert data["message"] == "Sync completed successfully"
    
    @patch('app.api.routes.data.get_data_fetcher')
    def test_sync_invalid_symbol(self, mock_get_fetcher):
        """Test sync with invalid symbol."""
        # Mock fetcher
        mock_fetcher = Mock()
        mock_fetcher.validate_symbol.return_value = False
        mock_get_fetcher.return_value = mock_fetcher
        
        # Test request
        request_data = {
            "symbol": "INVALID/SYMBOL",
            "tf": "1h"
        }
        
        response = client.post("/data/sync", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "not supported by exchange" in data["detail"]
    
    @patch('app.api.routes.data.get_data_fetcher')
    def test_sync_invalid_timeframe(self, mock_get_fetcher):
        """Test sync with invalid timeframe."""
        # Mock fetcher
        mock_fetcher = Mock()
        mock_fetcher.validate_symbol.return_value = True
        mock_fetcher.get_supported_timeframes.return_value = ["1m", "5m", "1h", "1d"]
        mock_get_fetcher.return_value = mock_fetcher
        
        # Test request
        request_data = {
            "symbol": "BTC/USDT",
            "tf": "invalid_tf"
        }
        
        response = client.post("/data/sync", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "not supported" in data["detail"]
    
    @patch('app.api.routes.data.get_data_fetcher')
    def test_sync_failure(self, mock_get_fetcher):
        """Test sync failure handling."""
        # Mock fetcher
        mock_fetcher = Mock()
        mock_fetcher.validate_symbol.return_value = True
        mock_fetcher.get_supported_timeframes.return_value = ["1m", "5m", "1h", "1d"]
        mock_fetcher.sync_symbol_timeframe.return_value = {
            "success": False,
            "message": "Connection timeout",
            "bars_added": 0,
            "meta": None
        }
        mock_get_fetcher.return_value = mock_fetcher
        
        # Test request
        request_data = {
            "symbol": "BTC/USDT",
            "tf": "1h"
        }
        
        response = client.post("/data/sync", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Connection timeout" in data["detail"]
    
    @patch('app.api.routes.data.get_data_fetcher')
    def test_sync_exception(self, mock_get_fetcher):
        """Test sync exception handling."""
        # Mock fetcher to raise exception
        mock_fetcher = Mock()
        mock_fetcher.validate_symbol.side_effect = Exception("Database connection failed")
        mock_get_fetcher.return_value = mock_fetcher
        
        # Test request
        request_data = {
            "symbol": "BTC/USDT",
            "tf": "1h"
        }
        
        response = client.post("/data/sync", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Internal error" in data["detail"]
        assert "Database connection failed" in data["detail"]


class TestDataMetadataEndpoint:
    """Test data metadata endpoint."""
    
    @patch('app.api.routes.data.get_data_store')
    def test_get_metadata_success(self, mock_get_store):
        """Test successful metadata retrieval."""
        # Mock store
        mock_store = Mock()
        mock_meta = SnapshotMeta(
            symbol="BTC/USDT",
            tf="1h",
            since=datetime(2022, 1, 1, tzinfo=timezone.utc),
            until=datetime(2022, 1, 2, tzinfo=timezone.utc),
            count=100,
            dataset_hash="a" * 64
        )
        mock_store.snapshot_meta.return_value = mock_meta
        mock_get_store.return_value = mock_store
        
        response = client.get("/data/meta/BTC%2FUSDT/1h")
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTC/USDT"
        assert data["tf"] == "1h"
        assert data["count"] == 100
    
    @patch('app.api.routes.data.get_data_store')
    def test_get_metadata_not_found(self, mock_get_store):
        """Test metadata retrieval when no data exists."""
        # Mock store
        mock_store = Mock()
        mock_store.snapshot_meta.return_value = None
        mock_get_store.return_value = mock_store
        
        response = client.get("/data/meta/BTC%2FUSDT/1h")
        
        assert response.status_code == 200
        assert response.json() is None


class TestDataLatestEndpoint:
    """Test latest timestamp endpoint."""
    
    @patch('app.api.routes.data.get_data_store')
    def test_get_latest_timestamp_success(self, mock_get_store):
        """Test successful latest timestamp retrieval."""
        # Mock store
        mock_store = Mock()
        mock_store.latest_ts.return_value = 1640995200000  # 2022-01-01 00:00:00 UTC
        mock_get_store.return_value = mock_store
        
        response = client.get("/data/latest/BTC%2FUSDT/1h")
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTC/USDT"
        assert data["timeframe"] == "1h"
        assert data["latest_timestamp"] == 1640995200000
        assert data["has_data"] is True
        assert "latest_datetime" in data
    
    @patch('app.api.routes.data.get_data_store')
    def test_get_latest_timestamp_no_data(self, mock_get_store):
        """Test latest timestamp when no data exists."""
        # Mock store
        mock_store = Mock()
        mock_store.latest_ts.return_value = None
        mock_get_store.return_value = mock_store
        
        response = client.get("/data/latest/BTC%2FUSDT/1h")
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTC/USDT"
        assert data["timeframe"] == "1h"
        assert data["latest_timestamp"] is None
        assert data["has_data"] is False


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    @patch('app.api.routes.data.get_data_fetcher')
    @patch('app.api.routes.data.get_data_store')
    def test_health_check_success(self, mock_get_store, mock_get_fetcher):
        """Test successful health check."""
        # Mock fetcher
        mock_fetcher = Mock()
        mock_fetcher.get_exchange_info.return_value = {
            "name": "binance",
            "id": "binance",
            "rateLimit": 1200
        }
        mock_get_fetcher.return_value = mock_fetcher
        
        # Mock store
        mock_store = Mock()
        mock_store.base_path = "/test/path"
        mock_store.db_path = "/test/path/metadata.db"
        mock_get_store.return_value = mock_store
        
        response = client.get("/data/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "exchange" in data
        assert "data_store" in data
    
    @patch('app.api.routes.data.get_data_fetcher')
    def test_health_check_error(self, mock_get_fetcher):
        """Test health check with error."""
        # Mock fetcher to raise exception
        mock_fetcher = Mock()
        mock_fetcher.get_exchange_info.side_effect = Exception("Connection failed")
        mock_get_fetcher.return_value = mock_fetcher
        
        response = client.get("/data/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Connection failed" in data["error"]
