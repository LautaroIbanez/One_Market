"""Entry band calculation with VWAP and fallback.

This module calculates the entry price using VWAP-based entry band
with configurable beta and fallback to typical price.
"""
import pandas as pd
import numpy as np
from typing import Optional, Literal
from pydantic import BaseModel, Field

from app.research.features import daily_vwap_reconstructed
from app.research.indicators import atr


class EntryBandResult(BaseModel):
    """Entry band calculation result."""
    
    entry_price: float = Field(..., description="Calculated entry price", gt=0)
    entry_mid: float = Field(..., description="Entry mid reference (VWAP or typical)", gt=0)
    beta: float = Field(..., description="Beta adjustment applied")
    method: Literal["vwap", "typical_price"] = Field(..., description="Method used")
    spread_pct: float = Field(default=0.0, description="Spread percentage applied")
    entry_low: Optional[float] = Field(None, description="Lower bound of entry range", gt=0)
    entry_high: Optional[float] = Field(None, description="Upper bound of entry range", gt=0)
    range_pct: Optional[float] = Field(None, description="Range size as percentage of price")


def calculate_entry_mid_vwap(
    df: pd.DataFrame,
    timestamp_col: str = 'timestamp'
) -> Optional[float]:
    """Calculate entry mid using daily VWAP.
    
    Args:
        df: DataFrame with OHLCV data
        timestamp_col: Timestamp column name
        
    Returns:
        VWAP value or None if insufficient data
    """
    try:
        vwap = daily_vwap_reconstructed(df, timestamp_col)
        
        # Return last valid VWAP
        if vwap.notna().any():
            return float(vwap.iloc[-1])
        
        return None
        
    except Exception:
        return None


def calculate_entry_mid_typical_price(df: pd.DataFrame) -> float:
    """Calculate entry mid using typical price fallback.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Typical price (H+L+C)/3
    """
    typical_price = (df['high'].iloc[-1] + df['low'].iloc[-1] + df['close'].iloc[-1]) / 3
    return float(typical_price)


def calculate_entry_band(
    df: pd.DataFrame,
    current_price: float,
    signal_direction: int,
    beta: float = 0.0,
    use_vwap: bool = True,
    min_distance_pct: float = 0.001,
    max_distance_pct: float = 0.01,
    use_volatility_range: bool = True,
    atr_period: int = 14,
    atr_multiplier: float = 0.5
) -> EntryBandResult:
    """Calculate entry band with VWAP or typical price fallback.
    
    The entry band allows for better entry prices by adjusting from mid reference.
    - Long: entry = mid * (1 - beta) - aim to buy below mid
    - Short: entry = mid * (1 + beta) - aim to sell above mid
    
    Args:
        df: DataFrame with OHLCV data
        current_price: Current market price
        signal_direction: Signal direction (1=long, -1=short)
        beta: Entry band adjustment (0-1, typically 0.001-0.01)
        use_vwap: Use VWAP for entry mid (fallback to typical price if not available)
        min_distance_pct: Minimum distance from current price
        max_distance_pct: Maximum distance from current price
        
    Returns:
        EntryBandResult with calculated entry price
    """
    # Calculate entry mid
    if use_vwap:
        entry_mid = calculate_entry_mid_vwap(df)
        method = "vwap"
        
        # Fallback to typical price if VWAP not available
        if entry_mid is None:
            entry_mid = calculate_entry_mid_typical_price(df)
            method = "typical_price"
    else:
        entry_mid = calculate_entry_mid_typical_price(df)
        method = "typical_price"
    
    # Calculate entry price with beta adjustment
    if signal_direction == 1:  # Long
        # Aim to buy below mid
        entry_price = entry_mid * (1 - beta)
    elif signal_direction == -1:  # Short
        # Aim to sell above mid
        entry_price = entry_mid * (1 + beta)
    else:
        # No signal, use current price
        entry_price = current_price
        beta = 0.0
    
    # Validate entry price is reasonable
    distance_from_current = abs(entry_price - current_price) / current_price
    
    # Clamp to reasonable distance
    if distance_from_current < min_distance_pct:
        # Too close, use current price
        entry_price = current_price
        beta = 0.0
    elif distance_from_current > max_distance_pct:
        # Too far, limit to max distance
        if signal_direction == 1:
            entry_price = current_price * (1 - max_distance_pct)
        else:
            entry_price = current_price * (1 + max_distance_pct)
        beta = max_distance_pct
    
    # Calculate spread
    spread_pct = abs(entry_price - entry_mid) / entry_mid
    
    # Calculate entry range based on volatility (ATR or std dev)
    entry_low = None
    entry_high = None
    range_pct = None
    
    if use_volatility_range and len(df) >= atr_period:
        try:
            # Calculate ATR for volatility measure
            atr_val = atr(df['high'], df['low'], df['close'], atr_period).iloc[-1]
            
            # Range bounds: entry_price +/- (ATR * multiplier)
            range_width = atr_val * atr_multiplier
            entry_low = entry_price - range_width
            entry_high = entry_price + range_width
            
            # Ensure positive prices
            entry_low = max(entry_low, entry_price * 0.5)
            entry_high = max(entry_high, entry_price * 1.01)
            
            # Calculate range as percentage
            range_pct = (entry_high - entry_low) / entry_price
            
        except Exception:
            # Fallback: use percentage-based range
            range_pct = 0.01  # 1% default range
            entry_low = entry_price * (1 - range_pct / 2)
            entry_high = entry_price * (1 + range_pct / 2)
    
    return EntryBandResult(
        entry_price=entry_price,
        entry_mid=entry_mid,
        beta=beta,
        method=method,
        spread_pct=spread_pct,
        entry_low=entry_low,
        entry_high=entry_high,
        range_pct=range_pct
    )


def calculate_limit_order_price(
    entry_price: float,
    signal_direction: int,
    tick_size: float = 0.01,
    improve_by_ticks: int = 1
) -> float:
    """Calculate limit order price with tick improvement.
    
    Args:
        entry_price: Calculated entry price
        signal_direction: Signal direction (1=long, -1=short)
        tick_size: Minimum price increment
        improve_by_ticks: Number of ticks to improve price
        
    Returns:
        Limit order price
    """
    improvement = tick_size * improve_by_ticks
    
    if signal_direction == 1:  # Long
        # Bid below entry price
        limit_price = entry_price - improvement
    else:  # Short
        # Ask above entry price
        limit_price = entry_price + improvement
    
    # Round to tick size
    limit_price = round(limit_price / tick_size) * tick_size
    
    return limit_price


def validate_entry_price(
    entry_price: float,
    current_price: float,
    signal_direction: int,
    max_slippage_pct: float = 0.01
) -> tuple[bool, str]:
    """Validate entry price is reasonable.
    
    Args:
        entry_price: Calculated entry price
        current_price: Current market price
        signal_direction: Signal direction
        max_slippage_pct: Maximum acceptable slippage
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if entry_price <= 0:
        return False, "Entry price must be positive"
    
    if current_price <= 0:
        return False, "Current price must be positive"
    
    # Calculate slippage
    if signal_direction == 1:  # Long
        slippage = (current_price - entry_price) / current_price
        if slippage > max_slippage_pct:
            return False, f"Entry price too far below market ({slippage:.2%} > {max_slippage_pct:.2%})"
    else:  # Short
        slippage = (entry_price - current_price) / current_price
        if slippage > max_slippage_pct:
            return False, f"Entry price too far above market ({slippage:.2%} > {max_slippage_pct:.2%})"
    
    return True, ""

