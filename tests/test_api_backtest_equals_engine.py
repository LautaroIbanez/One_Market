"""Tests to ensure API backtest equals engine results.

This module tests that the API backtest endpoint produces the same
results as the direct engine usage, within tolerance.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import pandas as pd
import numpy as np

from app.api.routes.backtest import router
from app.research.backtest.engine import BacktestEngine, BacktestConfig, BacktestResult
from app.data.schemas import Bar

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestAPIBacktestEqualsEngine:
    """Test that API backtest equals engine results."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start='2022-01-01', end='2022-01-31', freq='1H')
        np.random.seed(42)  # For reproducible results
        
        # Generate realistic price data
        base_price = 50000
        returns = np.random.normal(0, 0.02, len(dates))
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLCV data
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            # Add some noise for OHLC
            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'timestamp': int(date.timestamp() * 1000),
                'open': price,
                'high': high,
                'low': low,
                'close': price,
                'volume': volume,
                'timeframe': '1h',
                'source': 'test'
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def mock_data_store(self, sample_data):
        """Mock data store with sample data."""
        mock_store = Mock()
        
        # Convert DataFrame to Bar objects
        bars = []
        for _, row in sample_data.iterrows():
            bars.append(Bar(
                ts=row['timestamp'],
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                tf=row['timeframe'],
                source=row['source']
            ))
        
        mock_store.read_bars.return_value = bars
        return mock_store
    
    @patch('app.api.routes.backtest.get_data_store')
    @patch('app.api.routes.backtest.generate_signal')
    def test_api_backtest_equals_engine_direct(self, mock_generate_signal, mock_get_store, sample_data, mock_data_store):
        """Test that API backtest produces same results as direct engine usage."""
        # Setup mocks
        mock_get_store.return_value = mock_data_store
        
        # Mock signal generation
        mock_signal = Mock()
        mock_signal.signal = pd.Series([1, -1, 1, -1, 1] * (len(sample_data) // 5 + 1))[:len(sample_data)]
        mock_generate_signal.return_value = mock_signal
        
        # API request
        request_data = {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "strategy": "ma_crossover",
            "from_date": "2022-01-01T00:00:00Z",
            "to_date": "2022-01-31T23:59:59Z",
            "initial_capital": 10000.0,
            "risk_per_trade": 0.02,
            "commission": 0.001,
            "slippage": 0.0005,
            "use_trading_windows": True,
            "force_close": True,
            "one_trade_per_day": True,
            "atr_sl_multiplier": 2.0,
            "atr_tp_multiplier": 3.0,
            "atr_period": 14
        }
        
        # Call API
        response = client.post("/backtest/run", json=request_data)
        
        assert response.status_code == 200
        api_result = response.json()
        
        # Now run direct engine
        config = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,
            force_close=True,
            one_trade_per_day=True,
            atr_sl_multiplier=2.0,
            atr_tp_multiplier=3.0,
            atr_period=14
        )
        
        engine = BacktestEngine(config)
        direct_result = engine.run(sample_data, mock_signal.signal, "ma_crossover", verbose=False)
        
        # Compare results within tolerance
        tolerance = 0.01  # 1% tolerance for floating point differences
        
        assert abs(api_result['total_return'] - direct_result.total_return) < tolerance
        assert abs(api_result['cagr'] - direct_result.cagr) < tolerance
        assert abs(api_result['sharpe_ratio'] - direct_result.sharpe_ratio) < tolerance
        assert abs(api_result['max_drawdown'] - direct_result.max_drawdown) < tolerance
        assert abs(api_result['win_rate'] - direct_result.win_rate) < tolerance
        assert abs(api_result['profit_factor'] - direct_result.profit_factor) < tolerance
        assert abs(api_result['expectancy'] - direct_result.expectancy) < tolerance
        
        # Trade counts should be identical
        assert api_result['total_trades'] == direct_result.total_trades
        assert api_result['winning_trades'] == direct_result.winning_trades
        assert api_result['losing_trades'] == direct_result.losing_trades
    
    @patch('app.api.routes.backtest.get_data_store')
    def test_api_backtest_no_data_error(self, mock_get_store):
        """Test API error handling when no data is available."""
        # Mock empty data
        mock_store = Mock()
        mock_store.read_bars.return_value = []
        mock_get_store.return_value = mock_store
        
        request_data = {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "strategy": "ma_crossover"
        }
        
        response = client.post("/backtest/run", json=request_data)
        
        assert response.status_code == 400
        assert "No data found" in response.json()['detail']
    
    @patch('app.api.routes.backtest.get_data_store')
    @patch('app.api.routes.backtest.generate_signal')
    def test_api_backtest_no_signals_error(self, mock_generate_signal, mock_get_store, sample_data):
        """Test API error handling when no signals are generated."""
        # Mock data store
        mock_store = Mock()
        bars = [Bar(
            ts=row['timestamp'],
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=row['volume'],
            tf='1h',
            source='test'
        ) for _, row in sample_data.iterrows()]
        mock_store.read_bars.return_value = bars
        mock_get_store.return_value = mock_store
        
        # Mock no signals
        mock_generate_signal.return_value = None
        
        request_data = {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "strategy": "ma_crossover"
        }
        
        response = client.post("/backtest/run", json=request_data)
        
        assert response.status_code == 400
        assert "No signals generated" in response.json()['detail']
    
    @patch('app.api.routes.backtest.get_data_store')
    @patch('app.api.routes.backtest.generate_signal')
    def test_api_backtest_no_trades_error(self, mock_generate_signal, mock_get_store, sample_data):
        """Test API error handling when no trades are executed."""
        # Mock data store
        mock_store = Mock()
        bars = [Bar(
            ts=row['timestamp'],
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=row['volume'],
            tf='1h',
            source='test'
        ) for _, row in sample_data.iterrows()]
        mock_store.read_bars.return_value = bars
        mock_get_store.return_value = mock_store
        
        # Mock signals that result in no trades
        mock_signal = Mock()
        mock_signal.signal = pd.Series([0] * len(sample_data))  # All neutral signals
        mock_generate_signal.return_value = mock_signal
        
        request_data = {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "strategy": "ma_crossover"
        }
        
        response = client.post("/backtest/run", json=request_data)
        
        assert response.status_code == 400
        assert "No trades executed" in response.json()['detail']
    
    def test_api_backtest_parameter_validation(self):
        """Test API parameter validation."""
        # Test invalid symbol
        request_data = {
            "symbol": "",  # Empty symbol
            "timeframe": "1h",
            "strategy": "ma_crossover"
        }
        
        response = client.post("/backtest/run", json=request_data)
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.routes.backtest.get_strategy_list')
    def test_get_available_strategies(self, mock_get_strategies):
        """Test getting available strategies."""
        mock_get_strategies.return_value = ["ma_crossover", "rsi_regime_pullback", "trend_following_ema"]
        
        response = client.get("/backtest/strategies")
        
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert "count" in data
        assert data["count"] == 3
        assert "ma_crossover" in data["strategies"]
    
    @patch('app.api.routes.backtest.get_data_store')
    @patch('app.api.routes.backtest.get_strategy_list')
    def test_backtest_health_check(self, mock_get_strategies, mock_get_store):
        """Test backtest health check."""
        mock_get_strategies.return_value = ["ma_crossover", "rsi_regime_pullback"]
        mock_store = Mock()
        mock_get_store.return_value = mock_store
        
        response = client.get("/backtest/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["data_store_connected"] is True
        assert data["available_strategies"] == 2
        assert data["backtest_engine"] == "unified"
