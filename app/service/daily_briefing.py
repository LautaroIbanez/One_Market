"""Daily trading briefing generator.

This module generates comprehensive daily trading briefings with:
- Signal and confidence
- Entry range and price levels
- Risk/reward analysis  
- Performance metrics and context
- Actionable recommendations
"""

import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.service.decision import DailyDecision, DecisionEngine
from app.service.decision_tracker import get_tracker
from app.research.combine import combine_signals
from app.research.signals import generate_signal
import logging

logger = logging.getLogger(__name__)


class BriefingMetrics(BaseModel):
    """Performance metrics for briefing context."""
    
    recent_win_rate: float = Field(..., description="Win rate last 30 days")
    recent_sharpe: float = Field(..., description="Sharpe ratio last 30 days")
    recent_total_pnl: float = Field(..., description="Total PnL last 30 days")
    recent_max_dd: float = Field(..., description="Max drawdown last 30 days")
    recent_avg_pnl: float = Field(..., description="Average PnL per trade")
    total_decisions: int = Field(..., description="Total decisions tracked")
    executed_decisions: int = Field(..., description="Executed decisions")


class DailyBriefing(BaseModel):
    """Complete daily trading briefing."""
    
    # Metadata
    briefing_date: datetime = Field(..., description="Briefing generation date")
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe")
    
    # Decision
    decision: DailyDecision = Field(..., description="Daily decision")
    has_hypothetical_plan: bool = Field(default=False, description="Has hypothetical plan if skipped")
    hypothetical_plan: Optional[Dict[str, Any]] = Field(None, description="Hypothetical plan details")
    
    # Signal breakdown
    signal_direction: str = Field(..., description="LONG/SHORT/FLAT")
    signal_confidence: float = Field(..., description="Signal confidence 0-1")
    signal_source: str = Field(..., description="Signal source/strategy")
    strategy_breakdown: Dict[str, int] = Field(..., description="Individual strategy signals")
    
    # Trading plan
    entry_price: Optional[float] = Field(None, description="Entry price")
    stop_loss: Optional[float] = Field(None, description="Stop loss")
    take_profit: Optional[float] = Field(None, description="Take profit")
    entry_range_low: Optional[float] = Field(None, description="Entry range low")
    entry_range_high: Optional[float] = Field(None, description="Entry range high")
    risk_reward_ratio: Optional[float] = Field(None, description="R:R ratio")
    
    # Position sizing
    position_quantity: Optional[float] = Field(None, description="Position size")
    position_notional: Optional[float] = Field(None, description="Position notional value")
    risk_amount: Optional[float] = Field(None, description="Risk amount in $")
    risk_pct: float = Field(..., description="Risk percentage")
    
    # Market context
    current_price: float = Field(..., description="Current market price")
    atr_value: Optional[float] = Field(None, description="Current ATR")
    volatility_state: str = Field(default="normal", description="Volatility state")
    
    # Performance context
    metrics: Optional[BriefingMetrics] = Field(None, description="Recent performance metrics")
    
    # Recommendation
    should_execute: bool = Field(..., description="Should execute trade")
    skip_reason: Optional[str] = Field(None, description="Reason for skip")
    recommendation: str = Field(..., description="Trading recommendation text")
    risk_warning: Optional[str] = Field(None, description="Risk warnings")
    
    # Validation
    validation_checks: Dict[str, bool] = Field(..., description="Validation checks passed")
    
    class Config:
        arbitrary_types_allowed = True


def calculate_entry_range(entry_price: float, atr: float, beta: float = 0.003) -> tuple[float, float]:
    """Calculate entry range around entry price.
    
    Args:
        entry_price: Target entry price
        atr: Current ATR
        beta: Beta adjustment factor
        
    Returns:
        Tuple of (range_low, range_high)
    """
    spread = entry_price * beta
    return entry_price - spread, entry_price + spread


