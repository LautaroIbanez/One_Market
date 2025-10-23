"""Unit tests for recommendation engines integration.

This module tests the integration of EntryBandEngine and TpSlEngine
in the DailyRecommendationService to ensure:
1. LONG and SHORT recommendations get proper SL/TP levels
2. Entry bands are calculated correctly for both directions
3. Position sizing works with real engines
4. Risk-reward ratios are reasonable
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from app.service.daily_recommendation import DailyRecommendationService
from app.service.recommendation_contract import PlanDirection


class TestRecommendationEngines:
    """Test recommendation engines integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = DailyRecommendationService(capital=10000.0, max_risk_pct=2.0)
        
        # Mock data store
        self.mock_store = Mock()
        self.service.store = self.mock_store
        
        # Create realistic test data
        self.test_bars = self._create_test_bars()
        self.mock_store.read_bars.return_value = self.test_bars
    
    def _create_test_bars(self):
        """Create realistic test bars for engine testing."""
        bars = []
        base_price = 50000.0
        
        # Create 50 bars with realistic OHLCV data
        for i in range(50):
            timestamp = int((datetime.now(timezone.utc) - timedelta(hours=50-i)).timestamp() * 1000)
            
            # Add some volatility
            volatility = 0.02 * np.sin(i * 0.1)  # 2% volatility
            price = base_price * (1 + volatility)
            
            # Create realistic OHLC
            high = price * (1 + abs(volatility) * 0.5)
            low = price * (1 - abs(volatility) * 0.5)
            close = price
            volume = 1000 + np.random.randint(-200, 200)
            
            mock_bar = Mock()
            mock_bar.timestamp = timestamp
            mock_bar.high = high
            mock_bar.low = low
            mock_bar.close = close
            mock_bar.volume = volume
            mock_bar.to_dict.return_value = {
                'timestamp': timestamp,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            }
            bars.append(mock_bar)
        
        return bars
    
    def test_long_recommendation_with_engines(self):
        """Test LONG recommendation with real engines."""
        # Mock current price
        current_price = 50000.0
        
        with patch.object(self.service, '_get_current_price', return_value=current_price):
            recommendation = self.service._get_signal_based_recommendation(
                "BTC/USDT", "2024-01-01", ["1h"]
            )
            
            # Validate recommendation structure
            assert recommendation is not None
            assert recommendation.direction == PlanDirection.LONG
            assert recommendation.entry_price is not None
            assert recommendation.stop_loss is not None
            assert recommendation.take_profit is not None
            assert recommendation.quantity is not None
            assert recommendation.risk_amount is not None
            
            # Validate LONG-specific logic
            assert recommendation.stop_loss < recommendation.entry_price  # SL below entry for LONG
            assert recommendation.take_profit > recommendation.entry_price  # TP above entry for LONG
            
            # Validate entry band
            if recommendation.entry_band:
                entry_low, entry_high = recommendation.entry_band
                assert entry_low <= recommendation.entry_price <= entry_high
            
            # Validate position sizing
            assert recommendation.quantity > 0
            assert recommendation.risk_amount > 0
            assert recommendation.risk_percentage == 2.0
            
            # Validate engine analysis
            if recommendation.mtf_analysis and 'engine_analysis' in recommendation.mtf_analysis:
                engine_analysis = recommendation.mtf_analysis['engine_analysis']
                assert 'entry_method' in engine_analysis
                assert 'tp_sl_method' in engine_analysis
                assert 'risk_reward_ratio' in engine_analysis
                
                # Risk-reward ratio should be positive
                assert engine_analysis['risk_reward_ratio'] > 0
    
    def test_short_recommendation_with_engines(self):
        """Test SHORT recommendation with real engines."""
        # Mock current price
        current_price = 50000.0
        
        with patch.object(self.service, '_get_current_price', return_value=current_price):
            # Force SHORT direction by mocking the signal analysis
            with patch.object(self.service, '_get_signal_based_recommendation') as mock_method:
                # Create a SHORT recommendation manually
                recommendation = self.service._get_signal_based_recommendation(
                    "BTC/USDT", "2024-01-01", ["1h"]
                )
                
                # Override direction to SHORT for testing
                recommendation.direction = PlanDirection.SHORT
                
                # Recalculate with SHORT direction
                direction_int = -1
                
                # Use EntryBandEngine for SHORT
                from app.service.entry_band import calculate_entry_band
                entry_result = calculate_entry_band(
                    pd.DataFrame([bar.to_dict() for bar in self.test_bars]),
                    current_price,
                    signal_direction=direction_int,
                    beta=0.002,
                    use_vwap=True
                )
                
                # Use TpSlEngine for SHORT
                from app.service.tp_sl_engine import calculate_tp_sl, TPSLConfig
                tp_sl_config = TPSLConfig(
                    method="hybrid",
                    atr_period=14,
                    atr_multiplier=2.0,
                    min_tp_pct=0.01,
                    max_tp_pct=0.10,
                    min_sl_pct=0.005,
                    max_sl_pct=0.05
                )
                
                tp_sl_result = calculate_tp_sl(
                    pd.DataFrame([bar.to_dict() for bar in self.test_bars]),
                    entry_result.entry_price,
                    direction_int,
                    tp_sl_config
                )
                
                # Validate SHORT-specific logic
                assert tp_sl_result.stop_loss > entry_result.entry_price  # SL above entry for SHORT
                assert tp_sl_result.take_profit < entry_result.entry_price  # TP below entry for SHORT
                
                # Risk-reward ratio should be positive
                if tp_sl_result.stop_loss and tp_sl_result.take_profit:
                    risk = abs(entry_result.entry_price - tp_sl_result.stop_loss)
                    reward = abs(tp_sl_result.take_profit - entry_result.entry_price)
                    risk_reward_ratio = reward / risk if risk > 0 else 0
                    assert risk_reward_ratio > 0
    
    def test_entry_band_calculation(self):
        """Test entry band calculation with different directions."""
        df = pd.DataFrame([bar.to_dict() for bar in self.test_bars])
        current_price = 50000.0
        
        # Test LONG entry band
        from app.service.entry_band import calculate_entry_band
        long_result = calculate_entry_band(
            df, current_price, signal_direction=1, beta=0.002, use_vwap=True
        )
        
        assert long_result.entry_price is not None
        assert long_result.entry_low is not None
        assert long_result.entry_high is not None
        assert long_result.entry_low <= long_result.entry_price <= long_result.entry_high
        assert long_result.method in ['vwap', 'typical_price']
        
        # Test SHORT entry band
        short_result = calculate_entry_band(
            df, current_price, signal_direction=-1, beta=0.002, use_vwap=True
        )
        
        assert short_result.entry_price is not None
        assert short_result.entry_low is not None
        assert short_result.entry_high is not None
        assert short_result.entry_low <= short_result.entry_price <= short_result.entry_high
    
    def test_tp_sl_calculation(self):
        """Test TP/SL calculation with different directions."""
        df = pd.DataFrame([bar.to_dict() for bar in self.test_bars])
        entry_price = 50000.0
        
        from app.service.tp_sl_engine import calculate_tp_sl, TPSLConfig
        
        # Test LONG TP/SL
        long_config = TPSLConfig(
            method="hybrid",
            atr_period=14,
            atr_multiplier=2.0,
            min_tp_pct=0.01,
            max_tp_pct=0.10,
            min_sl_pct=0.005,
            max_sl_pct=0.05
        )
        
        long_result = calculate_tp_sl(df, entry_price, 1, long_config)
        
        assert long_result.stop_loss is not None
        assert long_result.take_profit is not None
        assert long_result.stop_loss < entry_price  # SL below entry for LONG
        assert long_result.take_profit > entry_price  # TP above entry for LONG
        
        # Test SHORT TP/SL
        short_result = calculate_tp_sl(df, entry_price, -1, long_config)
        
        assert short_result.stop_loss is not None
        assert short_result.take_profit is not None
        assert short_result.stop_loss > entry_price  # SL above entry for SHORT
        assert short_result.take_profit < entry_price  # TP below entry for SHORT
    
    def test_position_sizing_integration(self):
        """Test position sizing integration with engines."""
        from app.core.risk import calculate_position_size_fixed_risk
        
        capital = 10000.0
        risk_pct = 0.02
        entry_price = 50000.0
        stop_loss = 49000.0  # 2% risk
        
        position_size = calculate_position_size_fixed_risk(
            capital=capital,
            risk_pct=risk_pct,
            entry_price=entry_price,
            stop_loss=stop_loss
        )
        
        assert position_size.quantity > 0
        assert position_size.risk_amount > 0
        assert position_size.notional_value > 0
        
        # Validate risk calculation
        expected_risk = capital * risk_pct
        assert abs(position_size.risk_amount - expected_risk) < 0.01
    
    def test_risk_reward_ratio_calculation(self):
        """Test risk-reward ratio calculation."""
        entry_price = 50000.0
        stop_loss = 49000.0  # 2% risk
        take_profit = 52000.0  # 4% reward
        
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        assert risk_reward_ratio > 0
        assert risk_reward_ratio == 2.0  # 4% reward / 2% risk = 2:1
    
    def test_engine_analysis_metadata(self):
        """Test that engine analysis metadata is properly included."""
        current_price = 50000.0
        
        with patch.object(self.service, '_get_current_price', return_value=current_price):
            recommendation = self.service._get_signal_based_recommendation(
                "BTC/USDT", "2024-01-01", ["1h"]
            )
            
            # Check that engine analysis is included
            assert recommendation.mtf_analysis is not None
            assert 'engine_analysis' in recommendation.mtf_analysis
            
            engine_analysis = recommendation.mtf_analysis['engine_analysis']
            
            # Required fields
            required_fields = [
                'entry_method', 'entry_mid', 'entry_beta', 'entry_range_pct',
                'tp_sl_method', 'atr_value', 'risk_reward_ratio',
                'position_size', 'risk_amount'
            ]
            
            for field in required_fields:
                assert field in engine_analysis, f"Missing field: {field}"
            
            # Validate field types
            assert isinstance(engine_analysis['entry_method'], str)
            assert isinstance(engine_analysis['entry_mid'], (int, float))
            assert isinstance(engine_analysis['entry_beta'], (int, float))
            assert isinstance(engine_analysis['risk_reward_ratio'], (int, float))
            assert isinstance(engine_analysis['position_size'], (int, float))
            assert isinstance(engine_analysis['risk_amount'], (int, float))
    
    def test_hold_recommendation_with_engines(self):
        """Test HOLD recommendation still works with engines."""
        # Mock insufficient data to trigger HOLD
        self.mock_store.read_bars.return_value = []
        
        recommendation = self.service._get_signal_based_recommendation(
            "BTC/USDT", "2024-01-01", ["1h"]
        )
        
        assert recommendation is not None
        assert recommendation.direction == PlanDirection.HOLD
        assert recommendation.entry_price is None
        assert recommendation.stop_loss is None
        assert recommendation.take_profit is None
        assert recommendation.quantity is None
        assert recommendation.risk_amount is None
    
    def test_engine_error_handling(self):
        """Test error handling in engine calculations."""
        # Mock engine failure
        with patch('app.service.entry_band.calculate_entry_band', side_effect=Exception("Engine error")):
            with patch.object(self.service, '_get_current_price', return_value=50000.0):
                recommendation = self.service._get_signal_based_recommendation(
                    "BTC/USDT", "2024-01-01", ["1h"]
                )
                
                # Should fallback to HOLD on engine error
                assert recommendation is not None
                assert recommendation.direction == PlanDirection.HOLD


if __name__ == "__main__":
    pytest.main([__file__])
