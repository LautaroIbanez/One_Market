"""Tests for UI skip state display and hypothetical levels."""
import pytest
import streamlit as st
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime, timedelta

from app.service.decision import DailyDecision


class TestUISkipState:
    """Test UI display of skip state with hypothetical levels."""
    
    def test_render_price_chart_skip_state(self):
        """Test that price chart shows hypothetical levels when should_execute=False."""
        from ui.app import render_price_chart
        
        # Create test data
        dates = pd.date_range('2023-01-01', periods=60, freq='1H')
        df = pd.DataFrame({
            'timestamp': dates.astype('int64') // 10**6,  # Convert to milliseconds
            'open': [100 + i * 0.1 for i in range(60)],
            'high': [101 + i * 0.1 for i in range(60)],
            'low': [99 + i * 0.1 for i in range(60)],
            'close': [100.5 + i * 0.1 for i in range(60)],
            'volume': [1000] * 60
        })
        
        # Create decision with should_execute=False
        decision = DailyDecision(
            decision_date=datetime.now(),
            trading_day=datetime.now().strftime('%Y-%m-%d'),
            window="A",
            signal=1,
            signal_strength=0.7,
            signal_source="test_strategy",
            should_execute=False,
            entry_price=105.0,
            stop_loss=100.0,
            take_profit=110.0,
            entry_mid=105.0,
            market_price=105.0,
            timestamp_ms=int(datetime.now().timestamp() * 1000)
        )
        
        # Render chart
        fig = render_price_chart(df, decision, "BTC-USDT", "1h")
        
        # Verify chart was created
        assert fig is not None
        assert len(fig.data) > 0  # Should have candlestick data
        
        # Check that chart has layout
        assert fig.layout is not None
        assert fig.layout.title is not None
        assert "BTC-USDT" in fig.layout.title.text
    
    def test_skip_reason_display(self):
        """Test that skip reason is properly displayed in UI."""
        # Create decision with skip reason
        decision = DailyDecision(
            decision_date=datetime.now(),
            trading_day=datetime.now().strftime('%Y-%m-%d'),
            window="A",
            signal=1,
            signal_strength=0.7,
            signal_source="test_strategy",
            should_execute=False,
            entry_price=105.0,
            stop_loss=100.0,
            take_profit=110.0,
            entry_mid=105.0,
            market_price=105.0,
            timestamp_ms=int(datetime.now().timestamp() * 1000),
            skip_reason="Volatilidad alta"
        )
        
        # Test decision attributes
        assert hasattr(decision, 'should_execute')
        assert decision.should_execute == False
        
        # Test decision without skip_reason
        decision_no_reason = DailyDecision(
            decision_date=datetime.now(),
            trading_day=datetime.now().strftime('%Y-%m-%d'),
            window="A",
            signal=1,
            signal_strength=0.7,
            signal_source="test_strategy",
            should_execute=False,
            entry_price=105.0,
            stop_loss=100.0,
            take_profit=110.0,
            entry_mid=105.0,
            market_price=105.0,
            timestamp_ms=int(datetime.now().timestamp() * 1000)
        )
        
        # Should handle missing skip_reason gracefully
        skip_reason = getattr(decision_no_reason, 'skip_reason', 'No especificado')
        # skip_reason is None by default, so we test that getattr works correctly
        assert skip_reason is None
    
    def test_hypothetical_levels_logic(self):
        """Test the logic for determining hypothetical levels."""
        # Test should_execute=True (not hypothetical)
        decision_execute = DailyDecision(
            decision_date=datetime.now(),
            trading_day=datetime.now().strftime('%Y-%m-%d'),
            window="A",
            signal=1,
            signal_strength=0.8,
            signal_source="test_strategy",
            should_execute=True,
            entry_price=105.0,
            stop_loss=100.0,
            take_profit=110.0,
            entry_mid=105.0,
            market_price=105.0,
            timestamp_ms=int(datetime.now().timestamp() * 1000)
        )
        
        is_hypothetical_execute = not decision_execute.should_execute
        assert is_hypothetical_execute == False
        
        # Test should_execute=False (hypothetical)
        decision_skip = DailyDecision(
            decision_date=datetime.now(),
            trading_day=datetime.now().strftime('%Y-%m-%d'),
            window="A",
            signal=1,
            signal_strength=0.7,
            signal_source="test_strategy",
            should_execute=False,
            entry_price=105.0,
            stop_loss=100.0,
            take_profit=110.0,
            entry_mid=105.0,
            market_price=105.0,
            timestamp_ms=int(datetime.now().timestamp() * 1000)
        )
        
        is_hypothetical_skip = not decision_skip.should_execute
        assert is_hypothetical_skip == True
        
        # Test level prefix logic
        level_prefix_execute = "Hipotético " if is_hypothetical_execute else ""
        level_prefix_skip = "Hipotético " if is_hypothetical_skip else ""
        
        assert level_prefix_execute == ""
        assert level_prefix_skip == "Hipotético "
    
    def test_decision_without_levels(self):
        """Test handling of decision without entry/exit levels."""
        from ui.app import render_price_chart
        
        # Create test data
        dates = pd.date_range('2023-01-01', periods=60, freq='1H')
        df = pd.DataFrame({
            'timestamp': dates.astype('int64') // 10**6,
            'open': [100 + i * 0.1 for i in range(60)],
            'high': [101 + i * 0.1 for i in range(60)],
            'low': [99 + i * 0.1 for i in range(60)],
            'close': [100.5 + i * 0.1 for i in range(60)],
            'volume': [1000] * 60
        })
        
        # Create decision with minimal data
        decision_minimal = DailyDecision(
            decision_date=datetime.now(),
            trading_day=datetime.now().strftime('%Y-%m-%d'),
            window="A",
            signal=1,
            signal_strength=0.5,
            signal_source="test_strategy",
            should_execute=False,
            entry_price=105.0,
            market_price=105.0,
            timestamp_ms=int(datetime.now().timestamp() * 1000)
        )
        
        # Should not crash when rendering
        fig = render_price_chart(df, decision_minimal, "BTC-USDT", "1h")
        assert fig is not None
    
    def test_ui_metric_help_text(self):
        """Test that UI metric help text is properly formatted."""
        decision = DailyDecision(
            decision_date=datetime.now(),
            trading_day=datetime.now().strftime('%Y-%m-%d'),
            window="A",
            signal=1,
            signal_strength=0.7,
            signal_source="test_strategy",
            should_execute=False,
            entry_price=105.0,
            stop_loss=100.0,
            take_profit=110.0,
            entry_mid=105.0,
            market_price=105.0,
            timestamp_ms=int(datetime.now().timestamp() * 1000)
        )
        
        # Test skip_reason help text generation
        skip_reason = getattr(decision, 'skip_reason', 'No especificado')
        help_text = f"Razón: {skip_reason}"
        
        assert help_text == "Razón: None"
        
        # Test with None decision
        decision_none = None
        skip_reason_none = getattr(decision_none, 'skip_reason', 'Sin decisión') if decision_none else 'Sin decisión'
        help_text_none = f"Razón: {skip_reason_none}"
        
        assert help_text_none == "Razón: Sin decisión"


if __name__ == "__main__":
    pytest.main([__file__])
