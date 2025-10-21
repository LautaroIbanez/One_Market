"""Tests to ensure one trade per day rule is enforced.

This module tests that the backtest engine properly enforces
the one trade per day rule.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np

from app.research.backtest.engine import BacktestEngine, BacktestConfig, BacktestResult


class TestOneTradePerDayEnforced:
    """Test that one trade per day rule is enforced."""
    
    @pytest.fixture
    def sample_data_with_multiple_signals(self):
        """Create sample data with multiple signals per day."""
        # Create data for 3 days with multiple signals per day
        dates = []
        prices = []
        
        # Day 1: Multiple signals
        for hour in range(24):
            date = datetime(2022, 1, 1, hour, 0, 0, tzinfo=timezone.utc)
            dates.append(date)
            prices.append(50000 + hour * 10)  # Slight upward trend
        
        # Day 2: Multiple signals
        for hour in range(24):
            date = datetime(2022, 1, 2, hour, 0, 0, tzinfo=timezone.utc)
            dates.append(date)
            prices.append(50000 + hour * 5)  # Slower trend
        
        # Day 3: Multiple signals
        for hour in range(24):
            date = datetime(2022, 1, 3, hour, 0, 0, tzinfo=timezone.utc)
            dates.append(date)
            prices.append(50000 + hour * 15)  # Faster trend
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': [int(d.timestamp() * 1000) for d in dates],
            'open': prices,
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices],
            'close': prices,
            'volume': [1000] * len(prices)
        })
        
        return df
    
    @pytest.fixture
    def multiple_signals_per_day(self, sample_data_with_multiple_signals):
        """Create signals with multiple entries per day."""
        # Generate signals that would trigger multiple trades per day
        signals = []
        
        for i, row in sample_data_with_multiple_signals.iterrows():
            # Create signals every 4 hours (6 signals per day)
            if i % 4 == 0:
                signals.append(1)  # Long signal
            elif i % 4 == 2:
                signals.append(-1)  # Short signal
            else:
                signals.append(0)  # No signal
        
        return pd.Series(signals)
    
    def test_one_trade_per_day_enabled(self, sample_data_with_multiple_signals, multiple_signals_per_day):
        """Test that one trade per day rule is enforced when enabled."""
        config = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,
            force_close=True,
            one_trade_per_day=True  # Enable rule
        )
        
        engine = BacktestEngine(config)
        result = engine.run(sample_data_with_multiple_signals, multiple_signals_per_day, "test_strategy", verbose=False)
        
        assert result is not None
        assert result.total_trades > 0
        
        # Verify that we have at most 3 trades (one per day)
        assert result.total_trades <= 3, f"Expected at most 3 trades, got {result.total_trades}"
        
        # Verify that trades are distributed across different days
        if result.trades:
            trade_dates = set()
            for trade in result.trades:
                trade_date = datetime.fromtimestamp(trade['entry_time'] / 1000, tz=timezone.utc).date()
                trade_dates.add(trade_date)
            
            # Should have trades on different days
            assert len(trade_dates) <= 3, f"Expected trades on at most 3 different days, got {len(trade_dates)}"
    
    def test_one_trade_per_day_disabled(self, sample_data_with_multiple_signals, multiple_signals_per_day):
        """Test that multiple trades per day are allowed when rule is disabled."""
        config = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,
            force_close=True,
            one_trade_per_day=False  # Disable rule
        )
        
        engine = BacktestEngine(config)
        result = engine.run(sample_data_with_multiple_signals, multiple_signals_per_day, "test_strategy", verbose=False)
        
        assert result is not None
        assert result.total_trades > 0
        
        # With rule disabled, we should have more trades
        # (exact number depends on signal processing, but should be > 3)
        assert result.total_trades > 3, f"Expected more than 3 trades with rule disabled, got {result.total_trades}"
    
    def test_one_trade_per_day_with_forced_close(self, sample_data_with_multiple_signals, multiple_signals_per_day):
        """Test one trade per day rule with forced close enabled."""
        config = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,
            force_close=True,  # Force close at end of day
            one_trade_per_day=True
        )
        
        engine = BacktestEngine(config)
        result = engine.run(sample_data_with_multiple_signals, multiple_signals_per_day, "test_strategy", verbose=False)
        
        assert result is not None
        
        # Verify that all trades are properly closed
        if result.trades:
            for trade in result.trades:
                assert trade['status'] == 'CLOSED', f"Trade should be closed: {trade}"
                assert trade['exit_time'] is not None, "Trade should have exit time"
    
    def test_one_trade_per_day_edge_case_same_day_signals(self):
        """Test edge case where multiple signals occur on the same day."""
        # Create data for a single day with multiple signals
        dates = [datetime(2022, 1, 1, hour, 0, 0, tzinfo=timezone.utc) for hour in range(24)]
        
        df = pd.DataFrame({
            'timestamp': [int(d.timestamp() * 1000) for d in dates],
            'open': [50000] * 24,
            'high': [51000] * 24,
            'low': [49000] * 24,
            'close': [50000] * 24,
            'volume': [1000] * 24
        })
        
        # Create signals every hour (24 signals)
        signals = pd.Series([1 if i % 2 == 0 else 0 for i in range(24)])
        
        config = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,
            force_close=True,
            one_trade_per_day=True
        )
        
        engine = BacktestEngine(config)
        result = engine.run(df, signals, "test_strategy", verbose=False)
        
        assert result is not None
        
        # Should have at most 1 trade for the single day
        assert result.total_trades <= 1, f"Expected at most 1 trade for single day, got {result.total_trades}"
    
    def test_one_trade_per_day_with_trading_windows(self, sample_data_with_multiple_signals, multiple_signals_per_day):
        """Test one trade per day rule with trading windows enabled."""
        config = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,  # Enable trading windows
            force_close=True,
            one_trade_per_day=True
        )
        
        engine = BacktestEngine(config)
        result = engine.run(sample_data_with_multiple_signals, multiple_signals_per_day, "test_strategy", verbose=False)
        
        assert result is not None
        
        # Verify that trades respect both trading windows and one trade per day
        if result.trades:
            trade_dates = set()
            for trade in result.trades:
                trade_date = datetime.fromtimestamp(trade['entry_time'] / 1000, tz=timezone.utc).date()
                trade_dates.add(trade_date)
            
            # Should have at most one trade per day
            assert len(trade_dates) >= result.total_trades, "Should have at most one trade per day"
    
    def test_one_trade_per_day_performance_impact(self, sample_data_with_multiple_signals, multiple_signals_per_day):
        """Test that one trade per day rule doesn't significantly impact performance calculation."""
        # Test with rule enabled
        config_enabled = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,
            force_close=True,
            one_trade_per_day=True
        )
        
        engine_enabled = BacktestEngine(config_enabled)
        result_enabled = engine_enabled.run(sample_data_with_multiple_signals, multiple_signals_per_day, "test_strategy", verbose=False)
        
        # Test with rule disabled
        config_disabled = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,
            force_close=True,
            one_trade_per_day=False
        )
        
        engine_disabled = BacktestEngine(config_disabled)
        result_disabled = engine_disabled.run(sample_data_with_multiple_signals, multiple_signals_per_day, "test_strategy", verbose=False)
        
        assert result_enabled is not None
        assert result_disabled is not None
        
        # Both should produce valid results
        assert result_enabled.total_trades >= 0
        assert result_disabled.total_trades >= 0
        
        # Rule enabled should have fewer or equal trades
        assert result_enabled.total_trades <= result_disabled.total_trades, \
            f"Rule enabled should have fewer trades: {result_enabled.total_trades} vs {result_disabled.total_trades}"
    
    def test_one_trade_per_day_with_different_timeframes(self):
        """Test one trade per day rule with different timeframes."""
        # Test with daily timeframe (should naturally have one trade per day)
        daily_dates = [datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc) + timedelta(days=i) for i in range(5)]
        
        df_daily = pd.DataFrame({
            'timestamp': [int(d.timestamp() * 1000) for d in daily_dates],
            'open': [50000] * 5,
            'high': [51000] * 5,
            'low': [49000] * 5,
            'close': [50000] * 5,
            'volume': [1000] * 5
        })
        
        # Daily signals
        daily_signals = pd.Series([1, -1, 1, -1, 1])
        
        config = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=False,  # Disable for daily
            force_close=True,
            one_trade_per_day=True
        )
        
        engine = BacktestEngine(config)
        result = engine.run(df_daily, daily_signals, "test_strategy", verbose=False)
        
        assert result is not None
        assert result.total_trades <= 5, f"Expected at most 5 trades for 5 days, got {result.total_trades}"
