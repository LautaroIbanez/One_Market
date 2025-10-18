"""Risk management utilities for position sizing, stop loss, and take profit calculations.

This module provides functions for calculating ATR-based stops, position sizing
using various methods including Kelly criterion, and risk/reward computations.
"""
from typing import Optional, Tuple, List, Dict
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, field_validator


class PositionSize(BaseModel):
    """Position sizing result."""
    
    quantity: float = Field(..., description="Position size (in base currency units)", gt=0)
    notional_value: float = Field(..., description="Notional value in quote currency", gt=0)
    risk_amount: float = Field(..., description="Amount at risk", ge=0)
    risk_pct: float = Field(..., description="Percentage of capital at risk", ge=0, le=1)
    leverage: float = Field(default=1.0, description="Leverage used", ge=1.0)
    
    @field_validator('risk_pct')
    @classmethod
    def validate_risk_pct(cls, v):
        """Ensure risk percentage is reasonable."""
        if v > 0.1:  # More than 10% per trade
            raise ValueError(f"Risk percentage {v:.2%} exceeds maximum allowed (10%)")
        return v


class StopLossTakeProfit(BaseModel):
    """Stop loss and take profit levels."""
    
    entry_price: float = Field(..., description="Entry price", gt=0)
    stop_loss: float = Field(..., description="Stop loss price", gt=0)
    take_profit: Optional[float] = Field(None, description="Take profit price", gt=0)
    side: str = Field(..., description="Position side ('long' or 'short')")
    risk_amount: float = Field(..., description="Risk amount per unit", gt=0)
    reward_amount: Optional[float] = Field(None, description="Reward amount per unit")
    risk_reward_ratio: Optional[float] = Field(None, description="Risk/reward ratio")
    stop_loss_pct: float = Field(..., description="Stop loss percentage from entry")
    take_profit_pct: Optional[float] = Field(None, description="Take profit percentage from entry")
    
    @field_validator('side')
    @classmethod
    def validate_side(cls, v):
        """Validate position side."""
        if v.lower() not in ['long', 'short']:
            raise ValueError(f"Invalid side: {v}. Must be 'long' or 'short'")
        return v.lower()


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR).
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        period: ATR period (default: 14)
        
    Returns:
        Series of ATR values
    """
    # Calculate True Range
    high_low = high - low
    high_close_prev = abs(high - close.shift(1))
    low_close_prev = abs(low - close.shift(1))
    
    tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
    
    # Calculate ATR as exponential moving average of TR
    atr = tr.ewm(span=period, adjust=False).mean()
    
    return atr


def calculate_atr_from_bars(bars: List[Dict], period: int = 14) -> float:
    """Calculate current ATR from a list of OHLCV bars.
    
    Args:
        bars: List of OHLCV bar dictionaries with 'high', 'low', 'close' keys
        period: ATR period (default: 14)
        
    Returns:
        Current ATR value
        
    Raises:
        ValueError: If insufficient data
    """
    if len(bars) < period + 1:
        raise ValueError(f"Insufficient bars for ATR calculation. Need {period + 1}, got {len(bars)}")
    
    df = pd.DataFrame(bars)
    atr = calculate_atr(df['high'], df['low'], df['close'], period)
    
    return float(atr.iloc[-1])


def compute_levels(
    entry_price: float,
    atr: float,
    side: str,
    atr_multiplier_sl: float = 2.0,
    atr_multiplier_tp: float = 3.0,
    min_rr_ratio: float = 1.5
) -> StopLossTakeProfit:
    """Compute stop loss and take profit levels based on ATR.
    
    Args:
        entry_price: Entry price
        atr: Current ATR value
        side: Position side ('long' or 'short')
        atr_multiplier_sl: ATR multiplier for stop loss (default: 2.0)
        atr_multiplier_tp: ATR multiplier for take profit (default: 3.0)
        min_rr_ratio: Minimum risk/reward ratio (default: 1.5)
        
    Returns:
        StopLossTakeProfit object with calculated levels
        
    Raises:
        ValueError: If parameters are invalid
    """
    if entry_price <= 0:
        raise ValueError(f"Entry price must be positive, got {entry_price}")
    
    if atr <= 0:
        raise ValueError(f"ATR must be positive, got {atr}")
    
    side = side.lower()
    if side not in ['long', 'short']:
        raise ValueError(f"Invalid side: {side}. Must be 'long' or 'short'")
    
    # Calculate stop loss
    if side == 'long':
        stop_loss = entry_price - (atr * atr_multiplier_sl)
        take_profit = entry_price + (atr * atr_multiplier_tp)
        risk_amount = entry_price - stop_loss
        reward_amount = take_profit - entry_price
    else:  # short
        stop_loss = entry_price + (atr * atr_multiplier_sl)
        take_profit = entry_price - (atr * atr_multiplier_tp)
        risk_amount = stop_loss - entry_price
        reward_amount = entry_price - take_profit
    
    # Ensure stop loss is positive
    if stop_loss <= 0:
        raise ValueError(f"Calculated stop loss {stop_loss} is not positive")
    
    # Calculate percentages
    stop_loss_pct = abs((stop_loss - entry_price) / entry_price)
    take_profit_pct = abs((take_profit - entry_price) / entry_price)
    
    # Calculate risk/reward ratio
    risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
    
    # Validate minimum R/R ratio
    if risk_reward_ratio < min_rr_ratio:
        # Adjust take profit to meet minimum R/R
        reward_amount = risk_amount * min_rr_ratio
        if side == 'long':
            take_profit = entry_price + reward_amount
        else:
            take_profit = entry_price - reward_amount
        take_profit_pct = abs((take_profit - entry_price) / entry_price)
        risk_reward_ratio = min_rr_ratio
    
    return StopLossTakeProfit(
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        side=side,
        risk_amount=risk_amount,
        reward_amount=reward_amount,
        risk_reward_ratio=risk_reward_ratio,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct
    )


def calculate_position_size_fixed_risk(
    capital: float,
    risk_pct: float,
    entry_price: float,
    stop_loss: float,
    leverage: float = 1.0
) -> PositionSize:
    """Calculate position size using fixed risk percentage.
    
    Args:
        capital: Total trading capital
        risk_pct: Risk percentage (0.01 = 1%)
        entry_price: Entry price
        stop_loss: Stop loss price
        leverage: Leverage to use (default: 1.0)
        
    Returns:
        PositionSize object
        
    Raises:
        ValueError: If parameters are invalid
    """
    if capital <= 0:
        raise ValueError(f"Capital must be positive, got {capital}")
    
    if not 0 < risk_pct <= 0.1:
        raise ValueError(f"Risk percentage must be between 0 and 10%, got {risk_pct:.2%}")
    
    if entry_price <= 0 or stop_loss <= 0:
        raise ValueError("Entry price and stop loss must be positive")
    
    if leverage < 1:
        raise ValueError(f"Leverage must be >= 1, got {leverage}")
    
    # Calculate risk amount
    risk_amount_total = capital * risk_pct
    
    # Calculate risk per unit
    risk_per_unit = abs(entry_price - stop_loss)
    
    if risk_per_unit == 0:
        raise ValueError("Entry price and stop loss cannot be the same")
    
    # Calculate position size
    quantity = risk_amount_total / risk_per_unit
    
    # Apply leverage to notional value
    notional_value = quantity * entry_price
    
    return PositionSize(
        quantity=quantity,
        notional_value=notional_value,
        risk_amount=risk_amount_total,
        risk_pct=risk_pct,
        leverage=leverage
    )


def calculate_position_size_kelly(
    capital: float,
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    kelly_fraction: float = 0.25,
    max_risk_pct: float = 0.05
) -> float:
    """Calculate position size using Kelly Criterion (fractional).
    
    Args:
        capital: Total trading capital
        win_rate: Historical win rate (0.0 to 1.0)
        avg_win: Average win amount (as percentage, e.g., 0.03 = 3%)
        avg_loss: Average loss amount (as percentage, e.g., 0.015 = 1.5%)
        kelly_fraction: Fraction of Kelly to use (default: 0.25 = quarter Kelly)
        max_risk_pct: Maximum risk percentage cap (default: 0.05 = 5%)
        
    Returns:
        Risk percentage to use
        
    Raises:
        ValueError: If parameters are invalid
        
    Note:
        Kelly formula: f* = (p * b - q) / b
        where:
        - p = win rate
        - q = loss rate (1 - p)
        - b = avg_win / avg_loss ratio
    """
    if not 0 <= win_rate <= 1:
        raise ValueError(f"Win rate must be between 0 and 1, got {win_rate}")
    
    if avg_win <= 0:
        raise ValueError(f"Average win must be positive, got {avg_win}")
    
    if avg_loss <= 0:
        raise ValueError(f"Average loss must be positive, got {avg_loss}")
    
    if not 0 < kelly_fraction <= 1:
        raise ValueError(f"Kelly fraction must be between 0 and 1, got {kelly_fraction}")
    
    # Calculate Kelly percentage
    loss_rate = 1 - win_rate
    win_loss_ratio = avg_win / avg_loss
    
    kelly_pct = (win_rate * win_loss_ratio - loss_rate) / win_loss_ratio
    
    # Apply fractional Kelly
    kelly_pct = max(0, kelly_pct * kelly_fraction)
    
    # Cap at maximum risk
    risk_pct = min(kelly_pct, max_risk_pct)
    
    return risk_pct


def calculate_position_size_kelly_simple(
    capital: float,
    win_rate: float,
    risk_reward_ratio: float,
    kelly_fraction: float = 0.25,
    max_risk_pct: float = 0.05
) -> float:
    """Simplified Kelly Criterion using risk/reward ratio.
    
    Args:
        capital: Total trading capital
        win_rate: Historical win rate (0.0 to 1.0)
        risk_reward_ratio: Risk/reward ratio (e.g., 2.0 means reward is 2x risk)
        kelly_fraction: Fraction of Kelly to use (default: 0.25)
        max_risk_pct: Maximum risk percentage cap (default: 0.05 = 5%)
        
    Returns:
        Risk percentage to use
        
    Note:
        Simplified formula: f* = (p * R - q) / R
        where R is risk/reward ratio
    """
    if not 0 <= win_rate <= 1:
        raise ValueError(f"Win rate must be between 0 and 1, got {win_rate}")
    
    if risk_reward_ratio <= 0:
        raise ValueError(f"Risk/reward ratio must be positive, got {risk_reward_ratio}")
    
    loss_rate = 1 - win_rate
    
    # Kelly percentage
    kelly_pct = (win_rate * risk_reward_ratio - loss_rate) / risk_reward_ratio
    
    # Apply fractional Kelly
    kelly_pct = max(0, kelly_pct * kelly_fraction)
    
    # Cap at maximum
    risk_pct = min(kelly_pct, max_risk_pct)
    
    return risk_pct


def calculate_var(
    returns: pd.Series,
    confidence_level: float = 0.95,
    method: str = "historical"
) -> float:
    """Calculate Value at Risk (VaR).
    
    Args:
        returns: Series of returns
        confidence_level: Confidence level (default: 0.95 = 95%)
        method: Calculation method ('historical' or 'parametric')
        
    Returns:
        VaR value (as positive number representing potential loss)
    """
    if method == "historical":
        # Historical VaR (percentile method)
        var = -returns.quantile(1 - confidence_level)
    elif method == "parametric":
        # Parametric VaR (assuming normal distribution)
        from scipy import stats
        mean = returns.mean()
        std = returns.std()
        z_score = stats.norm.ppf(1 - confidence_level)
        var = -(mean + z_score * std)
    else:
        raise ValueError(f"Unknown VaR method: {method}")
    
    return float(var)


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """Calculate Sharpe ratio.
    
    Args:
        returns: Series of returns
        risk_free_rate: Risk-free rate (annualized)
        periods_per_year: Number of periods in a year (252 for daily)
        
    Returns:
        Sharpe ratio
    """
    if len(returns) == 0:
        return 0.0
    
    excess_returns = returns - (risk_free_rate / periods_per_year)
    
    if excess_returns.std() == 0:
        return 0.0
    
    sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(periods_per_year)
    
    return float(sharpe)


def calculate_max_drawdown(equity_curve: pd.Series) -> Tuple[float, int, int]:
    """Calculate maximum drawdown from equity curve.
    
    Args:
        equity_curve: Series of equity values
        
    Returns:
        Tuple of (max_drawdown_pct, peak_idx, trough_idx)
    """
    if len(equity_curve) == 0:
        return (0.0, 0, 0)
    
    # Calculate running maximum
    running_max = equity_curve.expanding().max()
    
    # Calculate drawdown
    drawdown = (equity_curve - running_max) / running_max
    
    # Find maximum drawdown
    max_dd_idx = drawdown.idxmin()
    max_dd = abs(drawdown.loc[max_dd_idx])
    
    # Find peak (start of drawdown)
    peak_idx = equity_curve[:max_dd_idx].idxmax()
    
    return (float(max_dd), int(peak_idx), int(max_dd_idx))


def validate_position_size(
    quantity: float,
    entry_price: float,
    capital: float,
    max_position_pct: float = 0.2
) -> Tuple[bool, str]:
    """Validate that position size is within acceptable limits.
    
    Args:
        quantity: Position quantity
        entry_price: Entry price
        capital: Total capital
        max_position_pct: Maximum position size as percentage of capital
        
    Returns:
        Tuple of (is_valid, message)
    """
    notional_value = quantity * entry_price
    position_pct = notional_value / capital
    
    if position_pct > max_position_pct:
        return (False, f"Position size {position_pct:.2%} exceeds maximum {max_position_pct:.2%}")
    
    if quantity <= 0:
        return (False, f"Invalid quantity: {quantity}")
    
    if notional_value > capital:
        return (False, f"Position value ${notional_value:.2f} exceeds capital ${capital:.2f}")
    
    return (True, "Position size is valid")


def adjust_position_for_correlation(
    base_position_size: float,
    portfolio_positions: List[Dict],
    correlation_matrix: pd.DataFrame,
    new_symbol: str,
    reduction_factor: float = 0.5
) -> float:
    """Adjust position size based on portfolio correlation.
    
    Args:
        base_position_size: Base position size before correlation adjustment
        portfolio_positions: List of existing positions with 'symbol' and 'size'
        correlation_matrix: Correlation matrix of symbols
        new_symbol: Symbol for new position
        reduction_factor: Factor to reduce size for correlated positions (default: 0.5)
        
    Returns:
        Adjusted position size
    """
    if not portfolio_positions or correlation_matrix.empty:
        return base_position_size
    
    # Calculate average correlation with existing positions
    correlations = []
    for pos in portfolio_positions:
        symbol = pos['symbol']
        if symbol in correlation_matrix.index and new_symbol in correlation_matrix.columns:
            corr = abs(correlation_matrix.loc[symbol, new_symbol])
            correlations.append(corr)
    
    if not correlations:
        return base_position_size
    
    avg_correlation = np.mean(correlations)
    
    # Reduce position size based on correlation
    # High correlation (close to 1) -> more reduction
    adjustment_factor = 1 - (avg_correlation * reduction_factor)
    
    return base_position_size * adjustment_factor

