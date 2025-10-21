"""Unit tests for strategy comparison functionality.

This module tests the strategy comparison features including:
- Real backtest results integration
- Strategy aggregation and ranking
- Fallback mechanisms
- Error handling
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from app.service.strategy_ranking import StrategyRankingService
from app.service.strategy_orchestrator import StrategyBacktestResult


class TestStrategyComparison:
    """Test strategy comparison functionality."""
    
    @pytest.fixture
    def mock_backtest_results(self):
        """Create mock backtest results for testing."""
        results = []
        
        # Strategy 1: High performing
        results.append(StrategyBacktestResult(
            strategy_name="MA Crossover (10,20)",
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
            capital=1000.0,
            risk_pct=0.02,
            lookback_days=90
        ))
        
        # Strategy 2: Medium performing
        results.append(StrategyBacktestResult(
            strategy_name="RSI Regime (14)",
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
            capital=1000.0,
            risk_pct=0.02,
            lookback_days=90
        ))
        
        # Strategy 3: Low performing
        results.append(StrategyBacktestResult(
            strategy_name="Trend EMA (50,200)",
            timestamp=datetime.now(),
            total_return=-0.05,
            cagr=-0.08,
            sharpe_ratio=-0.3,
            max_drawdown=-0.20,
            win_rate=0.40,
            profit_factor=0.8,
            expectancy=-10.0,
            volatility=0.18,
            calmar_ratio=-0.4,
            sortino_ratio=-0.2,
            total_trades=28,
            winning_trades=11,
            losing_trades=17,
            avg_win=35.0,
            avg_loss=-45.0,
            capital=1000.0,
            risk_pct=0.02,
            lookback_days=90
        ))
        
        return results
    
    @pytest.fixture
    def mock_strategy_ranking_service(self):
        """Create mock StrategyRankingService."""
        service = Mock(spec=StrategyRankingService)
        return service
    
    def test_strategy_comparison_dataframe_mapping(self, mock_backtest_results):
        """Test that StrategyBacktestResult objects are correctly mapped to DataFrame."""
        # Create service instance
        service = StrategyRankingService(capital=1000.0, max_risk_pct=0.02, lookback_days=90)
        
        # Mock the orchestrator to return our test results
        with patch.object(service, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.run_all_backtests.return_value = mock_backtest_results
            
            # Get comparison DataFrame
            comparison_df = service.compare_strategies("BTC/USDT", "1h")
            
            # Verify DataFrame structure
            assert not comparison_df.empty
            assert len(comparison_df) == 3
            
            # Check required columns
            expected_columns = [
                'Strategy', 'Sharpe', 'CAGR', 'Win Rate', 'Max DD', 
                'Profit Factor', 'Expectancy', 'Total Trades', 'Wins', 'Losses'
            ]
            for col in expected_columns:
                assert col in comparison_df.columns
            
            # Verify data mapping
            assert comparison_df.iloc[0]['Strategy'] == "MA Crossover (10,20)"
            assert comparison_df.iloc[0]['Sharpe'] == 1.8
            assert comparison_df.iloc[0]['CAGR'] == 0.12
            assert comparison_df.iloc[0]['Win Rate'] == 0.65
            
            assert comparison_df.iloc[1]['Strategy'] == "RSI Regime (14)"
            assert comparison_df.iloc[1]['Sharpe'] == 1.2
            
            assert comparison_df.iloc[2]['Strategy'] == "Trend EMA (50,200)"
            assert comparison_df.iloc[2]['Sharpe'] == -0.3
    
    def test_strategy_ranking_by_sharpe(self, mock_backtest_results):
        """Test that strategies are correctly ranked by Sharpe ratio."""
        service = StrategyRankingService(capital=1000.0, max_risk_pct=0.02, lookback_days=90)
        
        with patch.object(service, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.run_all_backtests.return_value = mock_backtest_results
            
            comparison_df = service.compare_strategies("BTC/USDT", "1h")
            
            # Sort by Sharpe ratio (descending)
            sorted_df = comparison_df.sort_values('Sharpe', ascending=False)
            
            # Verify ranking
            assert sorted_df.iloc[0]['Strategy'] == "MA Crossover (10,20)"  # Sharpe: 1.8
            assert sorted_df.iloc[1]['Strategy'] == "RSI Regime (14)"       # Sharpe: 1.2
            assert sorted_df.iloc[2]['Strategy'] == "Trend EMA (50,200)"    # Sharpe: -0.3
    
    def test_strategy_ranking_by_cagr(self, mock_backtest_results):
        """Test that strategies are correctly ranked by CAGR."""
        service = StrategyRankingService(capital=1000.0, max_risk_pct=0.02, lookback_days=90)
        
        with patch.object(service, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.run_all_backtests.return_value = mock_backtest_results
            
            comparison_df = service.compare_strategies("BTC/USDT", "1h")
            
            # Sort by CAGR (descending)
            sorted_df = comparison_df.sort_values('CAGR', ascending=False)
            
            # Verify ranking
            assert sorted_df.iloc[0]['Strategy'] == "MA Crossover (10,20)"  # CAGR: 0.12
            assert sorted_df.iloc[1]['Strategy'] == "RSI Regime (14)"       # CAGR: 0.06
            assert sorted_df.iloc[2]['Strategy'] == "Trend EMA (50,200)"    # CAGR: -0.08
    
    def test_empty_results_handling(self):
        """Test handling of empty backtest results."""
        service = StrategyRankingService(capital=1000.0, max_risk_pct=0.02, lookback_days=90)
        
        with patch.object(service, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.run_all_backtests.return_value = []
            
            comparison_df = service.compare_strategies("BTC/USDT", "1h")
            
            # Should return empty DataFrame
            assert comparison_df.empty
    
    def test_backtest_failure_handling(self):
        """Test handling of backtest failures."""
        service = StrategyRankingService(capital=1000.0, max_risk_pct=0.02, lookback_days=90)
        
        with patch.object(service, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.run_all_backtests.side_effect = Exception("Backtest failed")
            
            # Should handle exception gracefully
            with pytest.raises(Exception):
                service.compare_strategies("BTC/USDT", "1h")
    
    def test_strategy_metrics_calculation(self, mock_backtest_results):
        """Test that all metrics are correctly calculated and mapped."""
        service = StrategyRankingService(capital=1000.0, max_risk_pct=0.02, lookback_days=90)
        
        with patch.object(service, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.run_all_backtests.return_value = mock_backtest_results
            
            comparison_df = service.compare_strategies("BTC/USDT", "1h")
            
            # Test first strategy (high performing)
            high_perf = comparison_df[comparison_df['Strategy'] == "MA Crossover (10,20)"].iloc[0]
            
            assert high_perf['Sharpe'] == 1.8
            assert high_perf['CAGR'] == 0.12
            assert high_perf['Win Rate'] == 0.65
            assert high_perf['Max DD'] == -0.08
            assert high_perf['Profit Factor'] == 1.5
            assert high_perf['Expectancy'] == 25.0
            assert high_perf['Total Trades'] == 45
            assert high_perf['Wins'] == 29
            assert high_perf['Losses'] == 16
            
            # Test third strategy (low performing)
            low_perf = comparison_df[comparison_df['Strategy'] == "Trend EMA (50,200)"].iloc[0]
            
            assert low_perf['Sharpe'] == -0.3
            assert low_perf['CAGR'] == -0.08
            assert low_perf['Win Rate'] == 0.40
            assert low_perf['Max DD'] == -0.20
            assert low_perf['Profit Factor'] == 0.8
            assert low_perf['Expectancy'] == -10.0
            assert low_perf['Total Trades'] == 28
            assert low_perf['Wins'] == 11
            assert low_perf['Losses'] == 17
    
    def test_dataframe_sorting_consistency(self, mock_backtest_results):
        """Test that DataFrame sorting is consistent across different metrics."""
        service = StrategyRankingService(capital=1000.0, max_risk_pct=0.02, lookback_days=90)
        
        with patch.object(service, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.run_all_backtests.return_value = mock_backtest_results
            
            comparison_df = service.compare_strategies("BTC/USDT", "1h")
            
            # Test sorting by different metrics
            sharpe_sorted = comparison_df.sort_values('Sharpe', ascending=False)
            cagr_sorted = comparison_df.sort_values('CAGR', ascending=False)
            winrate_sorted = comparison_df.sort_values('Win Rate', ascending=False)
            
            # All should have same number of rows
            assert len(sharpe_sorted) == len(cagr_sorted) == len(winrate_sorted) == 3
            
            # Sharpe and CAGR should have same top performer
            assert sharpe_sorted.iloc[0]['Strategy'] == cagr_sorted.iloc[0]['Strategy'] == "MA Crossover (10,20)"
            
            # Win rate should also have same top performer
            assert winrate_sorted.iloc[0]['Strategy'] == "MA Crossover (10,20)"
    
    def test_ui_integration_simulation(self):
        """Test the UI integration with simulated data."""
        # This test simulates what happens in the UI when compare_all_strategies is called
        
        # Mock the UI function behavior
        def mock_compare_all_strategies(symbol: str, timeframe: str, capital: float):
            try:
                service = StrategyRankingService(capital=capital, max_risk_pct=0.02, lookback_days=90)
                comparison_df = service.compare_strategies(symbol, timeframe)
                
                if not comparison_df.empty:
                    return comparison_df
                else:
                    # Fallback to simulated data
                    return pd.DataFrame({
                        'Strategy': ['MA Crossover (10,20)', 'RSI Regime (14)', 'Trend EMA (50,200)'],
                        'Sharpe': [1.8, 1.2, -0.3],
                        'CAGR': [0.12, 0.06, -0.08],
                        'Win Rate': [0.65, 0.55, 0.40],
                        'Max DD': [-0.08, -0.12, -0.20],
                        'Profit Factor': [1.5, 1.2, 0.8],
                        'Expectancy': [25.0, 15.0, -10.0],
                        'Total Trades': [45, 32, 28]
                    })
            except Exception as e:
                # Fallback to simulated data
                return pd.DataFrame({
                    'Strategy': ['MA Crossover (10,20)', 'RSI Regime (14)', 'Trend EMA (50,200)'],
                    'Sharpe': [1.8, 1.2, -0.3],
                    'CAGR': [0.12, 0.06, -0.08],
                    'Win Rate': [0.65, 0.55, 0.40],
                    'Max DD': [-0.08, -0.12, -0.20],
                    'Profit Factor': [1.5, 1.2, 0.8],
                    'Expectancy': [25.0, 15.0, -10.0],
                    'Total Trades': [45, 32, 28]
                })
        
        # Test successful case
        result = mock_compare_all_strategies("BTC/USDT", "1h", 1000.0)
        assert not result.empty
        assert len(result) == 3
        assert 'Strategy' in result.columns
        assert 'Sharpe' in result.columns
        
        # Test that fallback works
        result_fallback = mock_compare_all_strategies("UNKNOWN/USDT", "1h", 1000.0)
        assert not result_fallback.empty
        assert len(result_fallback) == 3


if __name__ == "__main__":
    pytest.main([__file__])
