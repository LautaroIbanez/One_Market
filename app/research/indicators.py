"""Technical indicator wrappers with lookahead prevention.

This module provides wrapper functions for common technical indicators
ensuring no lookahead bias and consistent data handling.
"""
import pandas as pd
import numpy as np
from typing import Optional, Union, Tuple
import warnings

# Suppress pandas warnings
warnings.filterwarnings('ignore', category=FutureWarning)


def validate_series(series: pd.Series, name: str = "Series") -> None:
    """Validate that series has sufficient data."""
    if len(series) < 2:
        raise ValueError(f"{name} must have at least 2 data points, got {len(series)}")
    if series.isna().all():
        raise ValueError(f"{name} contains only NaN values")


def ema(close: pd.Series, period: int = 20, adjust: bool = False) -> pd.Series:
    """Calculate Exponential Moving Average without lookahead.
    
    Args:
        close: Close price series
        period: EMA period
        adjust: Use adjusted EMA calculation (default: False for consistency)
        
    Returns:
        EMA series
    """
    validate_series(close, "Close price")
    return close.ewm(span=period, adjust=adjust, min_periods=period).mean()


def sma(close: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Simple Moving Average without lookahead.
    
    Args:
        close: Close price series
        period: SMA period
        
    Returns:
        SMA series
    """
    validate_series(close, "Close price")
    return close.rolling(window=period, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index without lookahead.
    
    Args:
        close: Close price series
        period: RSI period
        
    Returns:
        RSI series (0-100)
    """
    validate_series(close, "Close price")
    
    # Calculate price changes
    delta = close.diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Calculate average gains and losses using EMA
    avg_gains = gains.ewm(span=period, adjust=False, min_periods=period).mean()
    avg_losses = losses.ewm(span=period, adjust=False, min_periods=period).mean()
    
    # Calculate RS and RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range without lookahead.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ATR period
        
    Returns:
        ATR series
    """
    validate_series(high, "High price")
    validate_series(low, "Low price")
    validate_series(close, "Close price")
    
    # Calculate True Range components
    high_low = high - low
    high_close_prev = abs(high - close.shift(1))
    low_close_prev = abs(low - close.shift(1))
    
    # True Range is the max of the three
    tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
    
    # ATR is EMA of True Range
    atr_series = tr.ewm(span=period, adjust=False, min_periods=period).mean()
    
    return atr_series


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average Directional Index without lookahead.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ADX period
        
    Returns:
        ADX series (0-100)
    """
    validate_series(high, "High price")
    validate_series(low, "Low price")
    validate_series(close, "Close price")
    
    # Calculate directional movement
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    # Set to zero if movement is negative
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    # Calculate ATR for normalization
    atr_val = atr(high, low, close, period)
    
    # Smooth directional movements
    plus_di = 100 * plus_dm.ewm(span=period, adjust=False, min_periods=period).mean() / atr_val
    minus_di = 100 * minus_dm.ewm(span=period, adjust=False, min_periods=period).mean() / atr_val
    
    # Calculate DX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    
    # ADX is smoothed DX
    adx_series = dx.ewm(span=period, adjust=False, min_periods=period).mean()
    
    return adx_series


def donchian_channels(high: pd.Series, low: pd.Series, period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Donchian Channels without lookahead.
    
    Args:
        high: High price series
        low: Low price series
        period: Donchian period
        
    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    validate_series(high, "High price")
    validate_series(low, "Low price")
    
    upper_band = high.rolling(window=period, min_periods=period).max()
    lower_band = low.rolling(window=period, min_periods=period).min()
    middle_band = (upper_band + lower_band) / 2
    
    return upper_band, middle_band, lower_band


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD without lookahead.
    
    Args:
        close: Close price series
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
        
    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    validate_series(close, "Close price")
    
    # Calculate MACD line
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    
    # Calculate signal line
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands without lookahead.
    
    Args:
        close: Close price series
        period: Moving average period
        std_dev: Number of standard deviations
        
    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    validate_series(close, "Close price")
    
    middle_band = sma(close, period)
    std = close.rolling(window=period, min_periods=period).std()
    
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    return upper_band, middle_band, lower_band


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator without lookahead.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        k_period: %K period
        d_period: %D smoothing period
        
    Returns:
        Tuple of (%K, %D)
    """
    validate_series(high, "High price")
    validate_series(low, "Low price")
    validate_series(close, "Close price")
    
    # Calculate highest high and lowest low
    highest_high = high.rolling(window=k_period, min_periods=k_period).max()
    lowest_low = low.rolling(window=k_period, min_periods=k_period).min()
    
    # Calculate %K
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    
    # Calculate %D (smoothed %K)
    d = k.rolling(window=d_period, min_periods=d_period).mean()
    
    return k, d


def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Commodity Channel Index without lookahead.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: CCI period
        
    Returns:
        CCI series
    """
    validate_series(high, "High price")
    validate_series(low, "Low price")
    validate_series(close, "Close price")
    
    # Calculate typical price
    tp = (high + low + close) / 3
    
    # Calculate SMA of typical price
    tp_sma = tp.rolling(window=period, min_periods=period).mean()
    
    # Calculate mean deviation
    mean_dev = tp.rolling(window=period, min_periods=period).apply(lambda x: abs(x - x.mean()).mean())
    
    # Calculate CCI
    cci_series = (tp - tp_sma) / (0.015 * mean_dev)
    
    return cci_series


def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Williams %R without lookahead.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: Williams %R period
        
    Returns:
        Williams %R series (-100 to 0)
    """
    validate_series(high, "High price")
    validate_series(low, "Low price")
    validate_series(close, "Close price")
    
    highest_high = high.rolling(window=period, min_periods=period).max()
    lowest_low = low.rolling(window=period, min_periods=period).min()
    
    wr = -100 * (highest_high - close) / (highest_high - lowest_low)
    
    return wr


def momentum(close: pd.Series, period: int = 10) -> pd.Series:
    """Calculate Momentum without lookahead.
    
    Args:
        close: Close price series
        period: Momentum period
        
    Returns:
        Momentum series
    """
    validate_series(close, "Close price")
    return close - close.shift(period)


def roc(close: pd.Series, period: int = 10) -> pd.Series:
    """Calculate Rate of Change without lookahead.
    
    Args:
        close: Close price series
        period: ROC period
        
    Returns:
        ROC series (percentage)
    """
    validate_series(close, "Close price")
    return 100 * (close - close.shift(period)) / close.shift(period)


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate On-Balance Volume without lookahead.
    
    Args:
        close: Close price series
        volume: Volume series
        
    Returns:
        OBV series
    """
    validate_series(close, "Close price")
    validate_series(volume, "Volume")
    
    # Determine volume direction
    volume_direction = np.sign(close.diff())
    
    # Calculate OBV
    obv_series = (volume * volume_direction).cumsum()
    
    return obv_series


def vwap_intraday(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, timestamp: pd.Series) -> pd.Series:
    """Calculate intraday VWAP that resets daily.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        volume: Volume series
        timestamp: Timestamp series (must be datetime)
        
    Returns:
        VWAP series
    """
    validate_series(close, "Close price")
    validate_series(volume, "Volume")
    
    # Calculate typical price
    tp = (high + low + close) / 3
    
    # Convert timestamp to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(timestamp):
        timestamp = pd.to_datetime(timestamp, unit='ms')
    
    # Extract date for grouping
    date = timestamp.dt.date
    
    # Calculate cumulative (TP * volume) and cumulative volume per day
    tp_volume = tp * volume
    
    # Group by date and calculate cumulative sums
    cum_tp_volume = tp_volume.groupby(date).cumsum()
    cum_volume = volume.groupby(date).cumsum()
    
    # Calculate VWAP
    vwap_series = cum_tp_volume / cum_volume
    
    return vwap_series


def supertrend(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 10, multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
    """Calculate Supertrend indicator without lookahead.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ATR period
        multiplier: ATR multiplier
        
    Returns:
        Tuple of (supertrend, direction) where direction is 1 (long) or -1 (short)
    """
    validate_series(high, "High price")
    validate_series(low, "Low price")
    validate_series(close, "Close price")
    
    # Calculate ATR
    atr_val = atr(high, low, close, period)
    
    # Calculate basic bands
    hl2 = (high + low) / 2
    upper_band = hl2 + (multiplier * atr_val)
    lower_band = hl2 - (multiplier * atr_val)
    
    # Initialize
    supertrend_series = pd.Series(index=close.index, dtype=float)
    direction = pd.Series(index=close.index, dtype=int)
    
    supertrend_series.iloc[0] = upper_band.iloc[0]
    direction.iloc[0] = 1
    
    # Calculate Supertrend
    for i in range(1, len(close)):
        if pd.isna(upper_band.iloc[i]) or pd.isna(lower_band.iloc[i]):
            supertrend_series.iloc[i] = supertrend_series.iloc[i-1]
            direction.iloc[i] = direction.iloc[i-1]
            continue
            
        # Update bands
        if close.iloc[i-1] <= supertrend_series.iloc[i-1]:
            supertrend_series.iloc[i] = upper_band.iloc[i]
            direction.iloc[i] = -1
        else:
            supertrend_series.iloc[i] = lower_band.iloc[i]
            direction.iloc[i] = 1
            
        # Check for trend change
        if direction.iloc[i] == 1 and close.iloc[i] < supertrend_series.iloc[i]:
            supertrend_series.iloc[i] = upper_band.iloc[i]
            direction.iloc[i] = -1
        elif direction.iloc[i] == -1 and close.iloc[i] > supertrend_series.iloc[i]:
            supertrend_series.iloc[i] = lower_band.iloc[i]
            direction.iloc[i] = 1
    
    return supertrend_series, direction


def keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20, multiplier: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Keltner Channels without lookahead.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: EMA period
        multiplier: ATR multiplier
        
    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    validate_series(close, "Close price")
    
    # Middle line is EMA of close
    middle_band = ema(close, period)
    
    # Calculate ATR
    atr_val = atr(high, low, close, period)
    
    # Calculate bands
    upper_band = middle_band + (multiplier * atr_val)
    lower_band = middle_band - (multiplier * atr_val)
    
    return upper_band, middle_band, lower_band

