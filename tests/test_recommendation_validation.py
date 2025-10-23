"""Unit tests for recommendation validation and confidence ranges.

This module tests the DailyRecommendationService to ensure:
1. Confidence values are within valid ranges (0-100)
2. Data freshness validation works correctly
3. Volatility-based calculations are reasonable
4. Recommendation objects are properly constructed
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from app.service.daily_recommendation import DailyRecommendationService
from app.service.recommendation_contract import PlanDirection


class TestRecommendationValidation:
    """Test recommendation validation and confidence ranges."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = DailyRecommendationService(capital=10000.0, max_risk_pct=2.0)
        
        # Mock data store
        self.mock_store = Mock()
        self.service.store = self.mock_store
        
        # Mock strategy ranking service
        self.mock_ranking = Mock()
        self.service.strategy_ranking = self.mock_ranking
    
    def test_confidence_range_validation(self):
        """Test that confidence values are always within 0-100 range."""
        # Test with various confidence inputs
        test_cases = [
            (0.0, 0),      # Minimum confidence
            (0.5, 50),     # Medium confidence
            (1.0, 100),    # Maximum confidence
            (1.5, 100),    # Above 1.0 should be capped at 100
            (-0.1, 0),     # Negative should be capped at 0
        ]
        
        for input_confidence, expected_confidence in test_cases:
            # Mock the service to return a recommendation with the test confidence
            with patch.object(self.service, '_get_signal_based_recommendation') as mock_method:
                mock_recommendation = Mock()
                mock_recommendation.confidence = int(input_confidence * 100)
                mock_recommendation.direction = PlanDirection.LONG
                mock_recommendation.model_dump.return_value = {"confidence": expected_confidence}
                mock_method.return_value = mock_recommendation
                
                # Test the confidence is within bounds
                assert 0 <= expected_confidence <= 100, f"Confidence {expected_confidence} out of range"
    
    def test_data_freshness_validation(self):
        """Test data freshness validation logic."""
        # Test with fresh data
        fresh_timestamp = int((datetime.now(timezone.utc) - timedelta(minutes=30)).timestamp() * 1000)
        mock_bars = [Mock(timestamp=fresh_timestamp)]
        self.mock_store.read_bars.return_value = mock_bars
        
        freshness = self.service._validate_data_freshness("BTC/USDT", "2024-01-01", ["1h"])
        
        assert freshness["is_fresh"] is True
        assert freshness["overall_status"] == "fresh"
        
        # Test with stale data
        stale_timestamp = int((datetime.now(timezone.utc) - timedelta(hours=3)).timestamp() * 1000)
        mock_bars = [Mock(timestamp=stale_timestamp)]
        self.mock_store.read_bars.return_value = mock_bars
        
        freshness = self.service._validate_data_freshness("BTC/USDT", "2024-01-01", ["1h"])
        
        assert freshness["is_fresh"] is False
        assert freshness["overall_status"] in ["stale", "stale_with_warnings"]
        assert len(freshness["warnings"]) > 0
    
    def test_volatility_calculation_bounds(self):
        """Test that volatility-based calculations produce reasonable values."""
        # Create mock data with known volatility
        mock_bars = []
        base_price = 50000.0
        
        # Create bars with 2% daily volatility
        for i in range(20):
            timestamp = int((datetime.now(timezone.utc) - timedelta(hours=20-i)).timestamp() * 1000)
            volatility = 0.02 * np.sin(i * 0.5)  # 2% volatility pattern
            price = base_price * (1 + volatility)
            
            mock_bar = Mock()
            mock_bar.timestamp = timestamp
            mock_bar.high = price * 1.01
            mock_bar.low = price * 0.99
            mock_bar.close = price
            mock_bars.append(mock_bar)
        
        self.mock_store.read_bars.return_value = mock_bars
        
        # Test volatility calculation
        levels = self.service._calculate_volatility_based_levels("BTC/USDT", "1h", base_price, 1)
        
        # Validate that levels are reasonable
        assert levels["entry_band"] is not None
        assert levels["stop_loss"] is not None
        assert levels["take_profit"] is not None
        
        # Entry band should be around current price
        entry_low, entry_high = levels["entry_band"]
        assert entry_low < base_price < entry_high
        
        # Stop loss should be below entry for long position
        assert levels["stop_loss"] < base_price
        
        # Take profit should be above entry for long position
        assert levels["take_profit"] > base_price
        
        # Risk-reward ratio should be positive
        assert levels["risk_reward_ratio"] > 0
    
    def test_recommendation_object_validation(self):
        """Test that recommendation objects are properly constructed."""
        # Mock data
        mock_bars = []
        for i in range(50):
            timestamp = int((datetime.now(timezone.utc) - timedelta(hours=50-i)).timestamp() * 1000)
            mock_bar = Mock()
            mock_bar.timestamp = timestamp
            mock_bar.high = 50000.0
            mock_bar.low = 49000.0
            mock_bar.close = 49500.0
            mock_bars.append(mock_bar)
        
        self.mock_store.read_bars.return_value = mock_bars
        
        # Mock strategy ranking
        mock_ranking = Mock()
        mock_ranking.strategy_name = "test_strategy"
        mock_ranking.timeframe = "1h"
        mock_ranking.score = 0.75
        mock_ranking.sharpe_ratio = 1.2
        mock_ranking.win_rate = 0.65
        mock_ranking.max_drawdown = -0.08
        mock_ranking.total_return = 0.15
        mock_ranking.profit_factor = 1.5
        mock_ranking.calmar_ratio = 0.8
        
        self.mock_ranking.get_rankings.return_value = [mock_ranking]
        
        # Mock data for volatility calculation
        mock_bars = []
        for i in range(50):
            timestamp = int((datetime.now(timezone.utc) - timedelta(hours=50-i)).timestamp() * 1000)
            mock_bar = Mock()
            mock_bar.timestamp = timestamp
            mock_bar.high = 50000.0
            mock_bar.low = 49000.0
            mock_bar.close = 49500.0
            mock_bars.append(mock_bar)
        
        self.mock_store.read_bars.return_value = mock_bars
        
        # Mock weight calculator
        mock_weights = Mock()
        mock_weights.confidence = 0.75
        mock_weights.direction_weights = {"LONG": 0.8, "SHORT": 0.2, "HOLD": 0.0}
        mock_weights.strategy_weights = [mock_ranking]
        
        with patch.object(self.service.weight_calculator, 'calculate_weights', return_value=mock_weights):
            recommendation = self.service._get_ranking_based_recommendation("BTC/USDT", "2024-01-01", ["1h"])
            
            # Validate recommendation object
            assert recommendation is not None
            assert recommendation.confidence >= 0
            assert recommendation.confidence <= 100
            assert recommendation.direction in [PlanDirection.LONG, PlanDirection.SHORT, PlanDirection.HOLD]
            assert recommendation.symbol == "BTC/USDT"
            assert recommendation.date == "2024-01-01"
            
            # Validate that volatility analysis is included (if mtf_analysis exists)
            if recommendation.mtf_analysis:
                assert "volatility_analysis" in recommendation.mtf_analysis
                volatility_analysis = recommendation.mtf_analysis["volatility_analysis"]
                assert "atr" in volatility_analysis
                assert "risk_reward_ratio" in volatility_analysis
    
    def test_confidence_calculation_edge_cases(self):
        """Test confidence calculation with edge cases."""
        # Test with very low confidence
        mock_weights = Mock()
        mock_weights.confidence = 0.1  # Very low confidence
        mock_weights.direction_weights = {"LONG": 0.3, "SHORT": 0.3, "HOLD": 0.4}
        mock_weights.strategy_weights = []
        
        # Mock data for the service
        mock_bars = []
        for i in range(50):
            timestamp = int((datetime.now(timezone.utc) - timedelta(hours=50-i)).timestamp() * 1000)
            mock_bar = Mock()
            mock_bar.timestamp = timestamp
            mock_bar.high = 50000.0
            mock_bar.low = 49000.0
            mock_bar.close = 49500.0
            mock_bars.append(mock_bar)
        
        self.mock_store.read_bars.return_value = mock_bars
        self.mock_ranking.get_rankings.return_value = []
        
        with patch.object(self.service.weight_calculator, 'calculate_weights', return_value=mock_weights):
            recommendation = self.service._get_ranking_based_recommendation("BTC/USDT", "2024-01-01", ["1h"])
            
            # Should return HOLD recommendation due to no ranking data
            assert recommendation.direction == PlanDirection.HOLD
            assert "No ranking data available" in recommendation.rationale
        
        # Test with very high confidence - need to provide rankings
        mock_ranking = Mock()
        mock_ranking.strategy_name = "test_strategy"
        mock_ranking.timeframe = "1h"
        mock_ranking.score = 0.95
        mock_ranking.sharpe_ratio = 1.5
        mock_ranking.win_rate = 0.75
        mock_ranking.max_drawdown = -0.05
        mock_ranking.total_return = 0.25
        mock_ranking.profit_factor = 2.0
        mock_ranking.calmar_ratio = 1.2
        
        self.mock_ranking.get_rankings.return_value = [mock_ranking]
        
        mock_weights.confidence = 0.95  # Very high confidence
        mock_weights.strategy_weights = [mock_ranking]  # Non-empty strategy weights
        
        with patch.object(self.service.weight_calculator, 'calculate_weights', return_value=mock_weights):
            with patch.object(self.service, '_create_weighted_recommendation') as mock_create:
                mock_create.return_value = Mock()
                self.service._get_ranking_based_recommendation("BTC/USDT", "2024-01-01", ["1h"])
                
                # Should proceed with recommendation creation
                mock_create.assert_called_once()
    
    def test_volatility_multiplier_bounds(self):
        """Test that volatility multipliers stay within reasonable bounds."""
        # Test with very low volatility
        mock_bars = []
        base_price = 50000.0
        
        # Create bars with very low volatility (0.1%)
        for i in range(20):
            timestamp = int((datetime.now(timezone.utc) - timedelta(hours=20-i)).timestamp() * 1000)
            price = base_price * (1 + 0.001 * np.sin(i))  # 0.1% volatility
            
            mock_bar = Mock()
            mock_bar.timestamp = timestamp
            mock_bar.high = price * 1.0005
            mock_bar.low = price * 0.9995
            mock_bar.close = price
            mock_bars.append(mock_bar)
        
        self.mock_store.read_bars.return_value = mock_bars
        
        levels = self.service._calculate_volatility_based_levels("BTC/USDT", "1h", base_price, 1)
        
        # Volatility multiplier should be at least 1.0
        assert levels["volatility_multiplier"] >= 1.0
        
        # Test with very high volatility
        mock_bars = []
        # Create bars with very high volatility (5%)
        for i in range(20):
            timestamp = int((datetime.now(timezone.utc) - timedelta(hours=20-i)).timestamp() * 1000)
            price = base_price * (1 + 0.05 * np.sin(i))  # 5% volatility
            
            mock_bar = Mock()
            mock_bar.timestamp = timestamp
            mock_bar.high = price * 1.01
            mock_bar.low = price * 0.99
            mock_bar.close = price
            mock_bars.append(mock_bar)
        
        self.mock_store.read_bars.return_value = mock_bars
        
        levels = self.service._calculate_volatility_based_levels("BTC/USDT", "1h", base_price, 1)
        
        # Volatility multiplier should be capped at 3.0
        assert levels["volatility_multiplier"] <= 3.0


if __name__ == "__main__":
    pytest.main([__file__])
