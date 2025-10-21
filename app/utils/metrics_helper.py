"""Enhanced metrics calculation helper.

This module provides utilities for calculating comprehensive trading metrics
from backtest results, including equity curves and trade lists.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.service.strategy_orchestrator import StrategyBacktestResult


class MetricsCalculator:
    """Enhanced metrics calculator for trading strategies."""
    
    def __init__(self, risk_free_rate: float = 0.02):
        """Initialize calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino calculations
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_comprehensive_metrics(
        self,
        trades: List[Dict],
        equity_curve: List[float],
        initial_capital: float,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """Calculate comprehensive metrics from trades and equity curve.
        
        Args:
            trades: List of trade dictionaries with pnl, pnl_pct, etc.
            equity_curve: List of equity values over time
            initial_capital: Starting capital
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            Dictionary with comprehensive metrics
        """
        if not trades or not equity_curve:
            return self._empty_metrics()
        
        # Convert to pandas Series for easier calculations
        equity_series = pd.Series(equity_curve)
        trade_pnls = [t.get('pnl', 0) for t in trades]
        trade_pnl_pcts = [t.get('pnl_pct', 0) for t in trades]
        
        # Basic returns
        total_return = (equity_series.iloc[-1] - initial_capital) / initial_capital
        
        # Time-based calculations
        if isinstance(start_date, int):
            start_date = datetime.fromtimestamp(start_date / 1000)
        if isinstance(end_date, int):
            end_date = datetime.fromtimestamp(end_date / 1000)
        
        days = (end_date - start_date).days
        years = days / 365.25 if days > 0 else 1
        
        # CAGR
        cagr = ((1 + total_return) ** (1 / years) - 1) if years > 0 else 0
        
        # Returns series for risk metrics
        returns_series = pd.Series(trade_pnl_pcts)
        
        # Sharpe ratio
        excess_returns = returns_series - (self.risk_free_rate / 252)
        sharpe_ratio = (excess_returns.mean() / returns_series.std() * np.sqrt(252)) if returns_series.std() > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns_series[returns_series < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else returns_series.std()
        sortino_ratio = (excess_returns.mean() / downside_std * np.sqrt(252)) if downside_std > 0 else 0
        
        # Calmar ratio
        max_drawdown = self._calculate_max_drawdown(equity_series)
        calmar_ratio = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Win rate and profit factor
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        gross_profit = sum(t.get('pnl', 0) for t in winning_trades)
        gross_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        # Expectancy
        avg_win = np.mean([t.get('pnl', 0) for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.get('pnl', 0) for t in losing_trades]) if losing_trades else 0
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        # Volatility
        volatility = returns_series.std() * np.sqrt(252)
        
        # Additional metrics
        total_trades = len(trades)
        winning_trades_count = len(winning_trades)
        losing_trades_count = len(losing_trades)
        
        return {
            'total_return': total_return,
            'cagr': cagr,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'total_trades': total_trades,
            'winning_trades': winning_trades_count,
            'losing_trades': losing_trades_count,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }
    
    def _calculate_max_drawdown(self, equity_series: pd.Series) -> float:
        """Calculate maximum drawdown from equity curve."""
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        return drawdown.min()
    
    def _empty_metrics(self) -> Dict[str, float]:
        """Return empty metrics for failed calculations."""
        return {
            'total_return': 0.0,
            'cagr': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'max_drawdown': 0.0,
            'volatility': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'expectancy': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_win': 0.0,
            'avg_loss': 0.0
        }
    
    def enhance_backtest_result(
        self,
        result: StrategyBacktestResult,
        trades: List[Dict],
        equity_curve: List[float]
    ) -> StrategyBacktestResult:
        """Enhance a StrategyBacktestResult with comprehensive metrics.
        
        Args:
            result: Original backtest result
            trades: List of trade dictionaries
            equity_curve: Equity curve over time
            
        Returns:
            Enhanced StrategyBacktestResult
        """
        # Calculate comprehensive metrics
        metrics = self.calculate_comprehensive_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=result.capital,
            start_date=result.timestamp - timedelta(days=90),  # Approximate
            end_date=result.timestamp
        )
        
        # Update result with enhanced metrics
        result.total_return = metrics['total_return']
        result.cagr = metrics['cagr']
        result.sharpe_ratio = metrics['sharpe_ratio']
        result.sortino_ratio = metrics['sortino_ratio']
        result.calmar_ratio = metrics['calmar_ratio']
        result.max_drawdown = metrics['max_drawdown']
        result.volatility = metrics['volatility']
        result.win_rate = metrics['win_rate']
        result.profit_factor = metrics['profit_factor']
        result.expectancy = metrics['expectancy']
        result.total_trades = metrics['total_trades']
        result.winning_trades = metrics['winning_trades']
        result.losing_trades = metrics['losing_trades']
        result.avg_win = metrics['avg_win']
        result.avg_loss = metrics['avg_loss']
        
        return result


def create_enhanced_comparison_dataframe(
    results: List[StrategyBacktestResult]
) -> pd.DataFrame:
    """Create enhanced comparison DataFrame from backtest results.
    
    Args:
        results: List of StrategyBacktestResult objects
        
    Returns:
        DataFrame with comprehensive metrics
    """
    if not results:
        return pd.DataFrame()
    
    comparison_data = []
    for result in results:
        comparison_data.append({
            'Strategy': result.strategy_name,
            'Sharpe': result.sharpe_ratio,
            'Sortino': result.sortino_ratio,
            'Calmar': result.calmar_ratio,
            'CAGR': result.cagr,
            'Win Rate': result.win_rate,
            'Max DD': result.max_drawdown,
            'Profit Factor': result.profit_factor,
            'Expectancy': result.expectancy,
            'Volatility': result.volatility,
            'Total Trades': result.total_trades,
            'Wins': result.winning_trades,
            'Losses': result.losing_trades,
            'Avg Win': result.avg_win,
            'Avg Loss': result.avg_loss
        })
    
    return pd.DataFrame(comparison_data)
