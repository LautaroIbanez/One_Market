"""Take Profit and Stop Loss engine with multiple methods.

This module provides TP/SL calculation using:
- ATR-based stops
- Swing highs/lows
- Risk/Reward ratio validation
- Configurable parameters for UI exposure
"""
import pandas as pd
import numpy as np
from typing import Optional, Literal, Tuple
from pydantic import BaseModel, Field

from app.research.indicators import atr
from app.core.risk import compute_levels, StopLossTakeProfit


class TPSLConfig(BaseModel):
    """Configuration for TP/SL calculation."""
    
    method: Literal["atr", "swing", "hybrid"] = Field(default="atr", description="TP/SL method")
    
    # ATR parameters
    atr_period: int = Field(default=14, description="ATR period")
    atr_multiplier_sl: float = Field(default=2.0, description="ATR multiplier for SL", gt=0)
    atr_multiplier_tp: float = Field(default=3.0, description="ATR multiplier for TP", gt=0)
    
    # Swing parameters
    swing_lookback: int = Field(default=20, description="Lookback period for swing highs/lows")
    swing_buffer_pct: float = Field(default=0.001, description="Buffer beyond swing level (%)")
    
    # Risk/Reward
    min_rr_ratio: float = Field(default=1.5, description="Minimum R/R ratio", gt=1.0)
    max_rr_ratio: float = Field(default=5.0, description="Maximum R/R ratio", gt=1.0)
    
    # Limits
    min_sl_pct: float = Field(default=0.005, description="Minimum SL distance (%)")
    max_sl_pct: float = Field(default=0.05, description="Maximum SL distance (%)")


class TPSLResult(BaseModel):
    """TP/SL calculation result."""
    
    stop_loss: float = Field(..., description="Stop loss price", gt=0)
    take_profit: float = Field(..., description="Take profit price", gt=0)
    
    atr_value: float = Field(..., description="ATR value used", gt=0)
    risk_amount: float = Field(..., description="Risk amount per unit")
    reward_amount: float = Field(..., description="Reward amount per unit")
    risk_reward_ratio: float = Field(..., description="R/R ratio")
    
    stop_loss_pct: float = Field(..., description="SL distance from entry (%)")
    take_profit_pct: float = Field(..., description="TP distance from entry (%)")
    
    method_used: Literal["atr", "swing", "hybrid"] = Field(..., description="Method used")
    swing_level: Optional[float] = Field(None, description="Swing level if used")


def find_swing_high(high: pd.Series, lookback: int = 20) -> float:
    """Find recent swing high.
    
    Args:
        high: High price series
        lookback: Lookback period
        
    Returns:
        Swing high price
    """
    if len(high) < lookback:
        lookback = len(high)
    
    swing_high = high.iloc[-lookback:].max()
    return float(swing_high)


def find_swing_low(low: pd.Series, lookback: int = 20) -> float:
    """Find recent swing low.
    
    Args:
        low: Low price series
        lookback: Lookback period
        
    Returns:
        Swing low price
    """
    if len(low) < lookback:
        lookback = len(low)
    
    swing_low = low.iloc[-lookback:].min()
    return float(swing_low)


def calculate_tp_sl_atr(
    df: pd.DataFrame,
    entry_price: float,
    signal_direction: int,
    config: TPSLConfig
) -> TPSLResult:
    """Calculate TP/SL using ATR method.
    
    Args:
        df: DataFrame with OHLCV data
        entry_price: Entry price
        signal_direction: Signal direction (1=long, -1=short)
        config: TP/SL configuration
        
    Returns:
        TPSLResult with calculated levels
    """
    # Calculate ATR
    atr_val = atr(df['high'], df['low'], df['close'], period=config.atr_period)
    current_atr = float(atr_val.iloc[-1])
    
    # Use core risk module for calculation
    side = "long" if signal_direction == 1 else "short"
    
    levels = compute_levels(
        entry_price=entry_price,
        atr=current_atr,
        side=side,
        atr_multiplier_sl=config.atr_multiplier_sl,
        atr_multiplier_tp=config.atr_multiplier_tp,
        min_rr_ratio=config.min_rr_ratio
    )
    
    return TPSLResult(
        stop_loss=levels.stop_loss,
        take_profit=levels.take_profit,
        atr_value=current_atr,
        risk_amount=levels.risk_amount,
        reward_amount=levels.reward_amount,
        risk_reward_ratio=levels.risk_reward_ratio,
        stop_loss_pct=levels.stop_loss_pct,
        take_profit_pct=levels.take_profit_pct,
        method_used="atr",
        swing_level=None
    )


