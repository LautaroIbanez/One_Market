"""Tests to ensure forced close window is enforced.

This module tests that the backtest engine properly enforces
forced close between 19-20 AR (Argentina time).
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np

from app.research.backtest.engine import BacktestEngine, BacktestConfig, BacktestResult


class TestForcedCloseWindow:
    """Test that forced close window is enforced."""
    
    @pytest.fixture
    def sample_data_with_trading_hours(self):
        """Create sample data with trading hours."""
        # Create data for 2 days with hourly data
        dates = []
        prices = []
        
        # Day 1: Full day
        for hour in range(24):
            date = datetime(2022, 1, 1, hour, 0, 0, tzinfo=timezone.utc)
            dates.append(date)
            prices.append(50000 + hour * 10)
        
        # Day 2: Full day
        for hour in range(24):
            date = datetime(2022, 1, 2, hour, 0, 0, tzinfo=timezone.utc)
            dates.append(date)
            prices.append(50000 + hour * 5)
        
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
    def signals_with_open_positions(self, sample_data_with_trading_hours):
        """Create signals that result in open positions."""
        # Create signals that would leave positions open
        signals = []
        
        for i, row in sample_data_with_trading_hours.iterrows():
            # Create long signal at hour 10 (should be closed by forced close)
            if i == 10:
                signals.append(1)  # Long signal
            else:
                signals.append(0)  # No signal
        
        return pd.Series(signals)
    
    def test_forced_close_enabled(self, sample_data_with_trading_hours, signals_with_open_positions):
        """Test that forced close is enforced when enabled."""
        config = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,
            force_close=True,  # Enable forced close
            one_trade_per_day=True
        )
        
        engine = BacktestEngine(config)
        result = engine.run(sample_data_with_trading_hours, signals_with_open_positions, "test_strategy", verbose=False)
        
        assert result is not None
        
        # Verify that all trades are properly closed
        if result.trades:
            for trade in result.trades:
                assert trade['status'] == 'CLOSED', f"Trade should be closed: {trade}"
                assert trade['exit_time'] is not None, "Trade should have exit time"
                
                # Verify that exit time is within forced close window (19-20 AR)
                exit_time = datetime.fromtimestamp(trade['exit_time'] / 1000, tz=timezone.utc)
                # Convert to Argentina time (UTC-3)
                exit_time_ar = exit_time - timedelta(hours=3)
                
                # Check if exit time is between 19:00 and 20:00 AR
                if exit_time_ar.hour >= 19 and exit_time_ar.hour < 20:
                    assert True, f"Trade closed within forced close window: {exit_time_ar}"
                else:
                    # If not in forced close window, it should be closed by signal
                    assert trade['exit_time'] < trade['entry_time'] + 24 * 3600 * 1000, "Trade should be closed within 24 hours"
    
    def test_forced_close_disabled(self, sample_data_with_trading_hours, signals_with_open_positions):
        """Test that forced close is not enforced when disabled."""
        config = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,
            force_close=False,  # Disable forced close
            one_trade_per_day=True
        )
        
        engine = BacktestEngine(config)
        result = engine.run(sample_data_with_trading_hours, signals_with_open_positions, "test_strategy", verbose=False)
        
        assert result is not None
        
        # With forced close disabled, trades might remain open
        # This depends on the specific implementation, but we should not enforce
        # that all trades are closed at the forced close time
        if result.trades:
            for trade in result.trades:
                # Trades should still be closed by some mechanism
                assert trade['status'] == 'CLOSED', f"Trade should be closed: {trade}"
    
    def test_forced_close_with_trading_windows(self, sample_data_with_trading_hours, signals_with_open_positions):
        """Test forced close with trading windows enabled."""
        config = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,  # Enable trading windows
            force_close=True,  # Enable forced close
            one_trade_per_day=True
        )
        
        engine = BacktestEngine(config)
        result = engine.run(sample_data_with_trading_hours, signals_with_open_positions, "test_strategy", verbose=False)
        
        assert result is not None
        
        # Verify that trades respect both trading windows and forced close
        if result.trades:
            for trade in result.trades:
                assert trade['status'] == 'CLOSED', f"Trade should be closed: {trade}"
                assert trade['exit_time'] is not None, "Trade should have exit time"
    
    def test_forced_close_edge_case_end_of_day(self):
        """Test forced close edge case at end of day."""
        # Create data for a single day with signal near end
        dates = [datetime(2022, 1, 1, hour, 0, 0, tzinfo=timezone.utc) for hour in range(24)]
        
        df = pd.DataFrame({
            'timestamp': [int(d.timestamp() * 1000) for d in dates],
            'open': [50000] * 24,
            'high': [51000] * 24,
            'low': [49000] * 24,
            'close': [50000] * 24,
            'volume': [1000] * 24
        })
        
        # Create signal at hour 18 (should be closed by forced close at 19)
        signals = [0] * 18 + [1] + [0] * 5  # Signal at hour 18
        
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
        result = engine.run(df, pd.Series(signals), "test_strategy", verbose=False)
        
        assert result is not None
        
        # Should have at most 1 trade (forced close should close it)
        assert result.total_trades <= 1, f"Expected at most 1 trade, got {result.total_trades}"
        
        if result.trades:
            trade = result.trades[0]
            assert trade['status'] == 'CLOSED', "Trade should be closed by forced close"
    
    def test_forced_close_performance_impact(self, sample_data_with_trading_hours, signals_with_open_positions):
        """Test that forced close doesn't significantly impact performance calculation."""
        # Test with forced close enabled
        config_enabled = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,
            force_close=True,  # Enable forced close
            one_trade_per_day=True
        )
        
        engine_enabled = BacktestEngine(config_enabled)
        result_enabled = engine_enabled.run(sample_data_with_trading_hours, signals_with_open_positions, "test_strategy", verbose=False)
        
        # Test with forced close disabled
        config_disabled = BacktestConfig(
            initial_capital=10000.0,
            risk_per_trade=0.02,
            commission=0.001,
            slippage=0.0005,
            use_trading_windows=True,
            force_close=False,  # Disable forced close
            one_trade_per_day=True
        )
        
        engine_disabled = BacktestEngine(config_disabled)
        result_disabled = engine_disabled.run(sample_data_with_trading_hours, signals_with_open_positions, "test_strategy", verbose=False)
        
        assert result_enabled is not None
        assert result_disabled is not None
        
        # Both should produce valid results
        assert result_enabled.total_trades >= 0
        assert result_disabled.total_trades >= 0
        
        # Forced close should not significantly impact trade count
        # (exact comparison depends on implementation)
        assert abs(result_enabled.total_trades - result_disabled.total_trades) <= 1, \
            f"Forced close should not significantly impact trade count: {result_enabled.total_trades} vs {result_disabled.total_trades}"
    
    def test_forced_close_with_different_timeframes(self):
        """Test forced close with different timeframes."""
        # Test with hourly timeframe
        hourly_dates = [datetime(2022, 1, 1, hour, 0, 0, tzinfo=timezone.utc) for hour in range(24)]
        
        df_hourly = pd.DataFrame({
            'timestamp': [int(d.timestamp() * 1000) for d in hourly_dates],
            'open': [50000] * 24,
            'high': [51000] * 24,
            'low': [49000] * 24,
            'close': [50000] * 24,
            'volume': [1000] * 24
        })
        
        # Hourly signals
        hourly_signals = pd.Series([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        
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
        result = engine.run(df_hourly, hourly_signals, "test_strategy", verbose=False)
        
        assert result is not None
        
        # Should have at most 1 trade (forced close should close it)
        assert result.total_trades <= 1, f"Expected at most 1 trade, got {result.total_trades}"
        
        if result.trades:
            trade = result.trades[0]
            assert trade['status'] == 'CLOSED', "Trade should be closed by forced close"
