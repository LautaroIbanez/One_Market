"""Tests for service.entry_band module."""
import pytest
import pandas as pd
import numpy as np
from app.service.entry_band import (
    calculate_entry_mid_vwap,
    calculate_entry_mid_typical_price,
    calculate_entry_band,
    calculate_limit_order_price,
    validate_entry_price
)


class TestEntryMidCalculations:
    """Tests for entry mid calculations."""
    
    def test_calculate_entry_mid_typical_price(self):
        """Test typical price calculation."""
        df = pd.DataFrame({
            'high': [103],
            'low': [97],
            'close': [100]
        })
        
        result = calculate_entry_mid_typical_price(df)
        
        assert result == 100  # (103 + 97 + 100) / 3
    
    def test_calculate_entry_mid_vwap(self):
        """Test VWAP calculation."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2023-10-20 09:00', periods=5, freq='1H'),
            'high': [102, 104, 103, 105, 106],
            'low': [98, 100, 99, 101, 102],
            'close': [100, 102, 101, 103, 104],
            'volume': [1000, 1100, 1050, 1200, 1150]
        })
        
        result = calculate_entry_mid_vwap(df)
        
        # Should return a valid VWAP
        assert result is not None
        assert result > 0


class TestEntryBandCalculation:
    """Tests for entry band calculation."""
    
    def test_entry_band_long(self):
        """Test entry band for long signal."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2023-10-20', periods=10, freq='1H'),
            'high': [102] * 10,
            'low': [98] * 10,
            'close': [100] * 10,
            'volume': [1000] * 10
        })
        
        result = calculate_entry_band(
            df,
            current_price=100.0,
            signal_direction=1,  # Long
            beta=0.005,  # 0.5%
            use_vwap=False
        )
        
        # Long should aim below mid
        assert result.entry_price < result.entry_mid
        assert result.method == "typical_price"
    
    def test_entry_band_short(self):
        """Test entry band for short signal."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2023-10-20', periods=10, freq='1H'),
            'high': [102] * 10,
            'low': [98] * 10,
            'close': [100] * 10,
            'volume': [1000] * 10
        })
        
        result = calculate_entry_band(
            df,
            current_price=100.0,
            signal_direction=-1,  # Short
            beta=0.005,
            use_vwap=False
        )
        
        # Short should aim above mid
        assert result.entry_price > result.entry_mid
    
    def test_entry_band_beta_zero(self):
        """Test entry band with zero beta."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2023-10-20', periods=10, freq='1H'),
            'high': [102] * 10,
            'low': [98] * 10,
            'close': [100] * 10,
            'volume': [1000] * 10
        })
        
        result = calculate_entry_band(
            df,
            current_price=100.0,
            signal_direction=1,
            beta=0.0,
            use_vwap=False
        )
        
        # With beta=0, entry should equal mid
        assert result.entry_price == result.entry_mid


class TestLimitOrderPrice:
    """Tests for limit order price calculation."""
    
    def test_limit_order_long(self):
        """Test limit order for long."""
        limit_price = calculate_limit_order_price(
            entry_price=50000.0,
            signal_direction=1,
            tick_size=0.01,
            improve_by_ticks=10
        )
        
        # Should be below entry for long (better price)
        assert limit_price < 50000.0
        assert limit_price == 49999.9  # 50000 - (10 * 0.01)
    
    def test_limit_order_short(self):
        """Test limit order for short."""
        limit_price = calculate_limit_order_price(
            entry_price=50000.0,
            signal_direction=-1,
            tick_size=0.01,
            improve_by_ticks=10
        )
        
        # Should be above entry for short (better price)
        assert limit_price > 50000.0
        assert limit_price == 50000.1  # 50000 + (10 * 0.01)


class TestEntryPriceValidation:
    """Tests for entry price validation."""
    
    def test_validate_entry_price_valid(self):
        """Test valid entry price."""
        is_valid, msg = validate_entry_price(
            entry_price=50000.0,
            current_price=50050.0,
            signal_direction=1,
            max_slippage_pct=0.01
        )
        
        assert is_valid is True
        assert msg == ""
    
    def test_validate_entry_price_too_far(self):
        """Test entry price too far from market."""
        is_valid, msg = validate_entry_price(
            entry_price=49000.0,
            current_price=50000.0,
            signal_direction=1,
            max_slippage_pct=0.01
        )
        
        assert is_valid is False
        assert "too far" in msg
    
    def test_validate_entry_price_negative(self):
        """Test negative entry price fails."""
        is_valid, msg = validate_entry_price(
            entry_price=-100.0,
            current_price=50000.0,
            signal_direction=1
        )
        
        assert is_valid is False
        assert "must be positive" in msg

