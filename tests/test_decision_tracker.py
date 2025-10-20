"""Tests for decision tracking and feedback system."""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock

from app.service.decision_tracker import DecisionTracker, DecisionOutcome
from app.service.decision import DailyDecision


class TestDecisionTracker:
    """Test decision tracking and feedback functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_tracker_initialization(self):
        """Test tracker initialization."""
        tracker = DecisionTracker(storage_path=self.temp_path)
        
        assert tracker.storage_path == self.temp_path
        assert tracker.decisions_file == self.temp_path / "decision_history.json"
        assert tracker.outcomes_file == self.temp_path / "decision_outcomes.json"
        assert len(tracker._decisions) == 0
        assert len(tracker._outcomes) == 0
    
    def test_record_decision(self):
        """Test recording a decision."""
        tracker = DecisionTracker(storage_path=self.temp_path)
        
        # Create test decision
        decision = DailyDecision(
            decision_date=datetime.now(timezone.utc),
            trading_day=datetime.now().strftime('%Y-%m-%d'),
            window="A",
            signal=1,
            signal_strength=0.8,
            signal_source="test_strategy",
            should_execute=True,
            entry_price=105.0,
            stop_loss=100.0,
            take_profit=110.0,
            entry_mid=105.0,
            market_price=105.0,
            timestamp_ms=int(datetime.now().timestamp() * 1000)
        )
        
        # Record decision
        decision_id = tracker.record_decision(decision)
        
        # Verify decision was recorded
        assert decision_id is not None
        assert decision_id in tracker._decisions
        assert tracker._decisions[decision_id] == decision
        
        # Verify file was created
        assert tracker.decisions_file.exists()
    
    def test_record_outcome(self):
        """Test recording decision outcome."""
        tracker = DecisionTracker(storage_path=self.temp_path)
        
        # Create and record decision
        decision = DailyDecision(
            decision_date=datetime.now(timezone.utc),
            trading_day=datetime.now().strftime('%Y-%m-%d'),
            window="A",
            signal=1,
            signal_strength=0.8,
            signal_source="test_strategy",
            should_execute=True,
            entry_price=105.0,
            stop_loss=100.0,
            take_profit=110.0,
            entry_mid=105.0,
            market_price=105.0,
            timestamp_ms=int(datetime.now().timestamp() * 1000)
        )
        
        decision_id = tracker.record_decision(decision)
        
        # Record outcome
        tracker.record_outcome(
            decision_id=decision_id,
            outcome_price=108.0,
            pnl=3.0,
            pnl_pct=0.0286,
            was_executed=True,
            execution_price=105.0,
            exit_price=108.0,
            exit_reason="TP"
        )
        
        # Verify outcome was recorded
        assert decision_id in tracker._outcomes
        outcome = tracker._outcomes[decision_id]
        assert outcome.pnl == 3.0
        assert outcome.pnl_pct == 0.0286
        assert outcome.was_executed is True
        assert outcome.exit_reason == "TP"
    
    def test_performance_metrics(self):
        """Test performance metrics calculation."""
        tracker = DecisionTracker(storage_path=self.temp_path)
        
        # Create multiple decisions with outcomes
        decisions_data = [
            (1, True, 5.0, 0.05),   # Winning trade
            (1, True, -2.0, -0.02), # Losing trade
            (1, True, 3.0, 0.03),   # Winning trade
            (0, False, 0.0, 0.0),   # Skipped trade
            (1, True, 1.0, 0.01),   # Winning trade
        ]
        
        for i, (signal, executed, pnl, pnl_pct) in enumerate(decisions_data):
            decision = DailyDecision(
                decision_date=datetime.now(timezone.utc) - timedelta(days=i),
                trading_day=(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                window="A",
                signal=signal,
                signal_strength=0.7,
                signal_source="test_strategy",
                should_execute=executed,
                entry_price=105.0 if executed else None,
                stop_loss=100.0 if executed else None,
                take_profit=110.0 if executed else None,
                entry_mid=105.0 if executed else None,
                market_price=105.0,
                timestamp_ms=int(datetime.now().timestamp() * 1000)
            )
            
            decision_id = tracker.record_decision(decision)
            
            if executed:
                tracker.record_outcome(
                    decision_id=decision_id,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    was_executed=executed
                )
        
        # Get metrics
        metrics = tracker.get_performance_metrics(days=10)
        
        # Verify metrics
        assert metrics['total_decisions'] == 4  # Only decisions with outcomes
        assert metrics['executed_decisions'] == 4
        assert metrics['skip_rate'] == 0.0  # All executed
        assert metrics['win_rate'] == 0.75  # 3 out of 4 winning trades
        assert metrics['total_pnl'] == 7.0  # 5 + (-2) + 3 + 1
        assert metrics['avg_pnl'] == 1.75  # 7.0 / 4
        # Confidence is not stored in outcomes, so it will be 0.0
        assert metrics['avg_confidence'] == 0.0
    
    def test_skip_reasons_summary(self):
        """Test skip reasons summary."""
        tracker = DecisionTracker(storage_path=self.temp_path)
        
        # Create decisions with different skip reasons
        skip_reasons = ["Volatilidad alta", "Volatilidad alta", "Riesgo bajo", "Sin señal"]
        
        for i, reason in enumerate(skip_reasons):
            decision = DailyDecision(
                decision_date=datetime.now(timezone.utc) - timedelta(days=i),
                trading_day=(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                window="A",
                signal=0,
                signal_strength=0.5,
                signal_source="test_strategy",
                should_execute=False,
                skip_reason=reason,
                market_price=105.0,
                timestamp_ms=int(datetime.now().timestamp() * 1000)
            )
            
            decision_id = tracker.record_decision(decision)
            tracker.record_outcome(
                decision_id=decision_id,
                was_executed=False
            )
        
        # Get skip reasons summary
        summary = tracker.get_skip_reasons_summary(days=10)
        
        # Verify summary
        assert summary["Volatilidad alta"] == 2
        assert summary["Riesgo bajo"] == 1
        assert summary["Sin señal"] == 1
    
    def test_rolling_metrics(self):
        """Test rolling metrics calculation."""
        tracker = DecisionTracker(storage_path=self.temp_path)
        
        # Create multiple decisions with outcomes over time
        base_date = datetime.now(timezone.utc) - timedelta(days=10)
        
        for i in range(10):
            decision = DailyDecision(
                decision_date=base_date + timedelta(days=i),
                trading_day=(base_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                window="A",
                signal=1,
                signal_strength=0.7 + (i * 0.02),  # Increasing confidence
                signal_source="test_strategy",
                should_execute=True,
                entry_price=105.0,
                stop_loss=100.0,
                take_profit=110.0,
                entry_mid=105.0,
                market_price=105.0,
                timestamp_ms=int(datetime.now().timestamp() * 1000)
            )
            
            decision_id = tracker.record_decision(decision)
            
            # Alternate winning/losing trades
            pnl = 5.0 if i % 2 == 0 else -2.0
            tracker.record_outcome(
                decision_id=decision_id,
                pnl=pnl,
                pnl_pct=pnl / 105.0,
                was_executed=True
            )
        
        # Get rolling metrics
        rolling_df = tracker.get_rolling_metrics(days=10, window=3)
        
        # Verify rolling metrics
        assert not rolling_df.empty
        assert 'rolling_pnl' in rolling_df.columns
        assert 'rolling_win_rate' in rolling_df.columns
        assert 'rolling_confidence' in rolling_df.columns
        
        # Check that rolling metrics are calculated
        assert rolling_df['rolling_pnl'].notna().any()
        assert rolling_df['rolling_win_rate'].notna().any()
        assert rolling_df['rolling_confidence'].notna().any()
    
    def test_data_persistence(self):
        """Test that data persists across tracker instances."""
        # Create first tracker instance
        tracker1 = DecisionTracker(storage_path=self.temp_path)
        
        decision = DailyDecision(
            decision_date=datetime.now(timezone.utc),
            trading_day=datetime.now().strftime('%Y-%m-%d'),
            window="A",
            signal=1,
            signal_strength=0.8,
            signal_source="test_strategy",
            should_execute=True,
            entry_price=105.0,
            stop_loss=100.0,
            take_profit=110.0,
            entry_mid=105.0,
            market_price=105.0,
            timestamp_ms=int(datetime.now().timestamp() * 1000)
        )
        
        decision_id = tracker1.record_decision(decision)
        
        # Create second tracker instance (should load persisted data)
        tracker2 = DecisionTracker(storage_path=self.temp_path)
        
        # Verify data was loaded
        assert decision_id in tracker2._decisions
        assert tracker2._decisions[decision_id] == decision


if __name__ == "__main__":
    pytest.main([__file__])
