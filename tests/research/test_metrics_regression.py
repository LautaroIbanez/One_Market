"""Regression tests for trading metrics calculations.

This module tests edge cases and regression scenarios for metrics calculations,
ensuring robust handling of various trading scenarios.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict

from app.utils.metrics_helper import MetricsCalculator, create_enhanced_comparison_dataframe
from app.service.strategy_orchestrator import StrategyBacktestResult


class TestMetricsRegression:
    """Test regression scenarios for metrics calculations."""
    
    @pytest.fixture
    def metrics_calculator(self):
        """Create metrics calculator instance."""
        return MetricsCalculator(risk_free_rate=0.02)
    
    def test_empty_trades_handling(self, metrics_calculator):
        """Test handling of empty trades list."""
        metrics = metrics_calculator.calculate_comprehensive_metrics(
            trades=[],
            equity_curve=[1000.0],
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # Should return empty metrics
        assert metrics['total_return'] == 0.0
        assert metrics['cagr'] == 0.0
        assert metrics['sharpe_ratio'] == 0.0
        assert metrics['win_rate'] == 0.0
        assert metrics['total_trades'] == 0
    
    def test_all_losing_trades(self, metrics_calculator):
        """Test metrics calculation with all losing trades."""
        trades = [
            {'pnl': -50.0, 'pnl_pct': -0.05},
            {'pnl': -30.0, 'pnl_pct': -0.03},
            {'pnl': -40.0, 'pnl_pct': -0.04}
        ]
        equity_curve = [1000.0, 950.0, 920.0, 880.0]
        
        metrics = metrics_calculator.calculate_comprehensive_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # All trades are losing
        assert metrics['win_rate'] == 0.0
        assert metrics['total_trades'] == 3
        assert metrics['winning_trades'] == 0
        assert metrics['losing_trades'] == 3
        assert metrics['total_return'] < 0
        assert metrics['profit_factor'] == 0.0
    
    def test_all_winning_trades(self, metrics_calculator):
        """Test metrics calculation with all winning trades."""
        trades = [
            {'pnl': 50.0, 'pnl_pct': 0.05},
            {'pnl': 30.0, 'pnl_pct': 0.03},
            {'pnl': 40.0, 'pnl_pct': 0.04}
        ]
        equity_curve = [1000.0, 1050.0, 1080.0, 1120.0]
        
        metrics = metrics_calculator.calculate_comprehensive_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # All trades are winning
        assert metrics['win_rate'] == 1.0
        assert metrics['total_trades'] == 3
        assert metrics['winning_trades'] == 3
        assert metrics['losing_trades'] == 0
        assert metrics['total_return'] > 0
        assert metrics['profit_factor'] == float('inf')
    
    def test_single_trade_scenario(self, metrics_calculator):
        """Test metrics calculation with single trade."""
        trades = [{'pnl': 100.0, 'pnl_pct': 0.10}]
        equity_curve = [1000.0, 1100.0]
        
        metrics = metrics_calculator.calculate_comprehensive_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        
        assert metrics['total_trades'] == 1
        assert metrics['win_rate'] == 1.0
        assert metrics['total_return'] == 0.10
        assert metrics['winning_trades'] == 1
        assert metrics['losing_trades'] == 0
    
    def test_zero_volatility_handling(self, metrics_calculator):
        """Test handling of zero volatility scenarios."""
        trades = [
            {'pnl': 10.0, 'pnl_pct': 0.01},
            {'pnl': 10.0, 'pnl_pct': 0.01},
            {'pnl': 10.0, 'pnl_pct': 0.01}
        ]
        equity_curve = [1000.0, 1010.0, 1020.0, 1030.0]
        
        metrics = metrics_calculator.calculate_comprehensive_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # Should handle zero volatility gracefully
        assert metrics['volatility'] == 0.0
        assert metrics['sharpe_ratio'] == 0.0  # Should not crash
        assert metrics['sortino_ratio'] == 0.0
    
    def test_extreme_drawdown_scenario(self, metrics_calculator):
        """Test handling of extreme drawdown scenarios."""
        trades = [
            {'pnl': -500.0, 'pnl_pct': -0.50},  # 50% loss
            {'pnl': -200.0, 'pnl_pct': -0.20},  # 20% loss
            {'pnl': 50.0, 'pnl_pct': 0.05}     # Small win
        ]
        equity_curve = [1000.0, 500.0, 300.0, 350.0]
        
        metrics = metrics_calculator.calculate_comprehensive_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # Should handle extreme drawdown
        assert metrics['max_drawdown'] < -0.5  # More than 50% drawdown
        assert metrics['total_return'] < 0
        assert metrics['win_rate'] < 0.5
    
    def test_high_frequency_trading_scenario(self, metrics_calculator):
        """Test metrics with high frequency trading scenario."""
        # Generate 100 trades with small PnL
        trades = []
        equity_curve = [1000.0]
        current_equity = 1000.0
        
        for i in range(100):
            pnl = np.random.normal(0, 5)  # Small random PnL
            pnl_pct = pnl / current_equity
            current_equity += pnl
            
            trades.append({'pnl': pnl, 'pnl_pct': pnl_pct})
            equity_curve.append(current_equity)
        
        metrics = metrics_calculator.calculate_comprehensive_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        assert metrics['total_trades'] == 100
        assert 0 <= metrics['win_rate'] <= 1
        assert metrics['volatility'] >= 0
    
    def test_equity_curve_edge_cases(self, metrics_calculator):
        """Test edge cases in equity curve calculations."""
        # Test with constant equity (no trades)
        metrics = metrics_calculator.calculate_comprehensive_metrics(
            trades=[],
            equity_curve=[1000.0, 1000.0, 1000.0],
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        assert metrics['total_return'] == 0.0
        assert metrics['cagr'] == 0.0
        
        # Test with decreasing equity
        metrics = metrics_calculator.calculate_comprehensive_metrics(
            trades=[{'pnl': -100.0, 'pnl_pct': -0.10}],
            equity_curve=[1000.0, 900.0],
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        
        assert metrics['total_return'] == -0.10
        assert metrics['max_drawdown'] <= 0
    
    def test_enhanced_comparison_dataframe_edge_cases(self):
        """Test enhanced comparison DataFrame with edge cases."""
        # Test with empty results
        df = create_enhanced_comparison_dataframe([])
        assert df.empty
        
        # Test with single result
        result = StrategyBacktestResult(
            strategy_name="Test Strategy",
            timestamp=datetime.now(),
            total_return=0.10,
            cagr=0.08,
            sharpe_ratio=1.5,
            max_drawdown=-0.05,
            win_rate=0.60,
            profit_factor=1.2,
            expectancy=15.0,
            volatility=0.12,
            calmar_ratio=1.6,
            sortino_ratio=1.8,
            total_trades=20,
            winning_trades=12,
            losing_trades=8,
            avg_win=25.0,
            avg_loss=-15.0,
            capital=1000.0,
            risk_pct=0.02,
            lookback_days=90
        )
        
        df = create_enhanced_comparison_dataframe([result])
        assert not df.empty
        assert len(df) == 1
        assert df.iloc[0]['Strategy'] == "Test Strategy"
        assert df.iloc[0]['Sharpe'] == 1.5
        assert df.iloc[0]['Win Rate'] == 0.60
    
    def test_metrics_consistency_across_calculations(self, metrics_calculator):
        """Test that metrics are consistent across multiple calculations."""
        trades = [
            {'pnl': 50.0, 'pnl_pct': 0.05},
            {'pnl': -30.0, 'pnl_pct': -0.03},
            {'pnl': 40.0, 'pnl_pct': 0.04}
        ]
        equity_curve = [1000.0, 1050.0, 1020.0, 1060.0]
        
        # Calculate metrics multiple times
        metrics1 = metrics_calculator.calculate_comprehensive_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        metrics2 = metrics_calculator.calculate_comprehensive_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # Results should be identical
        for key in metrics1:
            assert abs(metrics1[key] - metrics2[key]) < 1e-10
    
    def test_risk_metrics_edge_cases(self, metrics_calculator):
        """Test risk metrics with edge cases."""
        # Test with very high volatility
        trades = [
            {'pnl': 100.0, 'pnl_pct': 0.10},
            {'pnl': -80.0, 'pnl_pct': -0.08},
            {'pnl': 120.0, 'pnl_pct': 0.12},
            {'pnl': -90.0, 'pnl_pct': -0.09}
        ]
        equity_curve = [1000.0, 1100.0, 1020.0, 1140.0, 1050.0]
        
        metrics = metrics_calculator.calculate_comprehensive_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # Should handle high volatility
        assert metrics['volatility'] > 0
        assert metrics['sharpe_ratio'] is not None
        assert metrics['sortino_ratio'] is not None
        assert metrics['calmar_ratio'] is not None


if __name__ == "__main__":
    pytest.main([__file__])
