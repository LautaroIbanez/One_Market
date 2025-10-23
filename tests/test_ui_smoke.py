"""Smoke tests for UI integration with backend.

This module tests that the UI correctly handles the nested response structure
from the backend and properly displays LONG/SHORT recommendations.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# Mock the streamlit imports
import sys
from unittest.mock import MagicMock
sys.modules['streamlit'] = MagicMock()

from ui.app import create_decision


class TestUISmoke:
    """Test UI smoke tests for backend integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_df = pd.DataFrame({
            'timestamp': [datetime.now(timezone.utc).timestamp() * 1000],
            'open': [50000.0],
            'high': [51000.0],
            'low': [49000.0],
            'close': [50500.0],
            'volume': [1000]
        })
        
        self.mock_combined_signal = Mock()
        self.mock_combined_signal.signal = pd.Series([1])
        self.mock_combined_signal.confidence = pd.Series([0.75])
    
    def test_long_recommendation_parsing(self):
        """Test that LONG recommendation is parsed correctly."""
        # Mock backend response for LONG recommendation
        mock_response = {
            "recommendation": {
                "date": "2024-01-01",
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "direction": "LONG",
                "entry_price": 50000.0,
                "entry_band": [49500.0, 50500.0],
                "stop_loss": 49000.0,
                "take_profit": 52000.0,
                "quantity": 0.2,
                "risk_amount": 200.0,
                "risk_percentage": 2.0,
                "confidence": 75,
                "rationale": "Based on ma_crossover with ATR-based levels",
                "strategy_name": "signal_based",
                "strategy_score": 0.75,
                "mtf_analysis": {
                    "engine_analysis": {
                        "entry_method": "vwap",
                        "tp_sl_method": "hybrid",
                        "atr_value": 500.0,
                        "risk_reward_ratio": 2.0
                    }
                }
            },
            "metadata": {
                "generated_at": "2024-01-01T10:00:00",
                "symbol": "BTC/USDT",
                "date": "2024-01-01"
            }
        }
        
        with patch('ui.app.BackendClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get_daily_recommendation.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            decision, advice = create_decision(
                self.mock_df, 
                self.mock_combined_signal, 
                risk_pct=0.02, 
                capital=10000.0, 
                symbol="BTC/USDT"
            )
            
            # Validate decision object
            assert decision is not None
            assert decision.should_execute is True  # LONG should execute
            assert decision.signal == 1  # LONG signal
            assert decision.entry_price == 50000.0
            assert decision.stop_loss == 49000.0
            assert decision.take_profit == 52000.0
            assert decision.skip_reason == "Based on ma_crossover with ATR-based levels"
            
            # Validate position size
            assert decision.position_size is not None
            assert decision.position_size.quantity == 0.2
            assert decision.position_size.risk_amount == 200.0
            
            # Validate advice object
            assert advice is not None
            assert advice.confidence_score == 0.75
            assert advice.consensus_direction == 1  # LONG
    
    def test_short_recommendation_parsing(self):
        """Test that SHORT recommendation is parsed correctly."""
        # Mock backend response for SHORT recommendation
        mock_response = {
            "recommendation": {
                "date": "2024-01-01",
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "direction": "SHORT",
                "entry_price": 50000.0,
                "entry_band": [49500.0, 50500.0],
                "stop_loss": 51000.0,  # Above entry for SHORT
                "take_profit": 48000.0,  # Below entry for SHORT
                "quantity": 0.2,
                "risk_amount": 200.0,
                "risk_percentage": 2.0,
                "confidence": 80,
                "rationale": "Based on rsi_regime_pullback with ATR-based levels",
                "strategy_name": "signal_based",
                "strategy_score": 0.80,
                "mtf_analysis": {
                    "engine_analysis": {
                        "entry_method": "vwap",
                        "tp_sl_method": "hybrid",
                        "atr_value": 500.0,
                        "risk_reward_ratio": 2.0
                    }
                }
            },
            "metadata": {
                "generated_at": "2024-01-01T10:00:00",
                "symbol": "BTC/USDT",
                "date": "2024-01-01"
            }
        }
        
        with patch('ui.app.BackendClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get_daily_recommendation.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            decision, advice = create_decision(
                self.mock_df, 
                self.mock_combined_signal, 
                risk_pct=0.02, 
                capital=10000.0, 
                symbol="BTC/USDT"
            )
            
            # Validate decision object
            assert decision is not None
            assert decision.should_execute is True  # SHORT should execute
            assert decision.signal == -1  # SHORT signal
            assert decision.entry_price == 50000.0
            assert decision.stop_loss == 51000.0  # Above entry for SHORT
            assert decision.take_profit == 48000.0  # Below entry for SHORT
            assert decision.skip_reason == "Based on rsi_regime_pullback with ATR-based levels"
            
            # Validate position size
            assert decision.position_size is not None
            assert decision.position_size.quantity == 0.2
            assert decision.position_size.risk_amount == 200.0
            
            # Validate advice object
            assert advice is not None
            assert advice.confidence_score == 0.80
            assert advice.consensus_direction == -1  # SHORT
    
    def test_hold_recommendation_parsing(self):
        """Test that HOLD recommendation is parsed correctly."""
        # Mock backend response for HOLD recommendation
        mock_response = {
            "recommendation": {
                "date": "2024-01-01",
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "direction": "HOLD",
                "entry_price": None,
                "entry_band": None,
                "stop_loss": None,
                "take_profit": None,
                "quantity": None,
                "risk_amount": None,
                "risk_percentage": None,
                "confidence": 0,
                "rationale": "No clear signal or insufficient data",
                "strategy_name": None,
                "strategy_score": None,
                "mtf_analysis": None
            },
            "metadata": {
                "generated_at": "2024-01-01T10:00:00",
                "symbol": "BTC/USDT",
                "date": "2024-01-01"
            }
        }
        
        with patch('ui.app.BackendClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get_daily_recommendation.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            decision, advice = create_decision(
                self.mock_df, 
                self.mock_combined_signal, 
                risk_pct=0.02, 
                capital=10000.0, 
                symbol="BTC/USDT"
            )
            
            # Validate decision object
            assert decision is not None
            assert decision.should_execute is False  # HOLD should not execute
            assert decision.signal == 0  # HOLD signal
            assert decision.entry_price is None
            assert decision.stop_loss is None
            assert decision.take_profit is None
            assert decision.skip_reason == "No clear signal or insufficient data"
            
            # Validate position size
            assert decision.position_size is None
            
            # Validate advice object
            assert advice is not None
            assert advice.confidence_score == 0.0
            assert advice.consensus_direction == 0  # HOLD
    
    def test_backend_error_handling(self):
        """Test that backend errors are handled gracefully."""
        with patch('ui.app.BackendClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get_daily_recommendation.return_value = None  # Backend error
            mock_client_class.return_value = mock_client
            
            decision, advice = create_decision(
                self.mock_df, 
                self.mock_combined_signal, 
                risk_pct=0.02, 
                capital=10000.0, 
                symbol="BTC/USDT"
            )
            
            # Should return None for both when backend fails
            assert decision is None
            assert advice is None
    
    def test_malformed_response_handling(self):
        """Test that malformed responses are handled gracefully."""
        # Mock malformed response (missing 'recommendation' key)
        mock_response = {
            "metadata": {
                "generated_at": "2024-01-01T10:00:00",
                "symbol": "BTC/USDT",
                "date": "2024-01-01"
            }
        }
        
        with patch('ui.app.BackendClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get_daily_recommendation.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            decision, advice = create_decision(
                self.mock_df, 
                self.mock_combined_signal, 
                risk_pct=0.02, 
                capital=10000.0, 
                symbol="BTC/USDT"
            )
            
            # Should return None for both when response is malformed
            assert decision is None
            assert advice is None


if __name__ == "__main__":
    pytest.main([__file__])