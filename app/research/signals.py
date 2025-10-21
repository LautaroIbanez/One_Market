"""Atomic trading signal strategies.

This module provides modular, tuneable trading strategies that generate
entry/exit signals. All strategies support both long and short positions
and output normalized signals.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Literal, List
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


class ATRChannelBreakoutConfig(BaseModel):
    """Configuration for ATR Channel Breakout with Volume Filter."""
    name: str = Field(default="atr_channel_breakout_volume", description="Strategy name")
    atr_period: int = Field(default=14, ge=5, le=50, description="ATR period")
    atr_multiplier: float = Field(default=2.0, ge=0.5, le=5.0, description="ATR multiplier for channel width")
    volume_ma_period: int = Field(default=20, ge=5, le=100, description="Volume MA period")
    volume_threshold: float = Field(default=1.5, ge=1.0, le=5.0, description="Minimum volume multiplier vs MA")
    long_enabled: bool = Field(default=True, description="Enable long signals")
    short_enabled: bool = Field(default=True, description="Enable short signals")


class VWAPZScoreConfig(BaseModel):
    """Configuration for VWAP Z-Score Mean Reversion Strategy."""
    name: str = Field(default="vwap_zscore_reversion", description="Strategy name")
    vwap_period: int = Field(default=20, ge=10, le=100, description="Period for rolling VWAP")
    zscore_entry: float = Field(default=2.0, ge=1.0, le=4.0, description="Z-score threshold for entry")
    zscore_exit: float = Field(default=0.5, ge=0.1, le=2.0, description="Z-score threshold for exit")
    long_enabled: bool = Field(default=True, description="Enable long signals")
    short_enabled: bool = Field(default=True, description="Enable short signals")


class EMATripleMomentumConfig(BaseModel):
    """Configuration for Triple EMA + RSI Regime Momentum Strategy."""
    name: str = Field(default="ema_triple_momentum", description="Strategy name")
    fast_period: int = Field(default=8, ge=3, le=20, description="Fast EMA period")
    mid_period: int = Field(default=21, ge=10, le=50, description="Mid EMA period")
    slow_period: int = Field(default=55, ge=20, le=200, description="Slow EMA period")
    rsi_period: int = Field(default=14, ge=5, le=30, description="RSI period for regime")
    rsi_bull_threshold: float = Field(default=50, ge=30, le=70, description="RSI threshold for long regime")
    rsi_bear_threshold: float = Field(default=50, ge=30, le=70, description="RSI threshold for short regime")
    long_enabled: bool = Field(default=True, description="Enable long signals")
    short_enabled: bool = Field(default=True, description="Enable short signals")


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


def atr_channel_breakout_volume(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, atr_period: int = 14, atr_multiplier: float = 2.0, volume_ma_period: int = 20, volume_threshold: float = 1.5, long_enabled: bool = True, short_enabled: bool = True) -> SignalOutput:
    """ATR Channel Breakout with Volume Filter. Trades breakouts of ATR-based channels confirmed by high volume. - Long: Price breaks above upper ATR band + volume > threshold - Short: Price breaks below lower ATR band + volume > threshold. Args: high: High price series, low: Low price series, close: Close price series, volume: Volume series, atr_period: ATR period, atr_multiplier: ATR multiplier for channel width, volume_ma_period: Volume MA period for filter, volume_threshold: Minimum volume multiplier vs MA, long_enabled: Enable long signals, short_enabled: Enable short signals. Returns: SignalOutput with signals"""
    validate_series(close, "Close price")
    atr_val = atr(high, low, close, atr_period)
    middle = close.rolling(window=atr_period).mean()
    upper_band = middle + (atr_val * atr_multiplier)
    lower_band = middle - (atr_val * atr_multiplier)
    volume_ma = volume.rolling(window=volume_ma_period).mean()
    high_volume = volume > (volume_ma * volume_threshold)
    signal = pd.Series(0, index=close.index)
    if long_enabled:
        breakout_long = (close > upper_band) & (close.shift(1) <= upper_band.shift(1))
        signal[breakout_long & high_volume] = 1
        in_long = signal.shift(1) == 1
        hold_long = close > middle
        signal[in_long & hold_long] = 1
    if short_enabled:
        breakout_short = (close < lower_band) & (close.shift(1) >= lower_band.shift(1))
        signal[breakout_short & high_volume] = -1
        in_short = signal.shift(1) == -1
        hold_short = close < middle
        signal[in_short & hold_short] = -1
    distance_from_mid = (close - middle) / middle
    volume_strength = (volume / volume_ma).clip(upper=3.0)
    strength = distance_from_mid * volume_strength
    return SignalOutput(signal=signal, strength=strength, metadata={"strategy": "atr_channel_breakout_volume", "atr_period": atr_period, "atr_multiplier": atr_multiplier, "volume_ma_period": volume_ma_period, "volume_threshold": volume_threshold})


def vwap_zscore_reversion(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, vwap_period: int = 20, zscore_entry: float = 2.0, zscore_exit: float = 0.5, long_enabled: bool = True, short_enabled: bool = True) -> SignalOutput:
    """VWAP Z-Score Mean Reversion Strategy. Trades reversions when price deviates significantly from VWAP (measured by z-score). - Long: Z-score < -zscore_entry (oversold vs VWAP), exit when z-score > -zscore_exit - Short: Z-score > +zscore_entry (overbought vs VWAP), exit when z-score < +zscore_exit. Args: high: High price series, low: Low price series, close: Close price series, volume: Volume series, vwap_period: Period for rolling VWAP calculation, zscore_entry: Z-score threshold for entry, zscore_exit: Z-score threshold for exit, long_enabled: Enable long signals, short_enabled: Enable short signals. Returns: SignalOutput with signals"""
    validate_series(close, "Close price")
    typical_price = (high + low + close) / 3
    vwap_rolling = (typical_price * volume).rolling(window=vwap_period).sum() / volume.rolling(window=vwap_period).sum()
    deviation = close - vwap_rolling
    std_dev = deviation.rolling(window=vwap_period).std()
    zscore = deviation / std_dev.replace(0, np.nan)
    signal = pd.Series(0, index=close.index)
    if long_enabled:
        entry_long = zscore < -zscore_entry
        signal[entry_long] = 1
        in_long = signal.shift(1) == 1
        exit_long = zscore > -zscore_exit
        signal[in_long & ~exit_long] = 1
        signal[in_long & exit_long] = 0
    if short_enabled:
        entry_short = zscore > zscore_entry
        signal[entry_short] = -1
        in_short = signal.shift(1) == -1
        exit_short = zscore < zscore_exit
        signal[in_short & ~exit_short] = -1
        signal[in_short & exit_short] = 0
    strength = -zscore / zscore_entry
    return SignalOutput(signal=signal, strength=strength, metadata={"strategy": "vwap_zscore_reversion", "vwap_period": vwap_period, "zscore_entry": zscore_entry, "zscore_exit": zscore_exit})


def ema_triple_momentum(close: pd.Series, fast_period: int = 8, mid_period: int = 21, slow_period: int = 55, rsi_period: int = 14, rsi_bull_threshold: float = 50, rsi_bear_threshold: float = 50, long_enabled: bool = True, short_enabled: bool = True) -> SignalOutput:
    """Triple EMA + RSI Regime Momentum (Multi-Timeframe Style). Combines three EMA alignment with RSI regime filter for momentum trades. - Long: Fast > Mid > Slow EMAs + RSI > bull_threshold - Short: Fast < Mid < Slow EMAs + RSI < bear_threshold. Args: close: Close price series, fast_period: Fast EMA period, mid_period: Mid EMA period, slow_period: Slow EMA period, rsi_period: RSI period for regime, rsi_bull_threshold: RSI threshold for long regime, rsi_bear_threshold: RSI threshold for short regime, long_enabled: Enable long signals, short_enabled: Enable short signals. Returns: SignalOutput with signals"""
    validate_series(close, "Close price")
    fast_ema = ema(close, fast_period)
    mid_ema = ema(close, mid_period)
    slow_ema = ema(close, slow_period)
    rsi_val = rsi(close, rsi_period)
    signal = pd.Series(0, index=close.index)
    if long_enabled:
        ema_aligned_long = (fast_ema > mid_ema) & (mid_ema > slow_ema)
        rsi_bullish = rsi_val > rsi_bull_threshold
        signal[ema_aligned_long & rsi_bullish] = 1
    if short_enabled:
        ema_aligned_short = (fast_ema < mid_ema) & (mid_ema < slow_ema)
        rsi_bearish = rsi_val < rsi_bear_threshold
        signal[ema_aligned_short & rsi_bearish] = -1
    fast_mid_dist = (fast_ema - mid_ema) / mid_ema
    mid_slow_dist = (mid_ema - slow_ema) / slow_ema
    rsi_strength = (rsi_val - 50) / 50
    strength = (fast_mid_dist + mid_slow_dist + rsi_strength) * 10
    return SignalOutput(signal=signal, strength=strength, metadata={"strategy": "ema_triple_momentum", "fast_period": fast_period, "mid_period": mid_period, "slow_period": slow_period, "rsi_period": rsi_period, "rsi_bull_threshold": rsi_bull_threshold, "rsi_bear_threshold": rsi_bear_threshold})


def combine_signals(signals_list: List[pd.Series], method: str = "consensus") -> SignalOutput:
    """Combine multiple signals into a single signal.
    
    Args:
        signals_list: List of signal series
        method: Combination method ("consensus", "average", "majority")
        
    Returns:
        Combined signal output
    """
    if not signals_list:
        return SignalOutput(signal=pd.Series([0]), metadata={"method": method})
    
    # Align all signals to the same length
    min_length = min(len(s) for s in signals_list)
    aligned_signals = [s.iloc[:min_length] for s in signals_list]
    
    if method == "consensus":
        # Consensus: all signals must agree
        combined_signal = pd.Series([0] * min_length)
        for i in range(min_length):
            values = [s.iloc[i] for s in aligned_signals]
            if all(v == 1 for v in values):
                combined_signal.iloc[i] = 1
            elif all(v == -1 for v in values):
                combined_signal.iloc[i] = -1
            else:
                combined_signal.iloc[i] = 0
    
    elif method == "average":
        # Average: take the mean of all signals
        combined_signal = pd.Series([0.0] * min_length)
        for i in range(min_length):
            values = [s.iloc[i] for s in aligned_signals]
            avg = sum(values) / len(values)
            if avg > 0.5:
                combined_signal.iloc[i] = 1
            elif avg < -0.5:
                combined_signal.iloc[i] = -1
            else:
                combined_signal.iloc[i] = 0
    
    elif method == "majority":
        # Majority vote
        combined_signal = pd.Series([0] * min_length)
        for i in range(min_length):
            values = [s.iloc[i] for s in aligned_signals]
            positive_count = sum(1 for v in values if v > 0)
            negative_count = sum(1 for v in values if v < 0)
            
            if positive_count > negative_count:
                combined_signal.iloc[i] = 1
            elif negative_count > positive_count:
                combined_signal.iloc[i] = -1
            else:
                combined_signal.iloc[i] = 0
    
    else:
        raise ValueError(f"Unknown combination method: {method}")
    
    return SignalOutput(
        signal=combined_signal,
        metadata={
            "method": method,
            "num_signals": len(signals_list),
            "combination": True
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
        "trend_following_ema",
        "atr_channel_breakout_volume",
        "vwap_zscore_reversion",
        "ema_triple_momentum"
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
        "trend_following_ema": lambda: trend_following_ema(df['close'], **params),
        "atr_channel_breakout_volume": lambda: atr_channel_breakout_volume(
            df['high'], df['low'], df['close'], df['volume'], **params
        ),
        "vwap_zscore_reversion": lambda: vwap_zscore_reversion(
            df['high'], df['low'], df['close'], df['volume'], **params
        ),
        "ema_triple_momentum": lambda: ema_triple_momentum(df['close'], **params)
    }
    
    if strategy_name not in strategies:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(strategies.keys())}")
    
    return strategies[strategy_name]()