def calculate_tp_sl_swing(
    df: pd.DataFrame,
    entry_price: float,
    signal_direction: int,
    config: TPSLConfig
) -> TPSLResult:
    """Calculate TP/SL using swing highs/lows method.
    
    Args:
        df: DataFrame with OHLCV data
        entry_price: Entry price
        signal_direction: Signal direction (1=long, -1=short)
        config: TP/SL configuration
        
    Returns:
        TPSLResult with calculated levels
    """
    # Calculate ATR for reference
    atr_val = atr(df['high'], df['low'], df['close'], period=config.atr_period)
    current_atr = float(atr_val.iloc[-1])
    
    if signal_direction == 1:  # Long
        # Stop below recent swing low
        swing_low = find_swing_low(df['low'], config.swing_lookback)
        stop_loss = swing_low * (1 - config.swing_buffer_pct)
        
        # Take profit at recent swing high or R/R based
        swing_high = find_swing_high(df['high'], config.swing_lookback)
        risk_amount = entry_price - stop_loss
        
        # Use swing high if it provides good R/R, otherwise use R/R ratio
        potential_tp = swing_high * (1 + config.swing_buffer_pct)
        reward_at_swing = potential_tp - entry_price
        rr_at_swing = reward_at_swing / risk_amount if risk_amount > 0 else 0
        
        if rr_at_swing >= config.min_rr_ratio:
            take_profit = potential_tp
        else:
            # Use minimum R/R
            take_profit = entry_price + (risk_amount * config.min_rr_ratio)
        
        swing_level = swing_low
        
    else:  # Short
        # Stop above recent swing high
        swing_high = find_swing_high(df['high'], config.swing_lookback)
        stop_loss = swing_high * (1 + config.swing_buffer_pct)
        
        # Take profit at recent swing low or R/R based
        swing_low = find_swing_low(df['low'], config.swing_lookback)
        risk_amount = stop_loss - entry_price
        
        # Use swing low if it provides good R/R
        potential_tp = swing_low * (1 - config.swing_buffer_pct)
        reward_at_swing = entry_price - potential_tp
        rr_at_swing = reward_at_swing / risk_amount if risk_amount > 0 else 0
        
        if rr_at_swing >= config.min_rr_ratio:
            take_profit = potential_tp
        else:
            # Use minimum R/R
            take_profit = entry_price - (risk_amount * config.min_rr_ratio)
        
        swing_level = swing_high
    
    # Calculate metrics
    reward_amount = abs(take_profit - entry_price)
    risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
    
    stop_loss_pct = abs(stop_loss - entry_price) / entry_price
    take_profit_pct = abs(take_profit - entry_price) / entry_price
    
    return TPSLResult(
        stop_loss=stop_loss,
        take_profit=take_profit,
        atr_value=current_atr,
        risk_amount=risk_amount,
        reward_amount=reward_amount,
        risk_reward_ratio=risk_reward_ratio,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        method_used="swing",
        swing_level=swing_level
    )


def calculate_tp_sl_hybrid(
    df: pd.DataFrame,
    entry_price: float,
    signal_direction: int,
    config: TPSLConfig
) -> TPSLResult:
    """Calculate TP/SL using hybrid method (ATR + Swing).
    
    Uses the more conservative (safer) stop loss from both methods.
    
    Args:
        df: DataFrame with OHLCV data
        entry_price: Entry price
        signal_direction: Signal direction (1=long, -1=short)
        config: TP/SL configuration
        
    Returns:
        TPSLResult with calculated levels
    """
    # Calculate both methods
    atr_result = calculate_tp_sl_atr(df, entry_price, signal_direction, config)
    swing_result = calculate_tp_sl_swing(df, entry_price, signal_direction, config)
    
    # Choose more conservative (wider) stop
    if signal_direction == 1:  # Long
        # Lower stop is safer for long
        stop_loss = min(atr_result.stop_loss, swing_result.stop_loss)
    else:  # Short
        # Higher stop is safer for short
        stop_loss = max(atr_result.stop_loss, swing_result.stop_loss)
    
    # Calculate risk
    risk_amount = abs(entry_price - stop_loss)
    
    # Take profit based on minimum R/R
    if signal_direction == 1:
        take_profit = entry_price + (risk_amount * config.min_rr_ratio)
    else:
        take_profit = entry_price - (risk_amount * config.min_rr_ratio)
    
    # Use swing high/low for TP if better
    if signal_direction == 1 and swing_result.take_profit > take_profit:
        take_profit = swing_result.take_profit
    elif signal_direction == -1 and swing_result.take_profit < take_profit:
        take_profit = swing_result.take_profit
    
    # Calculate metrics
    reward_amount = abs(take_profit - entry_price)
    risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
    
    stop_loss_pct = abs(stop_loss - entry_price) / entry_price
    take_profit_pct = abs(take_profit - entry_price) / entry_price
    
    return TPSLResult(
        stop_loss=stop_loss,
        take_profit=take_profit,
        atr_value=atr_result.atr_value,
        risk_amount=risk_amount,
        reward_amount=reward_amount,
        risk_reward_ratio=risk_reward_ratio,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        method_used="hybrid",
        swing_level=swing_result.swing_level
    )


