"""Decision tracking and feedback system.

This module tracks daily trading decisions and their outcomes,
providing feedback for improving future decisions.
"""

import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import logging

from app.service.decision import DailyDecision
from app.data.last_update import get_tracker

logger = logging.getLogger(__name__)


class DecisionOutcome(BaseModel):
    """Outcome of a trading decision."""
    
    decision_id: str = Field(..., description="Unique decision identifier")
    decision_date: datetime = Field(..., description="Date of decision")
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe")
    
    # Decision details
    should_execute: bool = Field(..., description="Whether trade was executed")
    signal: int = Field(..., description="Signal: 1 (long), -1 (short), 0 (no trade)")
    entry_price: Optional[float] = Field(None, description="Entry price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    
    # Outcome details
    outcome_price: Optional[float] = Field(None, description="Price when outcome was measured")
    outcome_timestamp: Optional[datetime] = Field(None, description="When outcome was measured")
    pnl: Optional[float] = Field(None, description="Profit/Loss")
    pnl_pct: Optional[float] = Field(None, description="Profit/Loss percentage")
    
    # Execution details
    was_executed: bool = Field(default=False, description="Whether trade was actually executed")
    execution_price: Optional[float] = Field(None, description="Actual execution price")
    exit_price: Optional[float] = Field(None, description="Actual exit price")
    exit_timestamp: Optional[datetime] = Field(None, description="Actual exit timestamp")
    exit_reason: Optional[str] = Field(None, description="Reason for exit (SL, TP, manual)")
    
    # Metadata
    skip_reason: Optional[str] = Field(None, description="Reason for skipping if not executed")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    signal_strength: Optional[float] = Field(None, description="Signal strength")
    
    class Config:
        arbitrary_types_allowed = True


class DecisionTracker:
    """Tracks trading decisions and their outcomes."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        from app.config.settings import settings
        self.storage_path = storage_path or settings.STORAGE_PATH
        self.decisions_file = self.storage_path / "decision_history.json"
        self.outcomes_file = self.storage_path / "decision_outcomes.json"
        self._decisions: Dict[str, DailyDecision] = {}
        self._outcomes: Dict[str, DecisionOutcome] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """Load decision and outcome data from storage."""
        # Load decisions
        if self.decisions_file.exists():
            try:
                with open(self.decisions_file, 'r') as f:
                    data = json.load(f)
                
                for key, decision_data in data.items():
                    # Convert datetime strings back to datetime objects
                    if 'decision_date' in decision_data:
                        decision_data['decision_date'] = datetime.fromisoformat(decision_data['decision_date'])
                    if 'timestamp_ms' in decision_data:
                        decision_data['timestamp_ms'] = int(decision_data['timestamp_ms'])
                    
                    self._decisions[key] = DailyDecision(**decision_data)
                
                logger.info(f"Loaded {len(self._decisions)} decisions")
            except Exception as e:
                logger.error(f"Error loading decisions: {e}")
                self._decisions = {}
        else:
            self._decisions = {}
        
        # Load outcomes
        if self.outcomes_file.exists():
            try:
                with open(self.outcomes_file, 'r') as f:
                    data = json.load(f)
                
                for key, outcome_data in data.items():
                    # Convert datetime strings back to datetime objects
                    if 'decision_date' in outcome_data:
                        outcome_data['decision_date'] = datetime.fromisoformat(outcome_data['decision_date'])
                    if 'outcome_timestamp' in outcome_data and outcome_data['outcome_timestamp']:
                        outcome_data['outcome_timestamp'] = datetime.fromisoformat(outcome_data['outcome_timestamp'])
                    if 'exit_timestamp' in outcome_data and outcome_data['exit_timestamp']:
                        outcome_data['exit_timestamp'] = datetime.fromisoformat(outcome_data['exit_timestamp'])
                    
                    self._outcomes[key] = DecisionOutcome(**outcome_data)
                
                logger.info(f"Loaded {len(self._outcomes)} outcomes")
            except Exception as e:
                logger.error(f"Error loading outcomes: {e}")
                self._outcomes = {}
        else:
            self._outcomes = {}
    
    def _save_data(self) -> None:
        """Save decision and outcome data to storage."""
        # Save decisions
        try:
            decisions_data = {}
            for key, decision in self._decisions.items():
                decision_dict = decision.dict()
                # Convert datetime to ISO string
                if 'decision_date' in decision_dict:
                    decision_dict['decision_date'] = decision.decision_date.isoformat()
                decisions_data[key] = decision_dict
            
            with open(self.decisions_file, 'w') as f:
                json.dump(decisions_data, f, indent=2)
            
            logger.debug(f"Saved {len(self._decisions)} decisions")
        except Exception as e:
            logger.error(f"Error saving decisions: {e}")
        
        # Save outcomes
        try:
            outcomes_data = {}
            for key, outcome in self._outcomes.items():
                outcome_dict = outcome.dict()
                # Convert datetime to ISO string
                if 'decision_date' in outcome_dict:
                    outcome_dict['decision_date'] = outcome.decision_date.isoformat()
                if 'outcome_timestamp' in outcome_dict and outcome_dict['outcome_timestamp']:
                    outcome_dict['outcome_timestamp'] = outcome.outcome_timestamp.isoformat()
                if 'exit_timestamp' in outcome_dict and outcome_dict['exit_timestamp']:
                    outcome_dict['exit_timestamp'] = outcome.exit_timestamp.isoformat()
                outcomes_data[key] = outcome_dict
            
            with open(self.outcomes_file, 'w') as f:
                json.dump(outcomes_data, f, indent=2)
            
            logger.debug(f"Saved {len(self._outcomes)} outcomes")
        except Exception as e:
            logger.error(f"Error saving outcomes: {e}")
    
    def _get_decision_key(self, decision: DailyDecision) -> str:
        """Generate unique key for decision."""
        # Use signal_source as symbol proxy and default timeframe
        symbol = getattr(decision, 'signal_source', 'unknown')
        timeframe = getattr(decision, 'timeframe', '1h')
        return f"{decision.decision_date.strftime('%Y%m%d')}_{symbol}_{timeframe}"
    
    def record_decision(self, decision: DailyDecision) -> str:
        """Record a trading decision."""
        key = self._get_decision_key(decision)
        self._decisions[key] = decision
        self._save_data()
        
        logger.info(f"Recorded decision: {key}")
        return key
    
    def record_outcome(
        self,
        decision_id: str,
        outcome_price: Optional[float] = None,
        pnl: Optional[float] = None,
        pnl_pct: Optional[float] = None,
        was_executed: bool = False,
        execution_price: Optional[float] = None,
        exit_price: Optional[float] = None,
        exit_reason: Optional[str] = None
    ) -> None:
        """Record the outcome of a decision."""
        if decision_id not in self._decisions:
            logger.warning(f"Decision {decision_id} not found")
            return
        
        decision = self._decisions[decision_id]
        
        outcome = DecisionOutcome(
            decision_id=decision_id,
            decision_date=decision.decision_date,
            symbol=getattr(decision, 'signal_source', 'unknown'),  # Using signal_source as symbol proxy
            timeframe=getattr(decision, 'timeframe', '1h'),  # Default timeframe
            should_execute=decision.should_execute,
            signal=decision.signal,
            entry_price=decision.entry_price,
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit,
            outcome_price=outcome_price,
            outcome_timestamp=datetime.now(timezone.utc),
            pnl=pnl,
            pnl_pct=pnl_pct,
            was_executed=was_executed,
            execution_price=execution_price,
            exit_price=exit_price,
            exit_reason=exit_reason,
            skip_reason=decision.skip_reason,
            confidence_score=getattr(decision, 'confidence_score', None),
            signal_strength=decision.signal_strength
        )
        
        self._outcomes[decision_id] = outcome
        self._save_data()
        
        logger.info(f"Recorded outcome for decision: {decision_id}")
    
    def get_decision_history(self, days: int = 30) -> List[DailyDecision]:
        """Get decision history for the last N days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        return [
            decision for decision in self._decisions.values()
            if decision.decision_date >= cutoff_date
        ]
    
    def get_outcome_history(self, days: int = 30) -> List[DecisionOutcome]:
        """Get outcome history for the last N days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        return [
            outcome for outcome in self._outcomes.values()
            if outcome.decision_date >= cutoff_date
        ]
    
    def get_performance_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get performance metrics for the last N days."""
        outcomes = self.get_outcome_history(days)
        
        if not outcomes:
            return {
                'total_decisions': 0,
                'executed_decisions': 0,
                'win_rate': 0.0,
                'avg_pnl': 0.0,
                'total_pnl': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'skip_rate': 0.0,
                'avg_confidence': 0.0
            }
        
        # Basic metrics
        total_decisions = len(outcomes)
        executed_decisions = sum(1 for o in outcomes if o.was_executed)
        skip_rate = (total_decisions - executed_decisions) / total_decisions if total_decisions > 0 else 0
        
        # PnL metrics (only for executed trades)
        executed_outcomes = [o for o in outcomes if o.was_executed and o.pnl is not None]
        
        if executed_outcomes:
            pnls = [o.pnl for o in executed_outcomes]
            winning_trades = [o for o in executed_outcomes if o.pnl > 0]
            losing_trades = [o for o in executed_outcomes if o.pnl < 0]
            
            win_rate = len(winning_trades) / len(executed_outcomes) if executed_outcomes else 0
            avg_pnl = sum(pnls) / len(pnls)
            total_pnl = sum(pnls)
            
            # Drawdown calculation
            cumulative_pnl = pd.Series(pnls).cumsum()
            running_max = cumulative_pnl.expanding().max()
            drawdown = (cumulative_pnl - running_max) / running_max
            max_drawdown = drawdown.min() if len(drawdown) > 0 else 0
            
            # Sharpe ratio (simplified)
            if len(pnls) > 1:
                sharpe_ratio = (avg_pnl / pd.Series(pnls).std()) if pd.Series(pnls).std() > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            win_rate = 0.0
            avg_pnl = 0.0
            total_pnl = 0.0
            max_drawdown = 0.0
            sharpe_ratio = 0.0
        
        # Confidence metrics
        confidence_scores = [o.confidence_score for o in outcomes if o.confidence_score is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            'total_decisions': total_decisions,
            'executed_decisions': executed_decisions,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'total_pnl': total_pnl,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'skip_rate': skip_rate,
            'avg_confidence': avg_confidence,
            'days_analyzed': days
        }
    
    def get_skip_reasons_summary(self, days: int = 30) -> Dict[str, int]:
        """Get summary of skip reasons."""
        outcomes = self.get_outcome_history(days)
        skip_reasons = {}
        
        for outcome in outcomes:
            if not outcome.was_executed and outcome.skip_reason:
                skip_reasons[outcome.skip_reason] = skip_reasons.get(outcome.skip_reason, 0) + 1
        
        return skip_reasons
    
    def get_rolling_metrics(self, days: int = 30, window: int = 7) -> pd.DataFrame:
        """Get rolling performance metrics."""
        outcomes = self.get_outcome_history(days)
        
        if not outcomes:
            return pd.DataFrame()
        
        # Create DataFrame
        df_data = []
        for outcome in outcomes:
            if outcome.was_executed and outcome.pnl is not None:
                df_data.append({
                    'date': outcome.decision_date.date(),
                    'pnl': outcome.pnl,
                    'pnl_pct': outcome.pnl_pct or 0,
                    'confidence': outcome.confidence_score or 0,
                    'signal_strength': outcome.signal_strength or 0
                })
        
        if not df_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(df_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Calculate rolling metrics
        df['rolling_pnl'] = df['pnl'].rolling(window=window, min_periods=1).sum()
        df['rolling_win_rate'] = (df['pnl'] > 0).rolling(window=window, min_periods=1).mean()
        df['rolling_avg_pnl'] = df['pnl'].rolling(window=window, min_periods=1).mean()
        df['rolling_confidence'] = df['confidence'].rolling(window=window, min_periods=1).mean()
        
        return df


# Global instance
_tracker = None


def get_tracker() -> DecisionTracker:
    """Get global decision tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = DecisionTracker()
    return _tracker


def record_decision(decision: DailyDecision) -> str:
    """Record a trading decision (convenience function)."""
    tracker = get_tracker()
    return tracker.record_decision(decision)


def record_outcome(
    decision_id: str,
    outcome_price: Optional[float] = None,
    pnl: Optional[float] = None,
    pnl_pct: Optional[float] = None,
    was_executed: bool = False,
    execution_price: Optional[float] = None,
    exit_price: Optional[float] = None,
    exit_reason: Optional[str] = None
) -> None:
    """Record decision outcome (convenience function)."""
    tracker = get_tracker()
    tracker.record_outcome(
        decision_id, outcome_price, pnl, pnl_pct, was_executed,
        execution_price, exit_price, exit_reason
    )


def get_performance_metrics(days: int = 30) -> Dict[str, Any]:
    """Get performance metrics (convenience function)."""
    tracker = get_tracker()
    return tracker.get_performance_metrics(days)
