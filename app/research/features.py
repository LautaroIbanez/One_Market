"""Feature engineering for trading strategies.

This module provides additional features beyond basic indicators,
including volatility measures, trend strength, and market regimes.
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple
from app.research.indicators import atr, validate_series


def daily_vwap_reconstructed(df: pd.DataFrame, timestamp_col: str = 'timestamp') -> pd.Series:
    """Reconstruct daily VWAP from OHLCV data.
    
    This handles cases where we don't have intraday tick data by
    using the typical price and volume from each bar.
    
    Args:
        df: DataFrame with OHLCV data
        timestamp_col: Name of timestamp column
        
    Returns:
        VWAP series
    """
    # Calculate typical price
    tp = (df['high'] + df['low'] + df['close']) / 3
    
    # Convert timestamp to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
        timestamp = pd.to_datetime(df[timestamp_col], unit='ms')
    else:
        timestamp = df[timestamp_col]
    
    # Extract date for grouping
    date = timestamp.dt.date
    
    # Calculate VWAP per day
    tp_volume = tp * df['volume']
    cum_tp_volume = tp_volume.groupby(date).cumsum()
    cum_volume = df['volume'].groupby(date).cumsum()
    
    vwap = cum_tp_volume / cum_volume
    
    return vwap


def relative_volatility(close: pd.Series, short_period: int = 10, long_period: int = 50) -> pd.Series:
    """Calculate relative volatility (short-term vol / long-term vol).
    
    Values > 1 indicate elevated volatility, < 1 indicate low volatility.
    
    Args:
        close: Close price series
        short_period: Short-term volatility period
        long_period: Long-term volatility period
        
    Returns:
        Relative volatility series
    """
    validate_series(close, "Close price")
    
    # Calculate returns
    returns = close.pct_change()
    
    # Calculate volatilities
    short_vol = returns.rolling(window=short_period, min_periods=short_period).std()
    long_vol = returns.rolling(window=long_period, min_periods=long_period).std()
    
    # Calculate relative volatility
    rel_vol = short_vol / long_vol
    
    return rel_vol


def normalized_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate ATR normalized by price (ATR%).
    
    This makes ATR comparable across different price levels.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ATR period
        
    Returns:
        Normalized ATR series (percentage)
    """
    from app.research.indicators import atr as calc_atr
    
    atr_val = calc_atr(high, low, close, period)
    natr = 100 * atr_val / close
    
    return natr


def trend_strength(close: pd.Series, period: int = 20) -> pd.Series:
    """Calculate trend strength using linear regression R-squared.
    
    Values closer to 1 indicate strong trend, closer to 0 indicate ranging market.
    
    Args:
        close: Close price series
        period: Lookback period
        
    Returns:
        Trend strength series (0-1)
    """
    validate_series(close, "Close price")
    
    def calc_r_squared(window):
        """Calculate R-squared for a window."""
        if len(window) < 2:
            return np.nan
        
        x = np.arange(len(window))
        y = window.values
        
        # Remove NaN
        mask = ~np.isnan(y)
        if mask.sum() < 2:
            return np.nan
        
        x = x[mask]
        y = y[mask]
        
        # Calculate correlation
        corr = np.corrcoef(x, y)[0, 1]
        r_squared = corr ** 2
        
        return r_squared
    
    trend_str = close.rolling(window=period, min_periods=period).apply(calc_r_squared, raw=False)
    
    return trend_str


def volatility_regime(close: pd.Series, short_period: int = 10, long_period: int = 50, threshold: float = 1.2) -> pd.Series:
    """Classify volatility regime (high/normal/low).
    
    Args:
        close: Close price series
        short_period: Short-term period
        long_period: Long-term period
        threshold: Threshold for high/low regime
        
    Returns:
        Regime series: 1 (high), 0 (normal), -1 (low)
    """
    rel_vol = relative_volatility(close, short_period, long_period)
    
    regime = pd.Series(0, index=close.index)
    regime[rel_vol > threshold] = 1
    regime[rel_vol < (1 / threshold)] = -1
    
    return regime


