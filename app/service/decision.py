"""Daily trading decision engine.

This module implements the core logic for generating one trade decision per day:
- Aggregate signals from multiple strategies
- Verify trading windows
- Calculate entry levels (entry band)
- Calculate SL/TP levels
- Position sizing
- Skip window B if window A already executed
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Literal
from datetime import datetime, time
from pydantic import BaseModel, Field

from app.core.calendar import TradingCalendar
from app.core.risk import calculate_position_size_fixed_risk, PositionSize
from app.core.utils import ensure_utc


class DailyDecision(BaseModel):
    """Daily trading decision."""
    
    # Decision metadata
    decision_date: datetime = Field(..., description="Decision date (UTC)")
    trading_day: str = Field(..., description="Trading day (YYYY-MM-DD)")
    window: Literal["A", "B", "none"] = Field(..., description="Trading window")
    
    # Signal
    signal: int = Field(..., description="Signal: 1 (long), -1 (short), 0 (no trade)")
    signal_strength: float = Field(default=0.0, description="Signal strength/confidence")
    signal_source: str = Field(..., description="Source of signal (strategy name)")
    
    # Entry
    should_execute: bool = Field(..., description="Whether to execute trade")
    entry_price: Optional[float] = Field(None, description="Entry price", gt=0)
    entry_mid: Optional[float] = Field(None, description="Entry mid reference (VWAP or typical)")
    entry_band_beta: float = Field(default=0.0, description="Entry band adjustment")
    
    # Stops
    stop_loss: Optional[float] = Field(None, description="Stop loss price", gt=0)
    take_profit: Optional[float] = Field(None, description="Take profit price", gt=0)
    atr_value: Optional[float] = Field(None, description="ATR value used")
    
    # Position sizing
    position_size: Optional[PositionSize] = Field(None, description="Position size calculation")
    
    # Execution tracking
    window_a_executed: bool = Field(default=False, description="Window A already executed today")
    skip_reason: Optional[str] = Field(None, description="Reason for skipping trade")
    
    # Metadata
    market_price: float = Field(..., description="Current market price", gt=0)
    timestamp_ms: int = Field(..., description="Decision timestamp (ms)")
    
    class Config:
        arbitrary_types_allowed = True


class DecisionEngine:
    """Daily decision engine."""
    
    def __init__(
        self,
        calendar: Optional[TradingCalendar] = None,
        default_risk_pct: float = 0.02,
        skip_window_b_if_a_executed: bool = True
    ):
        """Initialize decision engine.
        
        Args:
            calendar: Trading calendar (creates default if None)
            default_risk_pct: Default risk percentage per trade
            skip_window_b_if_a_executed: Skip window B if A already traded
        """
        self.calendar = calendar or TradingCalendar()
        self.default_risk_pct = default_risk_pct
        self.skip_window_b_if_a_executed = skip_window_b_if_a_executed
        
        # Track daily execution
        self._execution_tracker: Dict[str, bool] = {}  # {date: executed_in_window_a}
    
    def make_decision(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        signal_strength: Optional[pd.Series] = None,
        signal_source: str = "combined",
        current_time: Optional[datetime] = None,
        capital: float = 100000.0,
        risk_pct: Optional[float] = None
    ) -> DailyDecision:
        """Make daily trading decision.
        
        Args:
            df: DataFrame with OHLCV data
            signals: Signal series (1=long, -1=short, 0=flat)
            signal_strength: Optional signal strength/confidence
            signal_source: Name of signal source
            current_time: Current time (defaults to now)
            capital: Available capital
            risk_pct: Risk percentage (defaults to engine default)
            
        Returns:
            DailyDecision with all decision details
        """
        # Setup
        if current_time is None:
            current_time = datetime.now()
        current_time = ensure_utc(current_time)
        
        if risk_pct is None:
            risk_pct = self.default_risk_pct
        
        # Get current values
        latest_idx = len(df) - 1
        current_signal = int(signals.iloc[latest_idx])
        current_price = float(df['close'].iloc[latest_idx])
        current_timestamp = int(df['timestamp'].iloc[latest_idx])
        
        strength = float(signal_strength.iloc[latest_idx]) if signal_strength is not None else 0.0
        
        # Get trading window
        current_window = self.calendar.get_current_window(current_time)
        
        # Get trading day
        trading_day = current_time.strftime('%Y-%m-%d')
        
        # Check if already executed today
        window_a_executed = self._execution_tracker.get(trading_day, False)
        
        # Initialize decision
        decision = DailyDecision(
            decision_date=current_time,
            trading_day=trading_day,
            window=current_window if current_window else "none",
            signal=current_signal,
            signal_strength=strength,
            signal_source=signal_source,
            should_execute=False,
            market_price=current_price,
            timestamp_ms=current_timestamp,
            window_a_executed=window_a_executed
        )
        
        # Decision logic
        if current_signal == 0:
            decision.skip_reason = "No signal (flat)"
            return decision
        
        if not self.calendar.is_trading_hours(current_time):
            decision.skip_reason = "Outside trading hours"
            return decision
        
        # Check if too close to forced close
        if not self.calendar.is_valid_entry_time(current_time, min_time_before_close_minutes=30):
            decision.skip_reason = "Too close to forced close time"
            return decision
        
        # Check window B skip rule
        if current_window == "B" and window_a_executed and self.skip_window_b_if_a_executed:
            decision.skip_reason = "Window A already executed today"
            return decision
        
        # Calculate entry levels
        from app.service.entry_band import calculate_entry_band
        
        entry_result = calculate_entry_band(
            df,
            current_price,
            signal_direction=current_signal
        )
        
        decision.entry_price = entry_result.entry_price
        decision.entry_mid = entry_result.entry_mid
        decision.entry_band_beta = entry_result.beta
        
        # Calculate TP/SL
        from app.service.tp_sl_engine import calculate_tp_sl
        
        tp_sl_result = calculate_tp_sl(
            df=df,
            entry_price=decision.entry_price,
            signal_direction=current_signal
        )
        
        decision.stop_loss = tp_sl_result.stop_loss
        decision.take_profit = tp_sl_result.take_profit
        decision.atr_value = tp_sl_result.atr_value
        
        # Calculate position size
        position = calculate_position_size_fixed_risk(
            capital=capital,
            risk_pct=risk_pct,
            entry_price=decision.entry_price,
            stop_loss=decision.stop_loss,
            leverage=1.0
        )
        
        decision.position_size = position
        decision.should_execute = True
        
        # Mark as executed if in window A
        if current_window == "A":
            self._execution_tracker[trading_day] = True
        
        return decision
    
    def reset_daily_tracker(self):
        """Reset daily execution tracker."""
        self._execution_tracker.clear()
    
    def get_execution_status(self, date: str) -> bool:
        """Check if already executed on a given date.
        
        Args:
            date: Date string (YYYY-MM-DD)
            
        Returns:
            True if already executed in window A
        """
        return self._execution_tracker.get(date, False)
    
    def read_aggregated_signals(
        self,
        df: pd.DataFrame,
        strategy_signals: Dict[str, pd.Series],
        combination_method: str = "sharpe_weighted"
    ) -> tuple[pd.Series, Optional[pd.Series]]:
        """Read and aggregate signals from multiple strategies.
        
        Args:
            df: DataFrame with OHLCV data
            strategy_signals: Dictionary of {strategy_name: signal_series}
            combination_method: Method to combine signals
            
        Returns:
            Tuple of (combined_signal, signal_strength)
        """
        from app.research.combine import combine_signals
        
        # Calculate returns for Sharpe weighting
        returns = df['close'].pct_change()
        
        # Combine signals
        combined = combine_signals(
            signals=strategy_signals,
            method=combination_method,
            returns=returns if combination_method == "sharpe_weighted" else None
        )
        
        return combined.signal, combined.confidence

