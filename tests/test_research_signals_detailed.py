"""Tests for research.signals module."""
import pytest
import pandas as pd
import numpy as np
from app.research.signals import (
    ma_crossover,
    rsi_regime_pullback,
    donchian_breakout_adx,
    macd_histogram_atr_filter,
    mean_reversion,
    trend_following_ema,
    get_strategy_list,
    generate_signal
)


class TestSignalOutput:
    """Tests for signal output structure."""
    
    def test_signal_output_structure(self):
        """Test SignalOutput has required fields."""
        close = pd.Series(np.random.randn(100).cumsum() + 100)
        result = ma_crossover(close)
        
        assert hasattr(result, 'signal')
        assert hasattr(result, 'strength')
        assert hasattr(result, 'metadata')
    
    def test_signal_values(self):
        """Test signal only contains -1, 0, 1."""
        close = pd.Series(np.random.randn(100).cumsum() + 100)
        result = ma_crossover(close)
        
        unique_values = result.signal.unique()
        assert set(unique_values).issubset({-1, 0, 1})


class TestMACrossover:
    """Tests for MA Crossover strategy."""
    
    def test_ma_crossover_long_signal(self):
        """Test MA crossover generates long signal."""
        # Create uptrending data where fast > slow
        close = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110])
        result = ma_crossover(close, fast_period=3, slow_period=5)
        
        # Should have some long signals
        assert (result.signal == 1).any()
    
    def test_ma_crossover_short_signal(self):
        """Test MA crossover generates short signal."""
        # Create downtrending data
        close = pd.Series([110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100])
        result = ma_crossover(close, fast_period=3, slow_period=5)
        
        # Should have some short signals
        assert (result.signal == -1).any()
    
    def test_ma_crossover_long_disabled(self):
        """Test disabling long signals."""
        close = pd.Series([100, 101, 102, 103, 104, 105])
        result = ma_crossover(close, long_enabled=False)
        
        # Should have no long signals
        assert (result.signal == 1).sum() == 0
    
    def test_ma_crossover_short_disabled(self):
        """Test disabling short signals."""
        close = pd.Series([100, 99, 98, 97, 96, 95])
        result = ma_crossover(close, short_enabled=False)
        
        # Should have no short signals
        assert (result.signal == -1).sum() == 0


class TestRSIRegimePullback:
    """Tests for RSI Regime + Pullback strategy."""
    
    def test_rsi_regime_output(self):
        """Test RSI regime strategy output."""
        close = pd.Series(np.random.randn(100).cumsum() + 100)
        result = rsi_regime_pullback(close)
        
        assert len(result.signal) == len(close)
        assert result.metadata['strategy'] == 'rsi_regime_pullback'
    
    def test_rsi_regime_parameters(self):
        """Test RSI regime with custom parameters."""
        close = pd.Series(np.random.randn(100).cumsum() + 100)
        result = rsi_regime_pullback(
            close,
            rsi_period=10,
            oversold=25,
            overbought=75
        )
        
        assert result.metadata['rsi_period'] == 10
        assert result.metadata['oversold'] == 25
        assert result.metadata['overbought'] == 75


class TestDonchianBreakout:
    """Tests for Donchian Breakout + ADX strategy."""
    
    def test_donchian_breakout_output(self):
        """Test Donchian breakout output."""
        high = pd.Series(np.random.randn(100).cumsum() + 102)
        low = pd.Series(np.random.randn(100).cumsum() + 98)
        close = pd.Series(np.random.randn(100).cumsum() + 100)
        
        result = donchian_breakout_adx(high, low, close)
        
        assert len(result.signal) == len(close)
        assert result.metadata['strategy'] == 'donchian_breakout_adx'


class TestMACDHistogram:
    """Tests for MACD Histogram + ATR filter strategy."""
    
    def test_macd_histogram_output(self):
        """Test MACD histogram strategy output."""
        high = pd.Series(np.random.randn(100).cumsum() + 102)
        low = pd.Series(np.random.randn(100).cumsum() + 98)
        close = pd.Series(np.random.randn(100).cumsum() + 100)
        
        result = macd_histogram_atr_filter(high, low, close)
        
        assert len(result.signal) == len(close)
        assert result.metadata['strategy'] == 'macd_histogram_atr_filter'


class TestMeanReversion:
    """Tests for Mean Reversion strategy."""
    
    def test_mean_reversion_output(self):
        """Test mean reversion output."""
        close = pd.Series(np.random.randn(100).cumsum() + 100)
        result = mean_reversion(close)
        
        assert len(result.signal) == len(close)
        assert result.metadata['strategy'] == 'mean_reversion'


class TestTrendFollowingEMA:
    """Tests for Trend Following EMA strategy."""
    
    def test_trend_following_output(self):
        """Test trend following output."""
        close = pd.Series(np.random.randn(100).cumsum() + 100)
        result = trend_following_ema(close)
        
        assert len(result.signal) == len(close)
        assert result.metadata['strategy'] == 'trend_following_ema'


class TestStrategyFactory:
    """Tests for strategy factory functions."""
    
    def test_get_strategy_list(self):
        """Test getting strategy list."""
        strategies = get_strategy_list()
        
        assert isinstance(strategies, list)
        assert len(strategies) > 0
        assert 'ma_crossover' in strategies
        assert 'rsi_regime_pullback' in strategies
    
    def test_generate_signal_ma_crossover(self):
        """Test generating signal by name."""
        df = pd.DataFrame({
            'close': np.random.randn(50).cumsum() + 100,
            'high': np.random.randn(50).cumsum() + 102,
            'low': np.random.randn(50).cumsum() + 98
        })
        
        result = generate_signal('ma_crossover', df)
        
        assert len(result.signal) == len(df)
    
    def test_generate_signal_with_params(self):
        """Test generating signal with custom parameters."""
        df = pd.DataFrame({
            'close': np.random.randn(50).cumsum() + 100,
            'high': np.random.randn(50).cumsum() + 102,
            'low': np.random.randn(50).cumsum() + 98
        })
        
        params = {'fast_period': 5, 'slow_period': 10}
        result = generate_signal('ma_crossover', df, params)
        
        assert len(result.signal) == len(df)
    
    def test_generate_signal_invalid_strategy(self):
        """Test invalid strategy name raises error."""
        df = pd.DataFrame({
            'close': np.random.randn(50).cumsum() + 100,
            'high': np.random.randn(50).cumsum() + 102,
            'low': np.random.randn(50).cumsum() + 98
        })
        
        with pytest.raises(ValueError, match="Unknown strategy"):
            generate_signal('invalid_strategy', df)


class TestSignalSymmetry:
    """Tests for long/short symmetry."""
    
    def test_ma_crossover_symmetry(self):
        """Test MA crossover has symmetric long/short capability."""
        # Uptrend
        close_up = pd.Series(range(100, 120))
        result_up = ma_crossover(close_up, fast_period=3, slow_period=5)
        
        # Downtrend
        close_down = pd.Series(range(120, 100, -1))
        result_down = ma_crossover(close_down, fast_period=3, slow_period=5)
        
        # Both should have signals
        assert (result_up.signal != 0).any()
        assert (result_down.signal != 0).any()


class TestSignalContinuity:
    """Tests for signal continuity (no gaps)."""
    
    def test_signal_length_matches_input(self):
        """Test signal length matches input length."""
        close = pd.Series(np.random.randn(75).cumsum() + 100)
        result = ma_crossover(close)
        
        assert len(result.signal) == len(close)
        assert len(result.strength) == len(close)