def distance_from_ma(close: pd.Series, period: int = 20) -> pd.Series:
    """Calculate percentage distance from moving average.
    
    Args:
        close: Close price series
        period: Moving average period
        
    Returns:
        Distance series (percentage)
    """
    from app.research.indicators import sma
    
    ma = sma(close, period)
    distance = 100 * (close - ma) / ma
    
    return distance


def rolling_sharpe(returns: pd.Series, period: int = 90, periods_per_year: int = 252) -> pd.Series:
    """Calculate rolling Sharpe ratio.
    
    Args:
        returns: Returns series
        period: Rolling window period
        periods_per_year: Number of periods in a year
        
    Returns:
        Rolling Sharpe ratio series
    """
    validate_series(returns, "Returns")
    
    mean_returns = returns.rolling(window=period, min_periods=period).mean()
    std_returns = returns.rolling(window=period, min_periods=period).std()
    
    sharpe = (mean_returns / std_returns) * np.sqrt(periods_per_year)
    
    return sharpe


def rolling_sortino(returns: pd.Series, period: int = 90, periods_per_year: int = 252, target: float = 0.0) -> pd.Series:
    """Calculate rolling Sortino ratio.
    
    Args:
        returns: Returns series
        period: Rolling window period
        periods_per_year: Number of periods in a year
        target: Target return (default: 0)
        
    Returns:
        Rolling Sortino ratio series
    """
    validate_series(returns, "Returns")
    
    mean_returns = returns.rolling(window=period, min_periods=period).mean()
    
    # Calculate downside deviation
    downside_returns = returns.where(returns < target, 0)
    downside_std = downside_returns.rolling(window=period, min_periods=period).std()
    
    sortino = (mean_returns - target) / downside_std * np.sqrt(periods_per_year)
    
    return sortino


def cumulative_return(returns: pd.Series) -> pd.Series:
    """Calculate cumulative return from returns series.
    
    Args:
        returns: Returns series
        
    Returns:
        Cumulative return series
    """
    validate_series(returns, "Returns")
    return (1 + returns).cumprod() - 1


def rolling_max_dd(returns: pd.Series, period: int = 252) -> pd.Series:
    """Calculate rolling maximum drawdown.
    
    Args:
        returns: Returns series
        period: Rolling window period
        
    Returns:
        Rolling maximum drawdown series
    """
    validate_series(returns, "Returns")
    
    cum_returns = (1 + returns).cumprod()
    
    def calc_max_dd(window):
        """Calculate max drawdown for a window."""
        if len(window) < 2:
            return np.nan
        
        running_max = np.maximum.accumulate(window)
        dd = (window - running_max) / running_max
        return dd.min()
    
    rolling_dd = cum_returns.rolling(window=period, min_periods=period).apply(calc_max_dd, raw=False)
    
    return rolling_dd


def price_zscore(close: pd.Series, period: int = 20) -> pd.Series:
    """Calculate price Z-score (standardized distance from mean).
    
    Args:
        close: Close price series
        period: Lookback period
        
    Returns:
        Z-score series
    """
    validate_series(close, "Close price")
    
    mean = close.rolling(window=period, min_periods=period).mean()
    std = close.rolling(window=period, min_periods=period).std()
    
    zscore = (close - mean) / std
    
    return zscore


def volume_zscore(volume: pd.Series, period: int = 20) -> pd.Series:
    """Calculate volume Z-score.
    
    Args:
        volume: Volume series
        period: Lookback period
        
    Returns:
        Volume Z-score series
    """
    validate_series(volume, "Volume")
    
    mean = volume.rolling(window=period, min_periods=period).mean()
    std = volume.rolling(window=period, min_periods=period).std()
    
    zscore = (volume - mean) / std
    
    return zscore


def support_resistance_distance(close: pd.Series, period: int = 50) -> Tuple[pd.Series, pd.Series]:
    """Calculate distance to recent support and resistance levels.
    
    Args:
        close: Close price series
        period: Lookback period
        
    Returns:
        Tuple of (distance_to_resistance_pct, distance_to_support_pct)
    """
    validate_series(close, "Close price")
    
    # Resistance is recent high
    resistance = close.rolling(window=period, min_periods=period).max()
    
    # Support is recent low
    support = close.rolling(window=period, min_periods=period).min()
    
    # Calculate distances
    dist_to_resistance = 100 * (resistance - close) / close
    dist_to_support = 100 * (close - support) / close
    
    return dist_to_resistance, dist_to_support


