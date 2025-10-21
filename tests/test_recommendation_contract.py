"""Tests for recommendation contract and service.

This module tests the recommendation generation and contract validation.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import pandas as pd
import numpy as np

from app.api.routes.recommendation import router
from app.service.daily_recommendation import DailyRecommendationService
from app.service.recommendation_contract import Recommendation, PlanDirection, RecommendationRequest, RecommendationResponse

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestRecommendationContract:
    """Test recommendation contract validation."""
    
    def test_valid_recommendation_creation(self):
        """Test creating valid recommendation."""
        recommendation = Recommendation(
            date="2022-01-01",
            symbol="BTC/USDT",
            timeframe="1h",
            direction=PlanDirection.LONG,
            entry_band=[50000.0, 51000.0],
            entry_price=50500.0,
            stop_loss=49000.0,
            take_profit=52000.0,
            quantity=0.1,
            risk_amount=100.0,
            risk_percentage=2.0,
            rationale="Strong bullish signal",
            confidence=85,
            dataset_hash="abc123" * 10,
            params_hash="def456" * 10
        )
        
        assert recommendation.date == "2022-01-01"
        assert recommendation.symbol == "BTC/USDT"
        assert recommendation.direction == PlanDirection.LONG
        assert recommendation.confidence == 85
        assert recommendation.is_valid() is True
    
    def test_hold_recommendation_creation(self):
        """Test creating HOLD recommendation."""
        recommendation = Recommendation(
            date="2022-01-01",
            symbol="BTC/USDT",
            timeframe="1h",
            direction=PlanDirection.HOLD,
            rationale="No clear signal",
            confidence=0,
            dataset_hash="hold_hash",
            params_hash="hold_params"
        )
        
        assert recommendation.direction == PlanDirection.HOLD
        assert recommendation.is_valid() is True
        assert recommendation.get_risk_reward_ratio() is None
    
    def test_invalid_entry_band(self):
        """Test validation of entry band."""
        with pytest.raises(ValueError) as exc_info:
            Recommendation(
                date="2022-01-01",
                symbol="BTC/USDT",
                timeframe="1h",
                direction=PlanDirection.LONG,
                entry_band=[51000.0, 50000.0],  # min > max (invalid)
                rationale="Test",
                confidence=50,
                dataset_hash="abc123" * 10,
                params_hash="def456" * 10
            )
        
        assert "entry_band min must be < max" in str(exc_info.value)
    
    def test_invalid_stop_loss_long(self):
        """Test validation of stop loss for LONG position."""
        with pytest.raises(ValueError) as exc_info:
            Recommendation(
                date="2022-01-01",
                symbol="BTC/USDT",
                timeframe="1h",
                direction=PlanDirection.LONG,
                entry_price=50000.0,
                stop_loss=51000.0,  # SL > entry for LONG (invalid)
                take_profit=52000.0,
                rationale="Test",
                confidence=50,
                dataset_hash="abc123" * 10,
                params_hash="def456" * 10
            )
        
        assert "Stop loss for LONG must be < entry price" in str(exc_info.value)
    
    def test_invalid_stop_loss_short(self):
        """Test validation of stop loss for SHORT position."""
        with pytest.raises(ValueError) as exc_info:
            Recommendation(
                date="2022-01-01",
                symbol="BTC/USDT",
                timeframe="1h",
                direction=PlanDirection.SHORT,
                entry_price=50000.0,
                stop_loss=49000.0,  # SL < entry for SHORT (invalid)
                take_profit=48000.0,
                rationale="Test",
                confidence=50,
                dataset_hash="abc123" * 10,
                params_hash="def456" * 10
            )
        
        assert "Stop loss for SHORT must be > entry price" in str(exc_info.value)
    
    def test_risk_reward_ratio_calculation(self):
        """Test risk/reward ratio calculation."""
        # LONG position
        long_rec = Recommendation(
            date="2022-01-01",
            symbol="BTC/USDT",
            timeframe="1h",
            direction=PlanDirection.LONG,
            entry_price=50000.0,
            stop_loss=49000.0,  # Risk: 1000
            take_profit=52000.0,  # Reward: 2000
            rationale="Test",
            confidence=50,
            dataset_hash="abc123" * 10,
            params_hash="def456" * 10
        )
        
        ratio = long_rec.get_risk_reward_ratio()
        assert ratio == 2.0  # 2000 / 1000
        
        # SHORT position
        short_rec = Recommendation(
            date="2022-01-01",
            symbol="BTC/USDT",
            timeframe="1h",
            direction=PlanDirection.SHORT,
            entry_price=50000.0,
            stop_loss=51000.0,  # Risk: 1000
            take_profit=48000.0,  # Reward: 2000
            rationale="Test",
            confidence=50,
            dataset_hash="abc123" * 10,
            params_hash="def456" * 10
        )
        
        ratio = short_rec.get_risk_reward_ratio()
        assert ratio == 2.0  # 2000 / 1000


class TestDailyRecommendationService:
    """Test daily recommendation service."""
    
    @pytest.fixture
    def mock_service(self):
        """Create mock recommendation service."""
        with patch('app.service.daily_recommendation.DataStore'), \
             patch('app.service.daily_recommendation.DataFetcher'):
            service = DailyRecommendationService(capital=10000.0, max_risk_pct=2.0)
            return service
    
    @patch('app.service.daily_recommendation.DataStore')
    @patch('app.service.daily_recommendation.DataFetcher')
    def test_service_initialization(self, mock_fetcher, mock_store):
        """Test service initialization."""
        service = DailyRecommendationService(capital=5000.0, max_risk_pct=1.5)
        
        assert service.capital == 5000.0
        assert service.max_risk_pct == 1.5
        assert service.store is not None
        assert service.fetcher is not None
    
    @patch('app.service.daily_recommendation.DataStore')
    @patch('app.service.daily_recommendation.DataFetcher')
    def test_hold_recommendation_no_data(self, mock_fetcher, mock_store):
        """Test HOLD recommendation when no data is available."""
        # Mock empty data
        mock_store_instance = Mock()
        mock_store_instance.read_bars.return_value = []
        mock_store.return_value = mock_store_instance
        
        service = DailyRecommendationService()
        
        recommendation = service.get_daily_recommendation("BTC/USDT", "2022-01-01")
        
        assert recommendation.direction == PlanDirection.HOLD
        assert "No signals available" in recommendation.rationale
        assert recommendation.confidence == 0
    
    @patch('app.service.daily_recommendation.DataStore')
    @patch('app.service.daily_recommendation.DataFetcher')
    def test_hold_recommendation_low_confidence(self, mock_fetcher, mock_store):
        """Test HOLD recommendation for low confidence."""
        # Mock data with low confidence signals
        mock_store_instance = Mock()
        mock_bars = [Mock() for _ in range(100)]  # Mock bars
        mock_store_instance.read_bars.return_value = mock_bars
        mock_store.return_value = mock_store_instance
        
        service = DailyRecommendationService()
        
        # Mock low confidence score
        with patch.object(service, '_compute_combined_score', return_value=(0.1, 1, 0.1)):
            recommendation = service.get_daily_recommendation("BTC/USDT", "2022-01-01")
            
            assert recommendation.direction == PlanDirection.HOLD
            assert "Low confidence score" in recommendation.rationale
    
    @patch('app.service.daily_recommendation.DataStore')
    @patch('app.service.daily_recommendation.DataFetcher')
    def test_hold_recommendation_strong_conflict(self, mock_fetcher, mock_store):
        """Test HOLD recommendation for strong directional conflict."""
        # Mock data
        mock_store_instance = Mock()
        mock_bars = [Mock() for _ in range(100)]
        mock_store_instance.read_bars.return_value = mock_bars
        mock_store.return_value = mock_store_instance
        
        service = DailyRecommendationService()
        
        # Mock strong conflict
        with patch.object(service, '_has_strong_conflict', return_value=True):
            recommendation = service.get_daily_recommendation("BTC/USDT", "2022-01-01")
            
            assert recommendation.direction == PlanDirection.HOLD
            assert "Strong directional conflict" in recommendation.rationale


class TestRecommendationAPI:
    """Test recommendation API endpoints."""
    
    @patch('app.api.routes.recommendation.get_recommendation_service')
    def test_get_daily_recommendation_success(self, mock_get_service):
        """Test successful daily recommendation."""
        # Mock service
        mock_service = Mock()
        mock_recommendation = Recommendation(
            date="2022-01-01",
            symbol="BTC/USDT",
            timeframe="1h",
            direction=PlanDirection.LONG,
            rationale="Strong signal",
            confidence=85,
            dataset_hash="abc123" * 10,
            params_hash="def456" * 10
        )
        mock_service.get_daily_recommendation.return_value = mock_recommendation
        mock_get_service.return_value = mock_service
        
        response = client.get("/recommendation/daily?symbol=BTC/USDT&date=2022-01-01")
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTC/USDT"
        assert data["direction"] == "LONG"
        assert data["confidence"] == 85
    
    @patch('app.api.routes.recommendation.get_recommendation_service')
    def test_get_daily_recommendation_hold(self, mock_get_service):
        """Test HOLD recommendation."""
        # Mock service
        mock_service = Mock()
        mock_recommendation = Recommendation(
            date="2022-01-01",
            symbol="BTC/USDT",
            timeframe="1h",
            direction=PlanDirection.HOLD,
            rationale="No clear signal",
            confidence=0,
            dataset_hash="hold_hash",
            params_hash="hold_params"
        )
        mock_service.get_daily_recommendation.return_value = mock_recommendation
        mock_get_service.return_value = mock_service
        
        response = client.get("/recommendation/daily?symbol=BTC/USDT&date=2022-01-01")
        
        assert response.status_code == 200
        data = response.json()
        assert data["direction"] == "HOLD"
        assert data["confidence"] == 0
    
    def test_get_daily_recommendation_invalid_date(self):
        """Test invalid date format."""
        response = client.get("/recommendation/daily?symbol=BTC/USDT&date=invalid-date")
        
        assert response.status_code == 400
        assert "Invalid date format" in response.json()['detail']
    
    @patch('app.api.routes.recommendation.get_recommendation_service')
    def test_get_recommendation_history(self, mock_get_service):
        """Test getting recommendation history."""
        # Mock service
        mock_service = Mock()
        mock_recommendations = [
            Recommendation(
                date="2022-01-01",
                symbol="BTC/USDT",
                timeframe="1h",
                direction=PlanDirection.LONG,
                rationale="Signal 1",
                confidence=85,
                dataset_hash="abc123" * 10,
                params_hash="def456" * 10
            ),
            Recommendation(
                date="2022-01-02",
                symbol="BTC/USDT",
                timeframe="1h",
                direction=PlanDirection.SHORT,
                rationale="Signal 2",
                confidence=75,
                dataset_hash="abc123" * 10,
                params_hash="def456" * 10
            )
        ]
        mock_service.get_recommendation_history.return_value = mock_recommendations
        mock_get_service.return_value = mock_service
        
        response = client.get("/recommendation/history?symbol=BTC/USDT&from_date=2022-01-01&to_date=2022-01-02")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["direction"] == "LONG"
        assert data[1]["direction"] == "SHORT"
    
    @patch('app.api.routes.recommendation.get_recommendation_service')
    def test_get_recommendation_stats(self, mock_get_service):
        """Test getting recommendation statistics."""
        # Mock service
        mock_service = Mock()
        mock_recommendations = [
            Recommendation(
                date="2022-01-01",
                symbol="BTC/USDT",
                timeframe="1h",
                direction=PlanDirection.LONG,
                rationale="Signal 1",
                confidence=85,
                dataset_hash="abc123" * 10,
                params_hash="def456" * 10
            ),
            Recommendation(
                date="2022-01-02",
                symbol="BTC/USDT",
                timeframe="1h",
                direction=PlanDirection.SHORT,
                rationale="Signal 2",
                confidence=75,
                dataset_hash="abc123" * 10,
                params_hash="def456" * 10
            ),
            Recommendation(
                date="2022-01-03",
                symbol="BTC/USDT",
                timeframe="1h",
                direction=PlanDirection.HOLD,
                rationale="No signal",
                confidence=0,
                dataset_hash="hold_hash",
                params_hash="hold_params"
            )
        ]
        mock_service.get_recommendation_history.return_value = mock_recommendations
        mock_get_service.return_value = mock_service
        
        response = client.get("/recommendation/stats/BTC/USDT")
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTC/USDT"
        assert data["total_recommendations"] == 3
        assert data["long_recommendations"] == 1
        assert data["short_recommendations"] == 1
        assert data["hold_recommendations"] == 1
        assert data["average_confidence"] == 53.33  # (85 + 75 + 0) / 3
    
    def test_recommendation_health_check(self):
        """Test recommendation health check."""
        response = client.get("/recommendation/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
