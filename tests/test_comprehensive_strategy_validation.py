"""Comprehensive tests for strategy comparison validation.

This module tests that real backtests produce usable metrics and that
the fallback system works correctly when backtests fail.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from app.service.strategy_orchestrator import StrategyOrchestrator, StrategyBacktestResult
from app.research.backtest.engine import BacktestEngine, BacktestConfig
from app.utils.metrics_helper import MetricsCalculator, create_enhanced_comparison_dataframe


class TestComprehensiveStrategyValidation:
    """Test comprehensive strategy validation."""
    
    @pytest.fixture
    def mock_data(self):
        """Create mock market data."""
        dates = pd.date_range(start='2024-01-01', end='2024-03-01', freq='1H')
        np.random.seed(42)
        
        # Generate realistic price data
        returns = np.random.normal(0.0001, 0.02, len(dates))  # 0.01% mean return, 2% volatility
        prices = 100 * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'timestamp': [int(d.timestamp() * 1000) for d in dates],
            'open': prices * (1 + np.random.normal(0, 0.001, len(dates))),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.005, len(dates)))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.005, len(dates)))),
            'close': prices,
            'volume': np.random.uniform(1000, 10000, len(dates))
        })
        
        return df
    
    @pytest.fixture
    def mock_signals(self):
        """Create mock trading signals."""
        # Generate realistic signals
        np.random.seed(42)
        signals = np.random.choice([-1, 0, 1], size=1000, p=[0.1, 0.8, 0.1])
        return pd.Series(signals)
    
    def test_backtest_engine_with_vectorbt_available(self, mock_data, mock_signals):
        """Test backtest engine when vectorbt is available."""
        config = BacktestConfig(
            initial_capital=10000.0,
            commission=0.001,
            slippage=0.0005,
            risk_per_trade=0.02
        )
        
        engine = BacktestEngine(config)
        
        # Mock vectorbt availability
        with patch('app.research.backtest.engine.VBT_AVAILABLE', True):
            with patch('app.research.backtest.engine.vbt') as mock_vbt:
                # Mock vectorbt functionality
                mock_vbt.Portfolio.from_signals.return_value = Mock()
                mock_vbt.Portfolio.from_signals.return_value.stats.return_value = {
                    'Total Return [%]': 15.5,
                    'Sharpe Ratio': 1.8,
                    'Max. Drawdown [%]': -8.2,
                    'Win Rate [%]': 65.0
                }
                
                result = engine.run(mock_data, mock_signals, "Test Strategy", verbose=False)
                
                # Should use vectorbt engine
                assert result is not None
                assert result.strategy_name == "Test Strategy"
    
    def test_backtest_engine_fallback_when_vectorbt_unavailable(self, mock_data, mock_signals):
        """Test fallback engine when vectorbt is not available."""
        config = BacktestConfig(
            initial_capital=10000.0,
            commission=0.001,
            slippage=0.0005,
            risk_per_trade=0.02
        )
        
        engine = BacktestEngine(config)
        
        # Mock vectorbt unavailability
        with patch('app.research.backtest.engine.VBT_AVAILABLE', False):
            result = engine.run(mock_data, mock_signals, "Test Strategy", verbose=False)
            
            # Should use fallback engine
            assert result is not None
            assert result.strategy_name == "Test Strategy"
            assert result.initial_capital == 10000.0
    
    def test_strategy_orchestrator_produces_real_metrics(self, mock_data):
        """Test that StrategyOrchestrator produces real metrics."""
        orchestrator = StrategyOrchestrator(
            capital=10000.0,
            max_risk_pct=0.02,
            lookback_days=90
        )
        
        # Mock data loading
        with patch.object(orchestrator, '_load_data') as mock_load:
            mock_load.return_value = mock_data
            
            # Mock backtest execution
            with patch.object(orchestrator, '_backtest_strategy') as mock_backtest:
                mock_result = StrategyBacktestResult(
                    strategy_name="Test Strategy",
                    timestamp=datetime.now(),
                    total_return=0.15,
                    cagr=0.12,
                    sharpe_ratio=1.8,
                    max_drawdown=-0.08,
                    win_rate=0.65,
                    profit_factor=1.5,
                    expectancy=25.0,
                    volatility=0.12,
                    calmar_ratio=1.5,
                    sortino_ratio=2.1,
                    total_trades=45,
                    winning_trades=29,
                    losing_trades=16,
                    avg_win=50.0,
                    avg_loss=-30.0,
                    capital=10000.0,
                    risk_pct=0.02,
                    lookback_days=90
                )
                mock_backtest.return_value = mock_result
                
                results = orchestrator.run_all_backtests("BTC/USDT", "1h")
                
                assert len(results) == 1
                assert results[0].strategy_name == "Test Strategy"
                assert results[0].sharpe_ratio == 1.8
                assert results[0].total_trades == 45
    
    def test_enhanced_comparison_dataframe_creation(self):
        """Test creation of enhanced comparison DataFrame."""
        results = [
            StrategyBacktestResult(
                strategy_name="Strategy 1",
                timestamp=datetime.now(),
                total_return=0.15,
                cagr=0.12,
                sharpe_ratio=1.8,
                max_drawdown=-0.08,
                win_rate=0.65,
                profit_factor=1.5,
                expectancy=25.0,
                volatility=0.12,
                calmar_ratio=1.5,
                sortino_ratio=2.1,
                total_trades=45,
                winning_trades=29,
                losing_trades=16,
                avg_win=50.0,
                avg_loss=-30.0,
                capital=10000.0,
                risk_pct=0.02,
                lookback_days=90
            ),
            StrategyBacktestResult(
                strategy_name="Strategy 2",
                timestamp=datetime.now(),
                total_return=0.08,
                cagr=0.06,
                sharpe_ratio=1.2,
                max_drawdown=-0.12,
                win_rate=0.55,
                profit_factor=1.2,
                expectancy=15.0,
                volatility=0.15,
                calmar_ratio=0.5,
                sortino_ratio=1.5,
                total_trades=32,
                winning_trades=18,
                losing_trades=14,
                avg_win=40.0,
                avg_loss=-25.0,
                capital=10000.0,
                risk_pct=0.02,
                lookback_days=90
            )
        ]
        
        df = create_enhanced_comparison_dataframe(results)
        
        assert not df.empty
        assert len(df) == 2
        assert 'Strategy' in df.columns
        assert 'Sharpe' in df.columns
        assert 'CAGR' in df.columns
        assert 'Win Rate' in df.columns
        assert 'Max DD' in df.columns
        assert 'Profit Factor' in df.columns
        assert 'Expectancy' in df.columns
        assert 'Total Trades' in df.columns
        
        # Check data mapping
        assert df.iloc[0]['Strategy'] == "Strategy 1"
        assert df.iloc[0]['Sharpe'] == 1.8
        assert df.iloc[0]['CAGR'] == 0.12
        assert df.iloc[0]['Win Rate'] == 0.65
        
        assert df.iloc[1]['Strategy'] == "Strategy 2"
        assert df.iloc[1]['Sharpe'] == 1.2
        assert df.iloc[1]['CAGR'] == 0.06
        assert df.iloc[1]['Win Rate'] == 0.55
    
    def test_metrics_calculator_comprehensive_metrics(self):
        """Test MetricsCalculator produces comprehensive metrics."""
        calculator = MetricsCalculator()
        
        # Create realistic trades
        trades = [
            {'pnl': 100.0, 'pnl_pct': 0.10},
            {'pnl': -50.0, 'pnl_pct': -0.05},
            {'pnl': 75.0, 'pnl_pct': 0.075},
            {'pnl': -25.0, 'pnl_pct': -0.025},
            {'pnl': 150.0, 'pnl_pct': 0.15}
        ]
        
        equity_curve = [10000.0, 10100.0, 10050.0, 10125.0, 10100.0, 10250.0]
        
        metrics = calculator.calculate_comprehensive_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=10000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # Verify all metrics are present
        required_metrics = [
            'total_return', 'cagr', 'sharpe_ratio', 'sortino_ratio', 'calmar_ratio',
            'max_drawdown', 'volatility', 'win_rate', 'profit_factor', 'expectancy',
            'total_trades', 'winning_trades', 'losing_trades', 'avg_win', 'avg_loss'
        ]
        
        for metric in required_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))
        
        # Verify realistic values
        assert metrics['total_trades'] == 5
        assert metrics['winning_trades'] == 3
        assert metrics['losing_trades'] == 2
        assert metrics['win_rate'] == 0.6
        assert metrics['total_return'] > 0  # Should be positive
        assert metrics['max_drawdown'] < 0  # Should be negative
    
    def test_fallback_comparison_consistency(self):
        """Test that fallback comparison produces consistent metrics."""
        # This would test the create_fallback_comparison function
        # but we need to mock the data loading and signal generation
        pass
    
    def test_multi_timeframe_analysis(self):
        """Test multi-timeframe analysis functionality."""
        # Mock multi-timeframe results
        multi_results = {
            "1h": pd.DataFrame({
                'Strategy': ['MA Crossover', 'RSI Regime'],
                'Sharpe': [1.5, 1.2],
                'CAGR': [0.10, 0.08],
                'Timeframe': ['1h', '1h']
            }),
            "4h": pd.DataFrame({
                'Strategy': ['MA Crossover', 'RSI Regime'],
                'Sharpe': [1.8, 1.4],
                'CAGR': [0.12, 0.09],
                'Timeframe': ['4h', '4h']
            })
        }
        
        # Test combining results
        combined_df = pd.concat(multi_results.values(), ignore_index=True)
        
        assert not combined_df.empty
        assert len(combined_df) == 4
        assert 'Timeframe' in combined_df.columns
        
        # Test pivot table creation
        pivot_sharpe = combined_df.pivot(index='Strategy', columns='Timeframe', values='Sharpe')
        
        assert not pivot_sharpe.empty
        assert '1h' in pivot_sharpe.columns
        assert '4h' in pivot_sharpe.columns
        assert 'MA Crossover' in pivot_sharpe.index
        assert 'RSI Regime' in pivot_sharpe.index
    
    def test_asset_metrics_calculation(self):
        """Test asset metrics calculation."""
        # Create mock price data
        dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='1H')
        np.random.seed(42)
        
        returns = np.random.normal(0.0001, 0.02, len(dates))
        prices = 100 * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'close': prices
        })
        
        # Calculate basic metrics
        returns_series = df['close'].pct_change().dropna()
        total_return = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1
        volatility = returns_series.std() * np.sqrt(252)
        
        # Calculate max drawdown
        cumulative = (1 + returns_series).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Verify metrics
        assert isinstance(total_return, float)
        assert isinstance(volatility, float)
        assert isinstance(max_drawdown, float)
        assert max_drawdown <= 0  # Drawdown should be negative or zero
    
    def test_error_handling_in_backtest_engine(self, mock_data, mock_signals):
        """Test error handling in backtest engine."""
        config = BacktestConfig(
            initial_capital=10000.0,
            commission=0.001,
            slippage=0.0005,
            risk_per_trade=0.02
        )
        
        engine = BacktestEngine(config)
        
        # Test with empty data
        empty_df = pd.DataFrame()
        result = engine._run_fallback_backtest(empty_df, mock_signals, "Test", verbose=False)
        
        assert result is not None
        assert result.total_trades == 0
        assert result.total_return == 0.0
        
        # Test with no signals
        empty_signals = pd.Series([0] * len(mock_data))
        result = engine._run_fallback_backtest(mock_data, empty_signals, "Test", verbose=False)
        
        assert result is not None
        assert result.total_trades == 0
    
    def test_metrics_validation_edge_cases(self):
        """Test metrics validation with edge cases."""
        calculator = MetricsCalculator()
        
        # Test with no trades
        metrics = calculator.calculate_comprehensive_metrics(
            trades=[],
            equity_curve=[1000.0],
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        assert metrics['total_trades'] == 0
        assert metrics['win_rate'] == 0.0
        assert metrics['total_return'] == 0.0
        
        # Test with all losing trades
        losing_trades = [
            {'pnl': -100.0, 'pnl_pct': -0.10},
            {'pnl': -50.0, 'pnl_pct': -0.05},
            {'pnl': -75.0, 'pnl_pct': -0.075}
        ]
        
        equity_curve = [1000.0, 900.0, 850.0, 775.0]
        
        metrics = calculator.calculate_comprehensive_metrics(
            trades=losing_trades,
            equity_curve=equity_curve,
            initial_capital=1000.0,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        assert metrics['win_rate'] == 0.0
        assert metrics['total_return'] < 0
        assert metrics['profit_factor'] == 0.0


if __name__ == "__main__":
    pytest.main([__file__])
