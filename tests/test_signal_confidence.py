"""Tests for signal confidence rescaling and UI display."""
import pytest
import pandas as pd
import numpy as np
from app.research.combine import simple_average, CombinedSignal


class TestSignalConfidence:
    """Test signal confidence rescaling and metadata."""
    
    def test_simple_average_confidence_scale(self):
        """Test that confidence is properly scaled to 0-1 range."""
        # Create test signals
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        
        # Test case 1: All strategies agree (high confidence)
        signals_agree = {
            'strategy1': pd.Series([1, 1, 1, 1, 1, -1, -1, -1, -1, -1], index=dates),
            'strategy2': pd.Series([1, 1, 1, 1, 1, -1, -1, -1, -1, -1], index=dates),
            'strategy3': pd.Series([1, 1, 1, 1, 1, -1, -1, -1, -1, -1], index=dates)
        }
        
        result = simple_average(signals_agree)
        
        # All strategies agree, so confidence should be 1.0
        assert result.confidence.iloc[0] == 1.0  # All long
        assert result.confidence.iloc[5] == 1.0  # All short
        
        # Test case 2: Strategies disagree (low confidence)
        signals_disagree = {
            'strategy1': pd.Series([1, 1, 1, 1, 1, -1, -1, -1, -1, -1], index=dates),
            'strategy2': pd.Series([-1, -1, -1, -1, -1, 1, 1, 1, 1, 1], index=dates),
            'strategy3': pd.Series([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], index=dates)
        }
        
        result = simple_average(signals_disagree)
        
        # Strategies disagree, so confidence should be lower
        # Average of [1, -1, 0] = 0, so confidence = abs(0) = 0
        assert result.confidence.iloc[0] == 0.0  # No consensus
        assert result.confidence.iloc[5] == 0.0  # No consensus
        
        # Test case 3: Mixed agreement (medium confidence)
        signals_mixed = {
            'strategy1': pd.Series([1, 1, 1, 1, 1, -1, -1, -1, -1, -1], index=dates),
            'strategy2': pd.Series([1, 1, 1, 1, 1, -1, -1, -1, -1, -1], index=dates),
            'strategy3': pd.Series([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], index=dates)
        }
        
        result = simple_average(signals_mixed)
        
        # 2 out of 3 strategies agree
        assert result.confidence.iloc[0] == 2/3  # 2 strategies out of 3
        assert result.confidence.iloc[5] == 2/3  # 2 strategies out of 3
    
    def test_confidence_metadata(self):
        """Test that confidence metadata includes strategy count."""
        dates = pd.date_range('2023-01-01', periods=5, freq='D')
        
        signals = {
            'strategy1': pd.Series([1, 1, -1, -1, 0], index=dates),
            'strategy2': pd.Series([1, -1, -1, 1, 0], index=dates),
            'strategy3': pd.Series([1, 1, 1, -1, 0], index=dates)
        }
        
        result = simple_average(signals)
        
        # Check metadata
        assert 'num_strategies' in result.metadata
        assert result.metadata['num_strategies'] == 3
        assert result.metadata['method'] == 'simple_average'
        
        # Check weights
        assert len(result.weights) == 3
        for weight in result.weights.values():
            assert abs(weight - 1/3) < 1e-6  # Equal weights
    
    def test_confidence_range(self):
        """Test that confidence values are always in valid range."""
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        
        # Test various signal combinations
        test_cases = [
            # All strategies agree
            {
                'strategy1': pd.Series([1] * 10, index=dates),
                'strategy2': pd.Series([1] * 10, index=dates),
                'strategy3': pd.Series([1] * 10, index=dates)
            },
            # All strategies disagree
            {
                'strategy1': pd.Series([1, -1, 1, -1, 1, -1, 1, -1, 1, -1], index=dates),
                'strategy2': pd.Series([-1, 1, -1, 1, -1, 1, -1, 1, -1, 1], index=dates),
                'strategy3': pd.Series([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], index=dates)
            },
            # Single strategy
            {
                'strategy1': pd.Series([1, -1, 1, -1, 1, -1, 1, -1, 1, -1], index=dates)
            }
        ]
        
        for signals in test_cases:
            result = simple_average(signals)
            
            # All confidence values should be in [0, 1]
            assert (result.confidence >= 0).all()
            assert (result.confidence <= 1).all()
            
            # Check that confidence is finite
            assert result.confidence.notna().all()
    
    def test_ui_tooltip_calculation(self):
        """Test the logic for UI tooltip calculation."""
        dates = pd.date_range('2023-01-01', periods=3, freq='D')
        
        # Create a test combined signal
        signals = {
            'strategy1': pd.Series([1, -1, 0], index=dates),
            'strategy2': pd.Series([1, -1, 0], index=dates),
            'strategy3': pd.Series([1, 0, 0], index=dates)
        }
        
        result = simple_average(signals)
        
        # Test tooltip calculation logic
        confidence = float(result.confidence.iloc[0])  # 1.0 (all agree)
        signal_value = int(result.signal.iloc[0])      # 1 (long)
        num_strategies = result.metadata.get('num_strategies', 0)  # 3
        
        # Calculate strategies in favor
        if signal_value != 0:
            strategies_favor = int(confidence * num_strategies)
            assert strategies_favor == 3  # All 3 strategies favor long
            tooltip = f"Estrategias a favor: {strategies_favor}/{num_strategies}"
            assert tooltip == "Estrategias a favor: 3/3"
        
        # Test flat signal case
        confidence_flat = float(result.confidence.iloc[2])  # 0.0 (flat)
        signal_value_flat = int(result.signal.iloc[2])      # 0 (flat)
        
        if signal_value_flat == 0:
            tooltip = f"Total estrategias: {num_strategies}"
            assert tooltip == "Total estrategias: 3"


if __name__ == "__main__":
    pytest.main([__file__])
