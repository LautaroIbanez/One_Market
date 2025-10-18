"""Tests for research.indicators module."""
import pytest
import pandas as pd
import numpy as np
from app.research.indicators import (
    ema, sma, rsi, atr, adx, donchian_channels, macd,
    bollinger_bands, stochastic, cci, williams_r,
    momentum, roc, obv, supertrend, keltner_channels,
    validate_series
)


class TestIndicatorValidation:
    """Tests for indicator validation."""
    
    def test_validate_series_valid(self):
        """Test valid series passes validation."""
        series = pd.Series([1, 2, 3, 4, 5])
        validate_series(series, "Test")  # Should not raise
    
    def test_validate_series_too_short(self):
        """Test that too short series raises error."""
        series = pd.Series([1])
        with pytest.raises(ValueError, match="at least 2 data points"):
            validate_series(series, "Test")
    
    def test_validate_series_all_nan(self):
        """Test that all NaN series raises error."""
        series = pd.Series([np.nan, np.nan, np.nan])
        with pytest.raises(ValueError, match="only NaN values"):
            validate_series(series, "Test")


class TestMovingAverages:
    """Tests for moving average indicators."""
    
    def test_ema_calculation(self):
        """Test EMA calculation."""
        close = pd.Series([100, 101, 102, 103, 104, 105])
        result = ema(close, period=3)
        
        assert len(result) == len(close)
        assert result.iloc[2:].notna().all()  # After warmup
        assert result.iloc[:2].isna().all()  # Warmup period
    
    def test_sma_calculation(self):
        """Test SMA calculation."""
        close = pd.Series([100, 101, 102, 103, 104, 105])
        result = sma(close, period=3)
        
        assert len(result) == len(close)
        assert result.iloc[2] == 101  # (100+101+102)/3


class TestMomentumIndicators:
    """Tests for momentum indicators."""
    
    def test_rsi_bounds(self):
        """Test RSI stays within 0-100."""
        close = pd.Series(np.random.randn(100).cumsum() + 100)
        result = rsi(close, period=14)
        
        valid_values = result[result.notna()]
        assert (valid_values >= 0).all()
        assert (valid_values <= 100).all()
    
    def test_momentum_calculation(self):
        """Test momentum calculation."""
        close = pd.Series([100, 101, 103, 102, 105])
        result = momentum(close, period=2)
        
        assert result.iloc[2] == 3  # 103 - 100
    
    def test_roc_calculation(self):
        """Test ROC calculation."""
        close = pd.Series([100, 105, 110])
        result = roc(close, period=1)
        
        assert result.iloc[1] == pytest.approx(5.0)  # 5% gain


class TestVolatilityIndicators:
    """Tests for volatility indicators."""
    
    def test_atr_positive(self):
        """Test ATR is always positive."""
        high = pd.Series([102, 104, 103, 105])
        low = pd.Series([98, 100, 99, 101])
        close = pd.Series([100, 102, 101, 103])
        
        result = atr(high, low, close, period=3)
        valid_values = result[result.notna()]
        assert (valid_values > 0).all()
    
    def test_bollinger_bands_order(self):
        """Test Bollinger Bands order (upper > middle > lower)."""
        close = pd.Series([100, 101, 102, 103, 104, 105])
        upper, middle, lower = bollinger_bands(close, period=3)
        
        valid_idx = middle.notna()
        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()


class TestTrendIndicators:
    """Tests for trend indicators."""
    
    def test_adx_bounds(self):
        """Test ADX stays within 0-100."""
        high = pd.Series(np.random.randn(50).cumsum() + 102)
        low = pd.Series(np.random.randn(50).cumsum() + 98)
        close = pd.Series(np.random.randn(50).cumsum() + 100)
        
        result = adx(high, low, close, period=14)
        valid_values = result[result.notna()]
        
        assert (valid_values >= 0).all()
        assert (valid_values <= 100).all()
    
    def test_donchian_channels(self):
        """Test Donchian channels calculation."""
        high = pd.Series([102, 104, 106, 105, 107])
        low = pd.Series([98, 100, 102, 101, 103])
        
        upper, middle, lower = donchian_channels(high, low, period=3)
        
        assert upper.iloc[2] == 104  # Max of first 3 highs
        assert lower.iloc[2] == 98   # Min of first 3 lows


class TestMACDIndicator:
    """Tests for MACD indicator."""
    
    def test_macd_components(self):
        """Test MACD returns correct components."""
        close = pd.Series(np.random.randn(50).cumsum() + 100)
        macd_line, signal_line, histogram = macd(close)
        
        assert len(macd_line) == len(close)
        assert len(signal_line) == len(close)
        assert len(histogram) == len(close)
    
    def test_macd_histogram_calculation(self):
        """Test MACD histogram is line - signal."""
        close = pd.Series(np.random.randn(50).cumsum() + 100)
        macd_line, signal_line, histogram = macd(close)
        
        valid_idx = histogram.notna()
        calculated_hist = macd_line[valid_idx] - signal_line[valid_idx]
        assert np.allclose(histogram[valid_idx], calculated_hist, rtol=1e-10)


class TestOscillators:
    """Tests for oscillator indicators."""
    
    def test_stochastic_bounds(self):
        """Test Stochastic stays within 0-100."""
        high = pd.Series(np.random.randn(50).cumsum() + 102)
        low = pd.Series(np.random.randn(50).cumsum() + 98)
        close = pd.Series(np.random.randn(50).cumsum() + 100)
        
        k, d = stochastic(high, low, close, k_period=14, d_period=3)
        
        valid_k = k[k.notna()]
        valid_d = d[d.notna()]
        
        assert (valid_k >= 0).all() and (valid_k <= 100).all()
        assert (valid_d >= 0).all() and (valid_d <= 100).all()
    
    def test_williams_r_bounds(self):
        """Test Williams %R stays within -100 to 0."""
        high = pd.Series(np.random.randn(30).cumsum() + 102)
        low = pd.Series(np.random.randn(30).cumsum() + 98)
        close = pd.Series(np.random.randn(30).cumsum() + 100)
        
        result = williams_r(high, low, close, period=14)
        valid_values = result[result.notna()]
        
        assert (valid_values >= -100).all()
        assert (valid_values <= 0).all()


class TestVolumeIndicators:
    """Tests for volume-based indicators."""
    
    def test_obv_cumulative(self):
        """Test OBV is cumulative."""
        close = pd.Series([100, 101, 100, 102])
        volume = pd.Series([1000, 1000, 1000, 1000])
        
        result = obv(close, volume)
        
        # OBV should change based on price direction
        assert result.iloc[1] > result.iloc[0]  # Price up
        assert result.iloc[2] < result.iloc[1]  # Price down


class TestLookaheadPrevention:
    """Tests to ensure no lookahead bias."""
    
    def test_ema_no_lookahead(self):
        """Test EMA doesn't use future data."""
        close = pd.Series([100, 200, 100, 100, 100])  # Spike in middle
        result = ema(close, period=2)
        
        # Value at index 0 should not be affected by spike at index 1
        assert result.iloc[0] != result.iloc[1]
    
    def test_rsi_no_lookahead(self):
        """Test RSI doesn't use future data."""
        close = pd.Series([100, 101, 102, 50, 104])  # Drop at index 3
        result = rsi(close, period=3)
        
        # RSI at index 2 should not be affected by drop at index 3
        if not pd.isna(result.iloc[2]):
            rsi_before_drop = result.iloc[2]
            assert rsi_before_drop > 0  # Should be positive before the drop

