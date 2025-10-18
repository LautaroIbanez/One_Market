"""Backtesting framework for One Market platform.

This package provides a comprehensive backtesting engine with support for:
- Vectorized backtesting using vectorbt
- Walk-forward analysis
- One trade per day rule
- Trading windows enforcement
- OCO TP/SL orders
- Commission and slippage
- Extensive performance metrics
"""

__version__ = "1.0.0"

from app.research.backtest.engine import BacktestEngine, BacktestConfig, BacktestResult
from app.research.backtest.metrics import calculate_metrics
from app.research.backtest.walk_forward import WalkForwardOptimizer, WalkForwardConfig, WalkForwardSummary
from app.research.backtest.rules import (
    enforce_one_trade_per_day,
    filter_by_trading_windows,
    apply_forced_close,
    validate_signals,
    get_trading_statistics
)
from app.research.backtest.monte_carlo import (
    run_monte_carlo,
    MonteCarloResult,
    permute_returns_by_blocks,
    calculate_risk_of_ruin,
    generate_monte_carlo_report
)

__all__ = [
    'BacktestEngine',
    'BacktestConfig',
    'BacktestResult',
    'calculate_metrics',
    'WalkForwardOptimizer',
    'WalkForwardConfig',
    'WalkForwardSummary',
    'enforce_one_trade_per_day',
    'filter_by_trading_windows',
    'apply_forced_close',
    'validate_signals',
    'get_trading_statistics',
    'run_monte_carlo',
    'MonteCarloResult',
    'permute_returns_by_blocks',
    'calculate_risk_of_ruin',
    'generate_monte_carlo_report'
]

