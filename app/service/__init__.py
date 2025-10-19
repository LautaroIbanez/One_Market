"""Daily decision service for One Market platform.

This package provides the daily trading decision logic:
- One operation per day
- Entry band calculation (VWAP-based)
- TP/SL engine with ATR and swing levels
- Multi-horizon advisor (short/medium/long term)
- Trade execution decision
- Paper trading database
- Strategy orchestrator and ranking (v2.0)
"""

__version__ = "2.0.0"

from app.service.decision import DecisionEngine, DailyDecision
from app.service.entry_band import (
    calculate_entry_band,
    calculate_entry_mid_vwap,
    calculate_entry_mid_typical_price,
    EntryBandResult
)
from app.service.tp_sl_engine import (
    calculate_tp_sl,
    TPSLConfig,
    TPSLResult,
    adjust_stops_for_volatility
)
from app.service.advisor import (
    MarketAdvisor,
    MultiHorizonAdvice,
    ShortTermAdvice,
    MediumTermAdvice,
    LongTermAdvice,
    integrate_backtest_metrics
)
from app.service.paper_trading import PaperTradingDB
from app.service.strategy_orchestrator import StrategyOrchestrator, StrategyBacktestResult
from app.service.strategy_ranking import StrategyRankingService, StrategyRecommendation

__all__ = [
    'DecisionEngine',
    'DailyDecision',
    'calculate_entry_band',
    'EntryBandResult',
    'calculate_tp_sl',
    'TPSLConfig',
    'TPSLResult',
    'MarketAdvisor',
    'MultiHorizonAdvice',
    'PaperTradingDB',
    'integrate_backtest_metrics',
    'StrategyOrchestrator',
    'StrategyRankingService',
    'StrategyRecommendation'
]