def assess_volatility_state(df: pd.DataFrame, atr_period: int = 14, lookback: int = 50) -> str:
    """Assess current volatility state.
    
    Args:
        df: DataFrame with OHLCV data
        atr_period: ATR calculation period
        lookback: Lookback period for comparison
        
    Returns:
        Volatility state: "low", "normal", "high", "extreme"
    """
    from app.core.risk import calculate_atr
    
    atr = calculate_atr(df['high'], df['low'], df['close'], period=atr_period)
    current_atr = atr.iloc[-1]
    
    # Compare to historical ATR
    if len(atr) < lookback:
        return "normal"
    
    historical_atr = atr.iloc[-lookback:]
    atr_percentile = (historical_atr < current_atr).sum() / len(historical_atr)
    
    if atr_percentile < 0.2:
        return "low"
    elif atr_percentile < 0.4:
        return "normal"
    elif atr_percentile < 0.8:
        return "high"
    else:
        return "extreme"


def generate_recommendation_text(
    decision: DailyDecision,
    hypothetical_plan: Optional[Dict[str, Any]],
    metrics: Optional[BriefingMetrics],
    volatility_state: str
) -> str:
    """Generate trading recommendation text.
    
    Args:
        decision: Daily decision
        hypothetical_plan: Hypothetical plan if skipped
        metrics: Performance metrics
        volatility_state: Volatility state
        
    Returns:
        Recommendation text
    """
    lines = []
    
    # Decision status
    if decision.should_execute:
        lines.append(f"✅ **EXECUTE TRADE**: {decision.signal_source}")
        lines.append(f"**Direction**: {'LONG' if decision.signal > 0 else 'SHORT'}")
        lines.append(f"**Confidence**: {decision.signal_strength:.1%}")
        
        if decision.entry_price:
            lines.append(f"\n**Entry Plan**:")
            lines.append(f"• Target Entry: ${decision.entry_price:,.2f}")
            lines.append(f"• Stop Loss: ${decision.stop_loss:,.2f}")
            lines.append(f"• Take Profit: ${decision.take_profit:,.2f}")
            
            if decision.position_size:
                lines.append(f"\n**Position**:")
                lines.append(f"• Size: {decision.position_size.quantity:.4f} units")
                lines.append(f"• Notional: ${decision.position_size.notional_value:,.2f}")
                lines.append(f"• Risk: ${decision.position_size.risk_amount:,.2f} ({decision.position_size.risk_pct:.1%})")
    
    else:
        lines.append(f"⏸️ **SKIP TRADE**: {decision.skip_reason or 'No conditions met'}")
        
        if hypothetical_plan and hypothetical_plan.get('has_plan'):
            lines.append(f"\n**Hypothetical Plan** (if conditions were met):")
            lines.append(f"• Direction: {hypothetical_plan['side']}")
            lines.append(f"• Entry: ${hypothetical_plan['entry_price']:,.2f}")
            lines.append(f"• Stop Loss: ${hypothetical_plan['stop_loss']:,.2f}")
            lines.append(f"• Take Profit: ${hypothetical_plan['take_profit']:,.2f}")
            lines.append(f"• R:R Ratio: {hypothetical_plan['risk_reward_ratio']:.2f}")
    
    # Market context
    lines.append(f"\n**Market Context**:")
    lines.append(f"• Volatility: {volatility_state.upper()}")
    
    # Performance context
    if metrics:
        lines.append(f"\n**Recent Performance** (30d):")
        lines.append(f"• Win Rate: {metrics.recent_win_rate:.1%}")
        lines.append(f"• Sharpe: {metrics.recent_sharpe:.2f}")
        lines.append(f"• Total PnL: ${metrics.recent_total_pnl:,.2f}")
        lines.append(f"• Trades: {metrics.executed_decisions}/{metrics.total_decisions}")
    
    return "\n".join(lines)


