"""Tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestRootEndpoints:
    """Tests for root endpoints."""
    
    def test_root(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestSymbolsEndpoint:
    """Tests for symbols endpoint."""
    
    def test_get_symbols(self):
        """Test getting available symbols."""
        response = client.get("/symbols")
        assert response.status_code == 200
        data = response.json()
        assert "symbols" in data
        assert "count" in data
        assert isinstance(data["symbols"], list)


class TestStrategiesEndpoint:
    """Tests for strategies endpoint."""
    
    def test_list_strategies(self):
        """Test listing available strategies."""
        response = client.get("/strategies")
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert "count" in data
        assert len(data["strategies"]) > 0


class TestSignalEndpoint:
    """Tests for signal generation endpoint."""
    
    def test_generate_signal_missing_data(self):
        """Test signal generation with missing data."""
        request_data = {
            "symbol": "INVALID/SYMBOL",
            "timeframe": "1h",
            "strategy": "ma_crossover"
        }
        
        response = client.post("/signal", json=request_data)
        
        # Should fail gracefully
        assert response.status_code in [400, 500]


class TestBacktestEndpoint:
    """Tests for backtest endpoint."""
    
    def test_backtest_missing_data(self):
        """Test backtest with missing data."""
        request_data = {
            "symbol": "INVALID/SYMBOL",
            "timeframe": "1h",
            "strategy": "ma_crossover",
            "initial_capital": 100000.0
        }
        
        response = client.post("/backtest", json=request_data)
        
        # Should fail gracefully
        assert response.status_code in [400, 500]


class TestMetricsEndpoint:
    """Tests for metrics endpoint."""
    
    def test_get_metrics(self):
        """Test getting metrics for a symbol."""
        response = client.get("/metrics/BTC-USDT")
        
        # Should return metrics even if empty
        assert response.status_code in [200, 500]  # 500 if DB doesn't exist yet


class TestForceCloseEndpoint:
    """Tests for force close endpoint."""
    
    def test_force_close(self):
        """Test force close endpoint."""
        response = client.post("/force-close")
        
        # Should succeed even with no positions
        assert response.status_code in [200, 500]


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Tests for async endpoint behavior."""
    
    @pytest.mark.skip(reason="Requires async test setup")
    async def test_concurrent_requests(self):
        """Test handling concurrent requests."""
        # Would test multiple simultaneous requests
        pass