def money_flow_index(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Money Flow Index.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        volume: Volume series
        period: MFI period
        
    Returns:
        MFI series (0-100)
    """
    validate_series(high, "High price")
    validate_series(low, "Low price")
    validate_series(close, "Close price")
    validate_series(volume, "Volume")
    
    # Calculate typical price
    tp = (high + low + close) / 3
    
    # Calculate raw money flow
    mf = tp * volume
    
    # Determine positive and negative money flow
    mf_direction = tp.diff()
    positive_mf = mf.where(mf_direction > 0, 0)
    negative_mf = mf.where(mf_direction < 0, 0)
    
    # Calculate sums over period
    positive_mf_sum = positive_mf.rolling(window=period, min_periods=period).sum()
    negative_mf_sum = negative_mf.rolling(window=period, min_periods=period).sum()
    
    # Calculate money flow ratio and MFI
    mf_ratio = positive_mf_sum / negative_mf_sum
    mfi = 100 - (100 / (1 + mf_ratio))
    
    return mfi


def choppy_index(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Choppiness Index.
    
    Values closer to 100 indicate choppy/ranging market,
    values closer to 0 indicate trending market.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: Lookback period
        
    Returns:
        Choppiness Index series (0-100)
    """
    validate_series(high, "High price")
    validate_series(low, "Low price")
    validate_series(close, "Close price")
    
    # Calculate ATR sum
    from app.research.indicators import atr as calc_atr
    atr_val = calc_atr(high, low, close, 1)  # True range (period=1)
    atr_sum = atr_val.rolling(window=period, min_periods=period).sum()
    
    # Calculate high-low range
    high_roll = high.rolling(window=period, min_periods=period).max()
    low_roll = low.rolling(window=period, min_periods=period).min()
    range_val = high_roll - low_roll
    
    # Calculate Choppiness Index
    chop = 100 * np.log10(atr_sum / range_val) / np.log10(period)
    
    return chop


def candle_direction(open_price: pd.Series, close: pd.Series) -> pd.Series:
    """Determine candle direction (bullish/bearish).
    
    Args:
        open_price: Open price series
        close: Close price series
        
    Returns:
        Direction series: 1 (bullish), -1 (bearish), 0 (doji)
    """
    validate_series(open_price, "Open price")
    validate_series(close, "Close price")
    
    diff = close - open_price
    direction = pd.Series(0, index=close.index)
    direction[diff > 0] = 1
    direction[diff < 0] = -1
    
    return direction


def consecutive_closes(close: pd.Series) -> Tuple[pd.Series, pd.Series]:
    """Count consecutive up and down closes.
    
    Args:
        close: Close price series
        
    Returns:
        Tuple of (consecutive_up, consecutive_down)
    """
    validate_series(close, "Close price")
    
    # Calculate price changes
    changes = close.diff()
    
    # Initialize
    consecutive_up = pd.Series(0, index=close.index)
    consecutive_down = pd.Series(0, index=close.index)
    
    up_count = 0
    down_count = 0
    
    for i in range(1, len(changes)):
        if changes.iloc[i] > 0:
            up_count += 1
            down_count = 0
        elif changes.iloc[i] < 0:
            down_count += 1
            up_count = 0
        else:
            up_count = 0
            down_count = 0
        
        consecutive_up.iloc[i] = up_count
        consecutive_down.iloc[i] = down_count
    
    return consecutive_up, consecutive_down


def higher_highs_lower_lows(high: pd.Series, low: pd.Series, period: int = 5) -> Tuple[pd.Series, pd.Series]:
    """Detect higher highs and lower lows pattern.
    
    Args:
        high: High price series
        low: Low price series
        period: Lookback period
        
    Returns:
        Tuple of (higher_highs, lower_lows) as boolean series
    """
    validate_series(high, "High price")
    validate_series(low, "Low price")
    
    # Calculate if current high is higher than previous period high
    prev_high = high.shift(period)
    higher_highs = high > prev_high
    
    # Calculate if current low is lower than previous period low
    prev_low = low.shift(period)
    lower_lows = low < prev_low
    
    return higher_highs, lower_lows