def calculate_tp_sl(
    df: pd.DataFrame,
    entry_price: float,
    signal_direction: int,
    config: Optional[TPSLConfig] = None
) -> TPSLResult:
    """Calculate TP/SL using configured method.
    
    Args:
        df: DataFrame with OHLCV data
        entry_price: Entry price
        signal_direction: Signal direction (1=long, -1=short)
        config: TP/SL configuration (uses defaults if None)
        
    Returns:
        TPSLResult with calculated levels
    """
    if config is None:
        config = TPSLConfig()
    
    # Select method
    if config.method == "atr":
        result = calculate_tp_sl_atr(df, entry_price, signal_direction, config)
    elif config.method == "swing":
        result = calculate_tp_sl_swing(df, entry_price, signal_direction, config)
    elif config.method == "hybrid":
        result = calculate_tp_sl_hybrid(df, entry_price, signal_direction, config)
    else:
        raise ValueError(f"Unknown TP/SL method: {config.method}")
    
    # Validate SL is within limits
    if result.stop_loss_pct < config.min_sl_pct:
        # Widen stop to minimum
        if signal_direction == 1:
            result.stop_loss = entry_price * (1 - config.min_sl_pct)
        else:
            result.stop_loss = entry_price * (1 + config.min_sl_pct)
        
        result.stop_loss_pct = config.min_sl_pct
        
        # Recalculate TP based on R/R
        risk_amount = abs(entry_price - result.stop_loss)
        if signal_direction == 1:
            result.take_profit = entry_price + (risk_amount * config.min_rr_ratio)
        else:
            result.take_profit = entry_price - (risk_amount * config.min_rr_ratio)
        
        result.risk_amount = risk_amount
        result.reward_amount = abs(result.take_profit - entry_price)
        result.take_profit_pct = abs(result.take_profit - entry_price) / entry_price
        result.risk_reward_ratio = config.min_rr_ratio
    
    elif result.stop_loss_pct > config.max_sl_pct:
        # Tighten stop to maximum
        if signal_direction == 1:
            result.stop_loss = entry_price * (1 - config.max_sl_pct)
        else:
            result.stop_loss = entry_price * (1 + config.max_sl_pct)
        
        result.stop_loss_pct = config.max_sl_pct
        
        # Recalculate TP
        risk_amount = abs(entry_price - result.stop_loss)
        if signal_direction == 1:
            result.take_profit = entry_price + (risk_amount * config.min_rr_ratio)
        else:
            result.take_profit = entry_price - (risk_amount * config.min_rr_ratio)
        
        result.risk_amount = risk_amount
        result.reward_amount = abs(result.take_profit - entry_price)
        result.take_profit_pct = abs(result.take_profit - entry_price) / entry_price
        result.risk_reward_ratio = config.min_rr_ratio
    
    # Validate R/R is within limits
    if result.risk_reward_ratio > config.max_rr_ratio:
        # Cap TP to max R/R
        if signal_direction == 1:
            result.take_profit = entry_price + (result.risk_amount * config.max_rr_ratio)
        else:
            result.take_profit = entry_price - (result.risk_amount * config.max_rr_ratio)
        
        result.reward_amount = abs(result.take_profit - entry_price)
        result.take_profit_pct = abs(result.take_profit - entry_price) / entry_price
        result.risk_reward_ratio = config.max_rr_ratio
    
    return result


def adjust_stops_for_volatility(
    result: TPSLResult,
    entry_price: float,
    volatility_regime: Literal["low", "normal", "high"],
    signal_direction: int
) -> TPSLResult:
    """Adjust stops based on volatility regime.
    
    Args:
        result: Original TP/SL result
        entry_price: Entry price
        volatility_regime: Current volatility regime
        signal_direction: Signal direction
        
    Returns:
        Adjusted TPSLResult
    """
    result = result.model_copy()
    
    if volatility_regime == "high":
        # Widen stops in high volatility
        multiplier = 1.2
    elif volatility_regime == "low":
        # Tighten stops in low volatility
        multiplier = 0.8
    else:
        # No adjustment
        return result
    
    # Adjust stops
    risk_distance = abs(entry_price - result.stop_loss)
    new_risk_distance = risk_distance * multiplier
    
    if signal_direction == 1:
        result.stop_loss = entry_price - new_risk_distance
        result.take_profit = entry_price + (new_risk_distance * result.risk_reward_ratio)
    else:
        result.stop_loss = entry_price + new_risk_distance
        result.take_profit = entry_price - (new_risk_distance * result.risk_reward_ratio)
    
    # Recalculate metrics
    result.risk_amount = new_risk_distance
    result.reward_amount = abs(result.take_profit - entry_price)
    result.stop_loss_pct = abs(result.stop_loss - entry_price) / entry_price
    result.take_profit_pct = abs(result.take_profit - entry_price) / entry_price
    
    return result