def generate_daily_briefing(
    symbol: str,
    timeframe: str,
    df: pd.DataFrame,
    strategies: Optional[list] = None,
    combination_method: str = "simple_average",
    capital: float = 100000.0,
    risk_pct: float = 0.02
) -> DailyBriefing:
    """Generate complete daily trading briefing.
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe
        df: DataFrame with OHLCV data
        strategies: List of strategies to use (default: all available)
        combination_method: Signal combination method
        capital: Available capital
        risk_pct: Risk percentage per trade
        
    Returns:
        DailyBriefing with complete analysis
    """
    logger.info(f"Generating daily briefing for {symbol} {timeframe}")
    
    # Default strategies
    if strategies is None:
        strategies = ['ma_crossover', 'rsi_regime_pullback', 'macd_histogram_atr_filter']
    
    # Generate signals
    strategy_signals = {}
    strategy_breakdown = {}
    
    for strategy in strategies:
        try:
            sig = generate_signal(strategy, df)
            strategy_signals[strategy] = sig.signal
            strategy_breakdown[strategy] = int(sig.signal.iloc[-1])
        except Exception as e:
            logger.warning(f"Strategy {strategy} failed: {e}")
    
    if not strategy_signals:
        raise ValueError("No strategies generated signals")
    
    # Combine signals
    returns = df['close'].pct_change()
    combined = combine_signals(
        strategy_signals,
        method=combination_method,
        returns=returns if combination_method == "sharpe_weighted" else None
    )
    
    current_signal = int(combined.signal.iloc[-1])
    signal_confidence = float(combined.confidence.iloc[-1])
    
    # Make decision
    engine = DecisionEngine(default_risk_pct=risk_pct)
    decision = engine.make_decision(
        df,
        combined.signal,
        signal_strength=combined.confidence,
        signal_source=f"{combination_method}_ensemble",
        capital=capital,
        risk_pct=risk_pct
    )
    
    # Calculate hypothetical plan if skipped
    hypothetical_plan = None
    has_hypothetical = False
    
    if not decision.should_execute and current_signal != 0:
        hypothetical_plan = engine.calculate_hypothetical_plan(
            df,
            current_signal,
            signal_confidence,
            capital,
            risk_pct
        )
        has_hypothetical = hypothetical_plan.get('has_plan', False)
    
    # Get performance metrics
    tracker = get_tracker()
    perf_metrics_raw = tracker.get_performance_metrics(days=30)
    
    metrics = BriefingMetrics(
        recent_win_rate=perf_metrics_raw['win_rate'],
        recent_sharpe=perf_metrics_raw['sharpe_ratio'],
        recent_total_pnl=perf_metrics_raw['total_pnl'],
        recent_max_dd=perf_metrics_raw['max_drawdown'],
        recent_avg_pnl=perf_metrics_raw['avg_pnl'],
        total_decisions=perf_metrics_raw['total_decisions'],
        executed_decisions=perf_metrics_raw['executed_decisions']
    )
    
    # Assess market state
    volatility_state = assess_volatility_state(df)
    current_price = float(df['close'].iloc[-1])
    
    # Extract trading plan details
    entry_price = decision.entry_price
    stop_loss = decision.stop_loss
    take_profit = decision.take_profit
    atr_value = decision.atr_value
    
    # Calculate entry range
    entry_range_low, entry_range_high = None, None
    if entry_price and atr_value:
        entry_range_low, entry_range_high = calculate_entry_range(
            entry_price,
            atr_value,
            beta=decision.entry_band_beta or 0.003
        )
    
    # Calculate R:R ratio
    risk_reward_ratio = None
    if entry_price and stop_loss and take_profit:
        if decision.signal > 0:  # Long
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:  # Short
            risk = stop_loss - entry_price
            reward = entry_price - take_profit
        
        risk_reward_ratio = reward / risk if risk > 0 else None
    
    # Position sizing
    position_quantity = decision.position_size.quantity if decision.position_size else None
    position_notional = decision.position_size.notional_value if decision.position_size else None
    risk_amount = decision.position_size.risk_amount if decision.position_size else None
    
    # Validation checks
    validation_checks = {
        'has_signal': current_signal != 0,
        'in_trading_hours': decision.window in ['A', 'B'],
        'sufficient_confidence': signal_confidence >= 0.5,
        'valid_entry': entry_price is not None if decision.should_execute else True,
        'valid_stops': (stop_loss is not None and take_profit is not None) if decision.should_execute else True,
        'acceptable_rr': risk_reward_ratio >= 1.5 if risk_reward_ratio else True
    }
    
    # Generate recommendation
    recommendation = generate_recommendation_text(
        decision,
        hypothetical_plan,
        metrics,
        volatility_state
    )
    
    # Risk warnings
    risk_warning = None
    if volatility_state == "extreme":
        risk_warning = "⚠️ EXTREME VOLATILITY - Consider reducing position size"
    elif volatility_state == "high":
        risk_warning = "⚠️ HIGH VOLATILITY - Monitor position closely"
    
    if metrics.recent_win_rate < 0.4:
        if risk_warning:
            risk_warning += " | Recent win rate below 40%"
        else:
            risk_warning = "⚠️ Recent win rate below 40% - Review strategy"
    
    # Build briefing
    briefing = DailyBriefing(
        briefing_date=datetime.now(timezone.utc),
        symbol=symbol,
        timeframe=timeframe,
        decision=decision,
        has_hypothetical_plan=has_hypothetical,
        hypothetical_plan=hypothetical_plan,
        signal_direction='LONG' if current_signal > 0 else ('SHORT' if current_signal < 0 else 'FLAT'),
        signal_confidence=signal_confidence,
        signal_source=decision.signal_source,
        strategy_breakdown=strategy_breakdown,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        entry_range_low=entry_range_low,
        entry_range_high=entry_range_high,
        risk_reward_ratio=risk_reward_ratio,
        position_quantity=position_quantity,
        position_notional=position_notional,
        risk_amount=risk_amount,
        risk_pct=risk_pct,
        current_price=current_price,
        atr_value=atr_value,
        volatility_state=volatility_state,
        metrics=metrics,
        should_execute=decision.should_execute,
        skip_reason=decision.skip_reason,
        recommendation=recommendation,
        risk_warning=risk_warning,
        validation_checks=validation_checks
    )
    
    logger.info(f"Briefing generated: {symbol} {timeframe} - {'EXECUTE' if decision.should_execute else 'SKIP'}")
    
    return briefing


def export_briefing_markdown(briefing: DailyBriefing) -> str:
    """Export briefing as Markdown format.
    
    Args:
        briefing: Daily briefing
        
    Returns:
        Markdown formatted string
    """
    lines = []
    
    lines.append(f"# Daily Trading Briefing")
    lines.append(f"**Date**: {briefing.briefing_date.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"**Symbol**: {briefing.symbol}")
    lines.append(f"**Timeframe**: {briefing.timeframe}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    lines.append(briefing.recommendation)
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Strategy breakdown
    lines.append("## Strategy Breakdown")
    for strategy, signal in briefing.strategy_breakdown.items():
        signal_str = "LONG" if signal > 0 else ("SHORT" if signal < 0 else "FLAT")
        lines.append(f"• **{strategy}**: {signal_str}")
    
    lines.append("")
    
    # Validation
    lines.append("## Validation Checks")
    for check, passed in briefing.validation_checks.items():
        status = "✅" if passed else "❌"
        lines.append(f"{status} {check.replace('_', ' ').title()}")
    
    if briefing.risk_warning:
        lines.append("")
        lines.append("## ⚠️ Warnings")
        lines.append(briefing.risk_warning)
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*Generated by One Market Trading System*")
    
    return "\n".join(lines)

