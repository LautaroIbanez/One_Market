"""Tests for service.tp_sl_engine module."""
import pytest
import pandas as pd
import numpy as np
from app.service.tp_sl_engine import (
    TPSLConfig,
    calculate_tp_sl_atr,
    calculate_tp_sl_swing,
    calculate_tp_sl,
    find_swing_high,
    find_swing_low,
    adjust_stops_for_volatility
)


class TestTPSLConfig:
    """Tests for TP/SL configuration."""
    
    def test_config_defaults(self):
        """Test default configuration."""
        config = TPSLConfig()
        
        assert config.method == "atr"
        assert config.atr_period == 14
        assert config.atr_multiplier_sl == 2.0
        assert config.atr_multiplier_tp == 3.0
        assert config.min_rr_ratio == 1.5
    
    def test_config_custom(self):
        """Test custom configuration."""
        config = TPSLConfig(
            method="swing",
            atr_multiplier_sl=2.5,
            min_rr_ratio=2.0
        )
        
        assert config.method == "swing"
        assert config.atr_multiplier_sl == 2.5
        assert config.min_rr_ratio == 2.0


class TestSwingLevels:
    """Tests for swing high/low finding."""
    
    def test_find_swing_high(self):
        """Test finding swing high."""
        high = pd.Series([100, 102, 105, 103, 104, 101, 106, 104])
        
        swing = find_swing_high(high, lookback=5)
        
        # Should be max of last 5: 104, 101, 106, 104 -> 106
        assert swing >= 104
    
    def test_find_swing_low(self):
        """Test finding swing low."""
        low = pd.Series([100, 98, 95, 97, 96, 99, 94, 96])
        
        swing = find_swing_low(low, lookback=5)
        
        # Should be min of last 5
        assert swing <= 97


class TestATRMethod:
    """Tests for ATR-based TP/SL."""
    
    def test_calculate_tp_sl_atr_long(self):
        """Test ATR TP/SL for long."""
        # Create data with enough bars
        n_bars = 30
        df = pd.DataFrame({
            'high': np.random.randn(n_bars).cumsum() + 102,
            'low': np.random.randn(n_bars).cumsum() + 98,
            'close': np.random.randn(n_bars).cumsum() + 100
        })
        
        config = TPSLConfig()
        result = calculate_tp_sl_atr(df, entry_price=100.0, signal_direction=1, config=config)
        
        # Long: SL below entry, TP above
        assert result.stop_loss < 100.0
        assert result.take_profit > 100.0
        assert result.risk_reward_ratio >= config.min_rr_ratio
    
    def test_calculate_tp_sl_atr_short(self):
        """Test ATR TP/SL for short."""
        n_bars = 30
        df = pd.DataFrame({
            'high': np.random.randn(n_bars).cumsum() + 102,
            'low': np.random.randn(n_bars).cumsum() + 98,
            'close': np.random.randn(n_bars).cumsum() + 100
        })
        
        config = TPSLConfig()
        result = calculate_tp_sl_atr(df, entry_price=100.0, signal_direction=-1, config=config)
        
        # Short: SL above entry, TP below
        assert result.stop_loss > 100.0
        assert result.take_profit < 100.0


class TestSwingMethod:
    """Tests for swing-based TP/SL."""
    
    def test_calculate_tp_sl_swing_long(self):
        """Test swing TP/SL for long."""
        df = pd.DataFrame({
            'high': [102, 104, 103, 105, 104, 106, 105, 107],
            'low': [98, 100, 99, 101, 100, 102, 101, 103],
            'close': [100, 102, 101, 103, 102, 104, 103, 105]
        })
        
        # Extend to have enough data
        df = pd.concat([df] * 5, ignore_index=True)
        
        config = TPSLConfig(swing_lookback=10)
        result = calculate_tp_sl_swing(df, entry_price=105.0, signal_direction=1, config=config)
        
        # SL should be below swing low
        assert result.stop_loss < 105.0
        assert result.swing_level is not None


class TestCalculateTPSL:
    """Tests for main TP/SL calculation."""
    
    def test_calculate_tp_sl_default(self):
        """Test TP/SL with default config."""
        n_bars = 30
        df = pd.DataFrame({
            'high': np.random.randn(n_bars).cumsum() + 102,
            'low': np.random.randn(n_bars).cumsum() + 98,
            'close': np.random.randn(n_bars).cumsum() + 100
        })
        
        result = calculate_tp_sl(df, entry_price=100.0, signal_direction=1)
        
        assert result.stop_loss > 0
        assert result.take_profit > 0
        assert result.risk_reward_ratio > 0
    
    def test_calculate_tp_sl_swing_method(self):
        """Test TP/SL with swing method."""
        df = pd.DataFrame({
            'high': [102] * 30,
            'low': [98] * 30,
            'close': [100] * 30
        })
        
        config = TPSLConfig(method="swing")
        result = calculate_tp_sl(df, entry_price=100.0, signal_direction=1, config=config)
        
        assert result.method_used == "swing"


class TestVolatilityAdjustment:
    """Tests for volatility-based adjustment."""
    
    def test_adjust_stops_high_volatility(self):
        """Test widening stops in high volatility."""
        from app.service.tp_sl_engine import TPSLResult
        
        original = TPSLResult(
            stop_loss=98.0,
            take_profit=103.0,
            atr_value=1.0,
            risk_amount=2.0,
            reward_amount=3.0,
            risk_reward_ratio=1.5,
            stop_loss_pct=0.02,
            take_profit_pct=0.03,
            method_used="atr"
        )
        
        adjusted = adjust_stops_for_volatility(
            original,
            entry_price=100.0,
            volatility_regime="high",
            signal_direction=1
        )
        
        # Stops should be wider in high volatility
        assert abs(adjusted.stop_loss - 100.0) > abs(original.stop_loss - 100.0)

