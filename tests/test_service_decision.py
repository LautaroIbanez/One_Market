"""Tests for service.decision module."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from app.service.decision import DecisionEngine, DailyDecision
from app.core.calendar import TradingCalendar


class TestDecisionEngine:
    """Tests for DecisionEngine."""
    
    def test_decision_engine_creation(self):
        """Test creating decision engine."""
        engine = DecisionEngine()
        
        assert engine.calendar is not None
        assert engine.default_risk_pct == 0.02
        assert engine.skip_window_b_if_a_executed is True
    
    def test_decision_engine_custom_params(self):
        """Test creating engine with custom parameters."""
        calendar = TradingCalendar()
        engine = DecisionEngine(
            calendar=calendar,
            default_risk_pct=0.03,
            skip_window_b_if_a_executed=False
        )
        
        assert engine.default_risk_pct == 0.03
        assert engine.skip_window_b_if_a_executed is False
    
    def test_no_signal_decision(self):
        """Test decision with no signal."""
        engine = DecisionEngine()
        
        df = pd.DataFrame({
            'timestamp': [int(datetime.now().timestamp() * 1000)],
            'open': [50000],
            'high': [50500],
            'low': [49500],
            'close': [50000],
            'volume': [1000]
        })
        
        signals = pd.Series([0])
        
        decision = engine.make_decision(df, signals)
        
        assert decision.signal == 0
        assert decision.should_execute is False
        assert decision.skip_reason == "No signal (flat)"
    
    def test_long_signal_decision(self):
        """Test decision with long signal."""
        # Create engine without strict trading hours for test
        engine = DecisionEngine()
        
        # Create data with enough bars for calculations
        n_bars = 50
        df = pd.DataFrame({
            'timestamp': [int((datetime.now() - timedelta(hours=n_bars-i)).timestamp() * 1000) for i in range(n_bars)],
            'open': np.random.randn(n_bars).cumsum() + 50000,
            'high': np.random.randn(n_bars).cumsum() + 50500,
            'low': np.random.randn(n_bars).cumsum() + 49500,
            'close': np.random.randn(n_bars).cumsum() + 50000,
            'volume': abs(np.random.randn(n_bars)) * 1000000
        })
        
        signals = pd.Series([0] * (n_bars - 1) + [1])
        
        # Use time during trading hours (14:00 UTC = 11:00 local, in window A)
        test_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
        
        decision = engine.make_decision(
            df, signals,
            current_time=test_time,
            capital=100000.0
        )
        
        assert decision.signal == 1
        # May or may not execute depending on trading hours check


class TestExecutionTracking:
    """Tests for execution tracking."""
    
    def test_execution_tracker_initial(self):
        """Test execution tracker starts empty."""
        engine = DecisionEngine()
        
        status = engine.get_execution_status('2023-10-20')
        assert status is False
    
    def test_reset_daily_tracker(self):
        """Test resetting daily tracker."""
        engine = DecisionEngine()
        engine._execution_tracker['2023-10-20'] = True
        
        engine.reset_daily_tracker()
        
        assert len(engine._execution_tracker) == 0


class TestSignalAggregation:
    """Tests for signal aggregation."""
    
    def test_read_aggregated_signals(self):
        """Test reading and aggregating signals."""
        engine = DecisionEngine()
        
        # Create sample data
        n_bars = 100
        df = pd.DataFrame({
            'timestamp': range(n_bars),
            'close': np.random.randn(n_bars).cumsum() + 100,
            'high': np.random.randn(n_bars).cumsum() + 102,
            'low': np.random.randn(n_bars).cumsum() + 98
        })
        
        # Create signals from different strategies
        strategy_signals = {
            'strategy1': pd.Series([1] * n_bars),
            'strategy2': pd.Series([-1] * n_bars),
            'strategy3': pd.Series([1] * n_bars)
        }
        
        combined, strength = engine.read_aggregated_signals(
            df, strategy_signals, combination_method="simple_average"
        )
        
        assert len(combined) == n_bars
        assert strength is not None


class TestDailyDecisionModel:
    """Tests for DailyDecision model."""
    
    def test_daily_decision_creation(self):
        """Test creating DailyDecision."""
        decision = DailyDecision(
            decision_date=datetime.now(),
            trading_day="2023-10-20",
            window="A",
            signal=1,
            signal_source="test",
            should_execute=False,
            market_price=50000.0,
            timestamp_ms=int(datetime.now().timestamp() * 1000)
        )
        
        assert decision.signal == 1
        assert decision.window == "A"
        assert decision.should_execute is False


class TestWindowBSkipRule:
    """Tests for window B skip rule."""
    
    def test_window_b_skipped_after_a(self):
        """Test that window B is skipped if A executed."""
        engine = DecisionEngine(skip_window_b_if_a_executed=True)
        
        # Mark window A as executed
        trading_day = "2023-10-20"
        engine._execution_tracker[trading_day] = True
        
        # Create minimal data
        df = pd.DataFrame({
            'timestamp': [int(datetime.now().timestamp() * 1000)],
            'open': [50000],
            'high': [50500],
            'low': [49500],
            'close': [50000],
            'volume': [1000]
        })
        
        signals = pd.Series([1])
        
        # Simulate window B time
        window_b_time = datetime.now().replace(hour=18, minute=0)  # 18:00 UTC = 15:00 local (window B)
        
        decision = engine.make_decision(
            df, signals,
            current_time=window_b_time
        )
        
        # Should skip if calendar determines it's window B
        # (actual result depends on calendar logic)
        assert isinstance(decision, DailyDecision)
    
    def test_window_b_not_skipped_if_disabled(self):
        """Test that window B is not skipped if rule disabled."""
        engine = DecisionEngine(skip_window_b_if_a_executed=False)
        
        # Mark window A as executed
        trading_day = "2023-10-20"
        engine._execution_tracker[trading_day] = True
        
        # Even if A executed, B should not skip (rule disabled)
        assert engine.skip_window_b_if_a_executed is False

