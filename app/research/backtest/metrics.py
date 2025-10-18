"""Performance metrics calculation.

This module provides functions to calculate trading performance metrics.
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


def calculate_cagr(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Calculate Compound Annual Growth Rate.
    
    Args:
        returns: Returns series
        periods_per_year: Number of periods in a year
        
    Returns:
        CAGR
    """
    if len(returns) == 0:
        return 0.0
    
    total_return = (1 + returns).prod() - 1
    years = len(returns) / periods_per_year
    
    if years <= 0:
        return 0.0
    
    cagr = (1 + total_return) ** (1 / years) - 1
    return float(cagr)


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """Calculate Sharpe ratio.
    
    Args:
        returns: Returns series
        risk_free_rate: Risk-free rate (annualized)
        periods_per_year: Number of periods in a year
        
    Returns:
        Sharpe ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    
    excess_returns = returns - (risk_free_rate / periods_per_year)
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(periods_per_year)
    
    return float(sharpe)


def calculate_sortino_ratio(
    returns: pd.Series,
    target_return: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """Calculate Sortino ratio.
    
    Args:
        returns: Returns series
        target_return: Target return (annualized)
        periods_per_year: Number of periods in a year
        
    Returns:
        Sortino ratio
    """
    if len(returns) == 0:
        return 0.0
    
    excess_returns = returns - (target_return / periods_per_year)
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0.0
    
    sortino = (excess_returns.mean() / downside_returns.std()) * np.sqrt(periods_per_year)
    
    return float(sortino)


def calculate_max_drawdown(equity_curve: pd.Series) -> tuple[float, int, int]:
    """Calculate maximum drawdown.
    
    Args:
        equity_curve: Equity curve series
        
    Returns:
        Tuple of (max_drawdown, peak_idx, trough_idx)
    """
    if len(equity_curve) == 0:
        return 0.0, 0, 0
    
    running_max = equity_curve.expanding().max()
    drawdown = (equity_curve - running_max) / running_max
    
    max_dd_idx = drawdown.idxmin()
    max_dd = abs(drawdown.loc[max_dd_idx])
    
    # Find peak
    peak_idx = equity_curve[:max_dd_idx].idxmax()
    
    return float(max_dd), int(peak_idx), int(max_dd_idx)


def calculate_calmar_ratio(cagr: float, max_drawdown: float) -> float:
    """Calculate Calmar ratio.
    
    Args:
        cagr: CAGR
        max_drawdown: Maximum drawdown
        
    Returns:
        Calmar ratio
    """
    if max_drawdown == 0:
        return 0.0
    
    return float(cagr / abs(max_drawdown))


def calculate_mar_ratio(cagr: float, avg_drawdown: float) -> float:
    """Calculate MAR ratio.
    
    Args:
        cagr: CAGR
        avg_drawdown: Average drawdown
        
    Returns:
        MAR ratio
    """
    if avg_drawdown == 0:
        return 0.0
    
    return float(cagr / abs(avg_drawdown))


def calculate_profit_factor(trades: pd.DataFrame) -> float:
    """Calculate profit factor.
    
    Args:
        trades: Trades DataFrame with 'pnl' column
        
    Returns:
        Profit factor
    """
    if len(trades) == 0:
        return 0.0
    
    wins = trades[trades['pnl'] > 0]['pnl'].sum()
    losses = abs(trades[trades['pnl'] < 0]['pnl'].sum())
    
    if losses == 0:
        return 0.0
    
    return float(wins / losses)


def calculate_expectancy(trades: pd.DataFrame) -> float:
    """Calculate expectancy (expected value per trade).
    
    Args:
        trades: Trades DataFrame with 'pnl' column
        
    Returns:
        Expectancy
    """
    if len(trades) == 0:
        return 0.0
    
    win_rate = (trades['pnl'] > 0).mean()
    avg_win = trades[trades['pnl'] > 0]['pnl'].mean() if (trades['pnl'] > 0).any() else 0
    avg_loss = abs(trades[trades['pnl'] < 0]['pnl'].mean()) if (trades['pnl'] < 0).any() else 0
    
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
    
    return float(expectancy)


def calculate_recovery_factor(total_return: float, max_drawdown: float) -> float:
    """Calculate recovery factor.
    
    Args:
        total_return: Total return
        max_drawdown: Maximum drawdown
        
    Returns:
        Recovery factor
    """
    if max_drawdown == 0:
        return 0.0
    
    return float(total_return / abs(max_drawdown))


def calculate_ulcer_index(equity_curve: pd.Series, period: int = 14) -> float:
    """Calculate Ulcer Index (measure of downside volatility).
    
    Args:
        equity_curve: Equity curve series
        period: Lookback period
        
    Returns:
        Ulcer Index
    """
    if len(equity_curve) < period:
        return 0.0
    
    running_max = equity_curve.rolling(window=period).max()
    drawdown_pct = ((equity_curve - running_max) / running_max) * 100
    ulcer = np.sqrt((drawdown_pct ** 2).sum() / period)
    
    return float(ulcer)


def calculate_omega_ratio(returns: pd.Series, threshold: float = 0.0) -> float:
    """Calculate Omega ratio.
    
    Args:
        returns: Returns series
        threshold: Threshold return
        
    Returns:
        Omega ratio
    """
    if len(returns) == 0:
        return 0.0
    
    gains = returns[returns > threshold] - threshold
    losses = threshold - returns[returns < threshold]
    
    if losses.sum() == 0:
        return 0.0
    
    omega = gains.sum() / losses.sum()
    
    return float(omega)


def calculate_metrics(portfolio, periods_per_year: int = 252) -> Dict[str, Any]:
    """Calculate all metrics from portfolio.
    
    Args:
        portfolio: vectorbt Portfolio object
        periods_per_year: Number of periods in a year
        
    Returns:
        Dictionary with all metrics
    """
    # Get returns and equity
    returns = portfolio.returns()
    equity = portfolio.value()
    
    # Basic metrics
    total_return = portfolio.total_return()
    cagr = calculate_cagr(returns, periods_per_year)
    
    # Risk-adjusted metrics
    sharpe = calculate_sharpe_ratio(returns, periods_per_year=periods_per_year)
    sortino = calculate_sortino_ratio(returns, periods_per_year=periods_per_year)
    
    # Drawdown metrics
    max_dd, peak_idx, trough_idx = calculate_max_drawdown(equity)
    drawdown = portfolio.drawdown()
    avg_dd = abs(drawdown.drawdown().mean())
    
    calmar = calculate_calmar_ratio(cagr, max_dd)
    mar = calculate_mar_ratio(cagr, avg_dd)
    recovery = calculate_recovery_factor(total_return, max_dd)
    
    # Trade metrics
    trades = portfolio.trades.records_readable if hasattr(portfolio.trades, 'records_readable') else pd.DataFrame()
    
    if len(trades) > 0:
        profit_factor = calculate_profit_factor(trades)
        expectancy = calculate_expectancy(trades)
        
        win_rate = (trades['PnL'] > 0).mean() if 'PnL' in trades.columns else 0
        avg_trade = trades['PnL'].mean() if 'PnL' in trades.columns else 0
    else:
        profit_factor = 0
        expectancy = 0
        win_rate = 0
        avg_trade = 0
    
    # Additional metrics
    volatility = returns.std() * np.sqrt(periods_per_year)
    ulcer = calculate_ulcer_index(equity)
    omega = calculate_omega_ratio(returns)
    
    return {
        'total_return': float(total_return),
        'cagr': float(cagr),
        'sharpe_ratio': float(sharpe),
        'sortino_ratio': float(sortino),
        'calmar_ratio': float(calmar),
        'mar_ratio': float(mar),
        'max_drawdown': float(max_dd),
        'avg_drawdown': float(avg_dd),
        'recovery_factor': float(recovery),
        'profit_factor': float(profit_factor),
        'expectancy': float(expectancy),
        'win_rate': float(win_rate),
        'avg_trade': float(avg_trade),
        'volatility': float(volatility),
        'ulcer_index': float(ulcer),
        'omega_ratio': float(omega)
    }

