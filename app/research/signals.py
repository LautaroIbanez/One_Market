"""Atomic trading signal strategies.

This module provides modular, tuneable trading strategies that generate
entry/exit signals. All strategies support both long and short positions
and output normalized signals.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from app.research.indicators import (
    sma, ema, rsi, atr, adx, donchian_channels, macd, validate_series
)


class SignalOutput(BaseModel):
    """Standardized signal output."""
    
    signal: pd.Series = Field(..., description="Signal series: 1 (long), -1 (short), 0 (flat)")
    strength: Optional[pd.Series] = Field(None, description="Optional continuous signal strength")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Strategy metadata")
    
    class Config:
        arbitrary_types_allowed = True


class StrategyConfig(BaseModel):
    """Base configuration for strategies."""
    
    name: str = Field(..., description="Strategy name")
    long_enabled: bool = Field(default=True, description="Enable long signals")
    short_enabled: bool = Field(default=True, description="Enable short signals")
    output_mode: Literal["discrete", "continuous"] = Field(default="discrete", description="Output signal mode")


def ma_crossover(
    close: pd.Series,
    fast_period: int = 10,
    slow_period: int = 20,
    ma_type: Literal["sma", "ema"] = "ema",
    long_enabled: bool = True,
    short_enabled: bool = True
) -> SignalOutput:
    """Moving Average Crossover strategy.
    
    Generates signals when fast MA crosses slow MA.
    - Long: Fast MA crosses above slow MA
    - Short: Fast MA crosses below slow MA
    
    Args:
        close: Close price series
        fast_period: Fast MA period
        slow_period: Slow MA period
        ma_type: Type of MA ('sma' or 'ema')
        long_enabled: Enable long signals
        short_enabled: Enable short signals
        
    Returns:
        SignalOutput with signals
    """
    validate_series(close, "Close price")
    
    # Calculate MAs
    if ma_type == "sma":
        fast_ma = sma(close, fast_period)
        slow_ma = sma(close, slow_period)
    else:
        fast_ma = ema(close, fast_period)
        slow_ma = ema(close, slow_period)
    
    # Calculate crossover
    signal = pd.Series(0, index=close.index)
    
    # Long signal: fast > slow
    if long_enabled:
        signal[(fast_ma > slow_ma)] = 1
    
    # Short signal: fast < slow
    if short_enabled:
        signal[(fast_ma < slow_ma)] = -1
    
    # Calculate continuous strength (normalized distance)
    strength = (fast_ma - slow_ma) / slow_ma * 100
    
    return SignalOutput(
        signal=signal,
        strength=strength,
        metadata={
            "strategy": "ma_crossover",
            "fast_period": fast_period,
            "slow_period": slow_period,
            "ma_type": ma_type
        }
    )


def rsi_regime_pullback(
    close: pd.Series,
    rsi_period: int = 14,
    oversold: float = 30,
    overbought: float = 70,
    regime_period: int = 50,
    long_enabled: bool = True,
    short_enabled: bool = True
) -> SignalOutput:
    """RSI Regime + Pullback strategy.
    
    Identifies market regime using longer-term MA, then trades pullbacks using RSI.
    - Long: In uptrend (price > MA) + RSI oversold bounce
    - Short: In downtrend (price < MA) + RSI overbought rejection
    
    Args:
        close: Close price series
        rsi_period: RSI period
        oversold: RSI oversold level
        overbought: RSI overbought level
        regime_period: Period for regime identification
        long_enabled: Enable long signals
        short_enabled: Enable short signals
        
    Returns:
        SignalOutput with signals
    """
    validate_series(close, "Close price")
    
    # Calculate RSI
    rsi_val = rsi(close, rsi_period)
    
    # Calculate regime (using EMA)
    regime_ma = ema(close, regime_period)
    
    # Initialize signal
    signal = pd.Series(0, index=close.index)
    
    # Long: uptrend + RSI bouncing from oversold
    if long_enabled:
        uptrend = close > regime_ma
        rsi_bounce = (rsi_val > oversold) & (rsi_val.shift(1) <= oversold)
        signal[uptrend & rsi_bounce] = 1
        
        # Hold long while in uptrend and RSI not overbought
        in_long = signal.shift(1) == 1
        hold_long = uptrend & (rsi_val < overbought)
        signal[in_long & hold_long] = 1
    
    # Short: downtrend + RSI rejecting from overbought
    if short_enabled:
        downtrend = close < regime_ma
        rsi_reject = (rsi_val < overbought) & (rsi_val.shift(1) >= overbought)
        signal[downtrend & rsi_reject] = -1
        
        # Hold short while in downtrend and RSI not oversold
        in_short = signal.shift(1) == -1
        hold_short = downtrend & (rsi_val > oversold)
        signal[in_short & hold_short] = -1
    
    # Calculate strength (distance from neutral RSI 50)
    strength = (rsi_val - 50) / 50
    
    return SignalOutput(
        signal=signal,
        strength=strength,
        metadata={
            "strategy": "rsi_regime_pullback",
            "rsi_period": rsi_period,
            "oversold": oversold,
            "overbought": overbought,
            "regime_period": regime_period
        }
    )


def donchian_breakout_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    donchian_period: int = 20,
    adx_period: int = 14,
    adx_threshold: float = 25,
    long_enabled: bool = True,
    short_enabled: bool = True
) -> SignalOutput:
    """Donchian Breakout with ADX filter.
    
    Trades breakouts of Donchian channels when trend is strong (ADX > threshold).
    - Long: Price breaks above upper band + ADX > threshold
    - Short: Price breaks below lower band + ADX > threshold
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        donchian_period: Donchian channel period
        adx_period: ADX period
        adx_threshold: Minimum ADX for trend confirmation
        long_enabled: Enable long signals
        short_enabled: Enable short signals
        
    Returns:
        SignalOutput with signals
    """
    validate_series(close, "Close price")
    
    # Calculate Donchian channels
    upper_band, middle_band, lower_band = donchian_channels(high, low, donchian_period)
    
    # Calculate ADX
    adx_val = adx(high, low, close, adx_period)
    
    # Initialize signal
    signal = pd.Series(0, index=close.index)
    
    # Strong trend filter
    strong_trend = adx_val > adx_threshold
    
    # Long: break above upper band + strong trend
    if long_enabled:
        breakout_long = (close > upper_band) & (close.shift(1) <= upper_band.shift(1))
        signal[breakout_long & strong_trend] = 1
        
        # Hold long while above middle band
        in_long = signal.shift(1) == 1
        hold_long = close > middle_band
        signal[in_long & hold_long] = 1
    
    # Short: break below lower band + strong trend
    if short_enabled:
        breakout_short = (close < lower_band) & (close.shift(1) >= lower_band.shift(1))
        signal[breakout_short & strong_trend] = -1
        
        # Hold short while below middle band
        in_short = signal.shift(1) == -1
        hold_short = close < middle_band
        signal[in_short & hold_short] = -1
    
    # Calculate strength (distance from middle band, weighted by ADX)
    distance_from_mid = (close - middle_band) / middle_band
    strength = distance_from_mid * (adx_val / 100)
    
    return SignalOutput(
        signal=signal,
        strength=strength,
        metadata={
            "strategy": "donchian_breakout_adx",
            "donchian_period": donchian_period,
            "adx_period": adx_period,
            "adx_threshold": adx_threshold
        }
    )


def macd_histogram_atr_filter(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
    atr_period: int = 14,
    atr_multiplier: float = 1.5,
    long_enabled: bool = True,
    short_enabled: bool = True
) -> SignalOutput:
    """MACD Histogram slope with ATR filter.
    
    Trades MACD histogram slope changes when volatility is adequate (ATR filter).
    - Long: MACD histogram turning up + ATR > threshold
    - Short: MACD histogram turning down + ATR > threshold
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        fast: MACD fast period
        slow: MACD slow period
        signal_period: MACD signal period
        atr_period: ATR period
        atr_multiplier: ATR multiplier for minimum volatility
        long_enabled: Enable long signals
        short_enabled: Enable short signals
        
    Returns:
        SignalOutput with signals
    """
    validate_series(close, "Close price")
    
    # Calculate MACD
    macd_line, signal_line, histogram = macd(close, fast, slow, signal_period)
    
    # Calculate ATR
    atr_val = atr(high, low, close, atr_period)
    
    # Calculate ATR as percentage of price
    atr_pct = (atr_val / close) * 100
    
    # Historical average ATR%
    atr_pct_ma = atr_pct.rolling(window=50, min_periods=20).mean()
    
    # Volatility filter: current ATR% should be above threshold
    sufficient_vol = atr_pct > (atr_pct_ma * atr_multiplier)
    
    # Calculate histogram slope
    hist_slope = histogram - histogram.shift(1)
    
    # Initialize signal
    signal = pd.Series(0, index=close.index)
    
    # Long: histogram turning up + sufficient volatility
    if long_enabled:
        hist_up = (hist_slope > 0) & (hist_slope.shift(1) <= 0)
        macd_positive = macd_line > signal_line
        signal[hist_up & sufficient_vol & macd_positive] = 1
        
        # Hold long while histogram positive
        in_long = signal.shift(1) == 1
        hold_long = histogram > 0
        signal[in_long & hold_long] = 1
    
    # Short: histogram turning down + sufficient volatility
    if short_enabled:
        hist_down = (hist_slope < 0) & (hist_slope.shift(1) >= 0)
        macd_negative = macd_line < signal_line
        signal[hist_down & sufficient_vol & macd_negative] = -1
        
        # Hold short while histogram negative
        in_short = signal.shift(1) == -1
        hold_short = histogram < 0
        signal[in_short & hold_short] = -1
    
    # Calculate strength (normalized histogram)
    strength = histogram / atr_val
    
    return SignalOutput(
        signal=signal,
        strength=strength,
        metadata={
            "strategy": "macd_histogram_atr_filter",
            "fast": fast,
            "slow": slow,
            "signal_period": signal_period,
            "atr_period": atr_period,
            "atr_multiplier": atr_multiplier
        }
    )


def mean_reversion(
    close: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
    long_enabled: bool = True,
    short_enabled: bool = True
) -> SignalOutput:
    """Mean reversion strategy using Bollinger Bands.
    
    Trades mean reversion when price reaches extreme levels.
    - Long: Price touches lower band, expecting bounce
    - Short: Price touches upper band, expecting pullback
    
    Args:
        close: Close price series
        period: Bollinger Band period
        std_dev: Number of standard deviations
        long_enabled: Enable long signals
        short_enabled: Enable short signals
        
    Returns:
        SignalOutput with signals
    """
    validate_series(close, "Close price")
    
    from app.research.indicators import bollinger_bands
    
    # Calculate Bollinger Bands
    upper_band, middle_band, lower_band = bollinger_bands(close, period, std_dev)
    
    # Initialize signal
    signal = pd.Series(0, index=close.index)
    
    # Long: price at or below lower band
    if long_enabled:
        at_lower_band = close <= lower_band
        signal[at_lower_band] = 1
        
        # Exit when price crosses above middle band
        in_long = signal.shift(1) == 1
        above_mid = close > middle_band
        signal[in_long & above_mid] = 0
    
    # Short: price at or above upper band
    if short_enabled:
        at_upper_band = close >= upper_band
        signal[at_upper_band] = -1
        
        # Exit when price crosses below middle band
        in_short = signal.shift(1) == -1
        below_mid = close < middle_band
        signal[in_short & below_mid] = 0
    
    # Calculate strength (distance from middle band in standard deviations)
    band_width = upper_band - lower_band
    strength = (close - middle_band) / (band_width / 2)
    
    return SignalOutput(
        signal=signal,
        strength=strength,
        metadata={
            "strategy": "mean_reversion",
            "period": period,
            "std_dev": std_dev
        }
    )


def trend_following_ema(
    close: pd.Series,
    fast_period: int = 8,
    slow_period: int = 21,
    trend_period: int = 50,
    long_enabled: bool = True,
    short_enabled: bool = True
) -> SignalOutput:
    """Trend following strategy with multiple EMAs.
    
    Uses fast/slow EMA crossover confirmed by longer-term trend.
    - Long: Fast > Slow > Trend EMA
    - Short: Fast < Slow < Trend EMA
    
    Args:
        close: Close price series
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        trend_period: Trend EMA period
        long_enabled: Enable long signals
        short_enabled: Enable short signals
        
    Returns:
        SignalOutput with signals
    """
    validate_series(close, "Close price")
    
    # Calculate EMAs
    fast_ema = ema(close, fast_period)
    slow_ema = ema(close, slow_period)
    trend_ema = ema(close, trend_period)
    
    # Initialize signal
    signal = pd.Series(0, index=close.index)
    
    # Long: fast > slow > trend
    if long_enabled:
        aligned_long = (fast_ema > slow_ema) & (slow_ema > trend_ema)
        signal[aligned_long] = 1
    
    # Short: fast < slow < trend
    if short_enabled:
        aligned_short = (fast_ema < slow_ema) & (slow_ema < trend_ema)
        signal[aligned_short] = -1
    
    # Calculate strength (alignment strength)
    fast_slow_dist = (fast_ema - slow_ema) / slow_ema
    slow_trend_dist = (slow_ema - trend_ema) / trend_ema
    strength = (fast_slow_dist + slow_trend_dist) * 50  # Normalize
    
    return SignalOutput(
        signal=signal,
        strength=strength,
        metadata={
            "strategy": "trend_following_ema",
            "fast_period": fast_period,
            "slow_period": slow_period,
            "trend_period": trend_period
        }
    )


def get_strategy_list() -> list[str]:
    """Get list of available strategies.
    
    Returns:
        List of strategy names
    """
    return [
        "ma_crossover",
        "rsi_regime_pullback",
        "donchian_breakout_adx",
        "macd_histogram_atr_filter",
        "mean_reversion",
        "trend_following_ema"
    ]


def generate_signal(
    strategy_name: str,
    df: pd.DataFrame,
    params: Optional[Dict[str, Any]] = None
) -> SignalOutput:
    """Generate signals using specified strategy.
    
    Args:
        strategy_name: Name of strategy to use
        df: DataFrame with OHLCV data
        params: Strategy parameters (optional)
        
    Returns:
        SignalOutput with signals
        
    Raises:
        ValueError: If strategy name is invalid
    """
    if params is None:
        params = {}
    
    # Map strategy names to functions
    strategies = {
        "ma_crossover": lambda: ma_crossover(df['close'], **params),
        "rsi_regime_pullback": lambda: rsi_regime_pullback(df['close'], **params),
        "donchian_breakout_adx": lambda: donchian_breakout_adx(
            df['high'], df['low'], df['close'], **params
        ),
        "macd_histogram_atr_filter": lambda: macd_histogram_atr_filter(
            df['high'], df['low'], df['close'], **params
        ),
        "mean_reversion": lambda: mean_reversion(df['close'], **params),
        "trend_following_ema": lambda: trend_following_ema(df['close'], **params)
    }
    
    if strategy_name not in strategies:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(strategies.keys())}")
    
    return strategies[strategy_name]()

