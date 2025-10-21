"""Fixtures for strategy comparison testing.

This module provides consistent test data for strategy comparison tests.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.service.strategy_orchestrator import StrategyBacktestResult


def create_strategy_backtest_result(
    strategy_name: str,
    total_return: float,
    cagr: float,
    sharpe_ratio: float,
    max_drawdown: float,
    win_rate: float,
    profit_factor: float,
    expectancy: float,
    total_trades: int,
    winning_trades: int,
    losing_trades: int,
    avg_win: float,
    avg_loss: float,
    volatility: float = 0.15,
    calmar_ratio: float = 1.0,
    sortino_ratio: float = 1.0,
    capital: float = 1000.0,
    risk_pct: float = 0.02,
    lookback_days: int = 90
) -> StrategyBacktestResult:
    """Create a StrategyBacktestResult with specified parameters."""
    return StrategyBacktestResult(
        strategy_name=strategy_name,
        timestamp=datetime.now(),
        total_return=total_return,
        cagr=cagr,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        profit_factor=profit_factor,
        expectancy=expectancy,
        volatility=volatility,
        calmar_ratio=calmar_ratio,
        sortino_ratio=sortino_ratio,
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        avg_win=avg_win,
        avg_loss=avg_loss,
        capital=capital,
        risk_pct=risk_pct,
        lookback_days=lookback_days
    )


def get_high_performing_strategies() -> List[StrategyBacktestResult]:
    """Get a set of high-performing strategy results."""
    return [
        create_strategy_backtest_result(
            strategy_name="MA Crossover (10,20)",
            total_return=0.25,
            cagr=0.20,
            sharpe_ratio=2.1,
            max_drawdown=-0.06,
            win_rate=0.72,
            profit_factor=2.0,
            expectancy=35.0,
            total_trades=50,
            winning_trades=36,
            losing_trades=14,
            avg_win=60.0,
            avg_loss=-25.0,
            volatility=0.10,
            calmar_ratio=3.3,
            sortino_ratio=2.8
        ),
        create_strategy_backtest_result(
            strategy_name="RSI Regime (14)",
            total_return=0.18,
            cagr=0.15,
            sharpe_ratio=1.8,
            max_drawdown=-0.08,
            win_rate=0.68,
            profit_factor=1.8,
            expectancy=28.0,
            total_trades=42,
            winning_trades=29,
            losing_trades=13,
            avg_win=55.0,
            avg_loss=-30.0,
            volatility=0.12,
            calmar_ratio=1.9,
            sortino_ratio=2.2
        ),
        create_strategy_backtest_result(
            strategy_name="Trend EMA (20,50)",
            total_return=0.15,
            cagr=0.12,
            sharpe_ratio=1.5,
            max_drawdown=-0.10,
            win_rate=0.62,
            profit_factor=1.6,
            expectancy=22.0,
            total_trades=38,
            winning_trades=24,
            losing_trades=14,
            avg_win=50.0,
            avg_loss=-32.0,
            volatility=0.14,
            calmar_ratio=1.2,
            sortino_ratio=1.8
        )
    ]


def get_medium_performing_strategies() -> List[StrategyBacktestResult]:
    """Get a set of medium-performing strategy results."""
    return [
        create_strategy_backtest_result(
            strategy_name="MACD Histogram",
            total_return=0.08,
            cagr=0.06,
            sharpe_ratio=1.2,
            max_drawdown=-0.12,
            win_rate=0.55,
            profit_factor=1.3,
            expectancy=15.0,
            total_trades=35,
            winning_trades=19,
            losing_trades=16,
            avg_win=45.0,
            avg_loss=-35.0,
            volatility=0.16,
            calmar_ratio=0.5,
            sortino_ratio=1.4
        ),
        create_strategy_backtest_result(
            strategy_name="Mean Reversion",
            total_return=0.05,
            cagr=0.04,
            sharpe_ratio=0.8,
            max_drawdown=-0.15,
            win_rate=0.52,
            profit_factor=1.1,
            expectancy=8.0,
            total_trades=30,
            winning_trades=16,
            losing_trades=14,
            avg_win=40.0,
            avg_loss=-38.0,
            volatility=0.18,
            calmar_ratio=0.27,
            sortino_ratio=1.0
        )
    ]


def get_low_performing_strategies() -> List[StrategyBacktestResult]:
    """Get a set of low-performing strategy results."""
    return [
        create_strategy_backtest_result(
            strategy_name="Trend EMA (50,200)",
            total_return=-0.05,
            cagr=-0.08,
            sharpe_ratio=-0.3,
            max_drawdown=-0.20,
            win_rate=0.40,
            profit_factor=0.8,
            expectancy=-10.0,
            total_trades=28,
            winning_trades=11,
            losing_trades=17,
            avg_win=35.0,
            avg_loss=-45.0,
            volatility=0.20,
            calmar_ratio=-0.4,
            sortino_ratio=-0.2
        ),
        create_strategy_backtest_result(
            strategy_name="Donchian Breakout",
            total_return=-0.12,
            cagr=-0.15,
            sharpe_ratio=-0.8,
            max_drawdown=-0.25,
            win_rate=0.35,
            profit_factor=0.6,
            expectancy=-20.0,
            total_trades=25,
            winning_trades=9,
            losing_trades=16,
            avg_win=30.0,
            avg_loss=-50.0,
            volatility=0.22,
            calmar_ratio=-0.6,
            sortino_ratio=-0.5
        )
    ]


def get_mixed_performance_strategies() -> List[StrategyBacktestResult]:
    """Get a mixed set of strategy results with varying performance."""
    return (
        get_high_performing_strategies() + 
        get_medium_performing_strategies() + 
        get_low_performing_strategies()
    )


def get_expected_comparison_dataframe() -> pd.DataFrame:
    """Get the expected DataFrame structure for strategy comparison."""
    return pd.DataFrame({
        'Strategy': [
            'MA Crossover (10,20)',
            'RSI Regime (14)', 
            'Trend EMA (20,50)',
            'MACD Histogram',
            'Mean Reversion',
            'Trend EMA (50,200)',
            'Donchian Breakout'
        ],
        'Sharpe': [2.1, 1.8, 1.5, 1.2, 0.8, -0.3, -0.8],
        'CAGR': [0.20, 0.15, 0.12, 0.06, 0.04, -0.08, -0.15],
        'Win Rate': [0.72, 0.68, 0.62, 0.55, 0.52, 0.40, 0.35],
        'Max DD': [-0.06, -0.08, -0.10, -0.12, -0.15, -0.20, -0.25],
        'Profit Factor': [2.0, 1.8, 1.6, 1.3, 1.1, 0.8, 0.6],
        'Expectancy': [35.0, 28.0, 22.0, 15.0, 8.0, -10.0, -20.0],
        'Total Trades': [50, 42, 38, 35, 30, 28, 25],
        'Wins': [36, 29, 24, 19, 16, 11, 9],
        'Losses': [14, 13, 14, 16, 14, 17, 16]
    })


def create_mock_strategy_ranking_service():
    """Create a mock StrategyRankingService for testing."""
    from unittest.mock import Mock
    
    service = Mock()
    service.capital = 1000.0
    service.max_risk_pct = 0.02
    service.lookback_days = 90
    
    return service


def create_mock_orchestrator():
    """Create a mock StrategyOrchestrator for testing."""
    from unittest.mock import Mock
    
    orchestrator = Mock()
    orchestrator.run_all_backtests.return_value = get_mixed_performance_strategies()
    
    return orchestrator


def get_test_symbols_and_timeframes():
    """Get test symbols and timeframes for testing."""
    return [
        ("BTC/USDT", "1h"),
        ("ETH/USDT", "4h"),
        ("BTC/USDT", "1d"),
        ("ETH/USDT", "1h"),
        ("BTC/USDT", "4h")
    ]


def get_error_scenarios():
    """Get various error scenarios for testing."""
    return {
        "empty_results": [],
        "backtest_failure": Exception("Backtest failed"),
        "data_loading_error": Exception("Data loading failed"),
        "service_unavailable": Exception("Service unavailable"),
        "invalid_parameters": ValueError("Invalid parameters")
    }
