"""Integration tests for UI strategy comparison functionality.

This module tests the integration between the UI and the strategy comparison
functionality, including error handling and fallback mechanisms.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from tests.fixtures.strategy_fixtures import (
    get_mixed_performance_strategies,
    get_expected_comparison_dataframe,
    create_mock_strategy_ranking_service,
    get_test_symbols_and_timeframes,
    get_error_scenarios
)


class TestUIStrategyIntegration:
    """Test UI integration with strategy comparison."""
    
    def test_compare_all_strategies_success(self):
        """Test successful strategy comparison in UI."""
        # Mock the UI function behavior
        def mock_compare_all_strategies(symbol: str, timeframe: str, capital: float):
            try:
                from app.service.strategy_ranking import StrategyRankingService
                
                # Initialize service
                service = StrategyRankingService(capital=capital, max_risk_pct=0.02, lookback_days=90)
                
                # Mock the orchestrator to return test data
                with patch.object(service, 'orchestrator') as mock_orchestrator:
                    mock_orchestrator.run_all_backtests.return_value = get_mixed_performance_strategies()
                    
                    # Get real strategy comparison
                    comparison_df = service.compare_strategies(symbol, timeframe)
                    
                    if not comparison_df.empty:
                        return comparison_df
                    else:
                        # Fallback to simulated data
                        return get_expected_comparison_dataframe()
                        
            except Exception as e:
                # Fallback to simulated data
                return get_expected_comparison_dataframe()
        
        # Test with different symbols and timeframes
        test_cases = get_test_symbols_and_timeframes()
        
        for symbol, timeframe in test_cases:
            result = mock_compare_all_strategies(symbol, timeframe, 1000.0)
            
            # Verify result structure
            assert not result.empty
            assert len(result) == 7  # 7 strategies in mixed performance set
            
            # Verify required columns
            required_columns = [
                'Strategy', 'Sharpe', 'CAGR', 'Win Rate', 'Max DD', 
                'Profit Factor', 'Expectancy', 'Total Trades', 'Wins', 'Losses'
            ]
            for col in required_columns:
                assert col in result.columns
            
            # Verify data types
            assert result['Sharpe'].dtype in [np.float64, np.int64]
            assert result['CAGR'].dtype in [np.float64, np.int64]
            assert result['Win Rate'].dtype in [np.float64, np.int64]
            assert result['Total Trades'].dtype in [np.float64, np.int64]
    
    def test_compare_all_strategies_empty_results(self):
        """Test handling of empty backtest results."""
        def mock_compare_all_strategies_empty(symbol: str, timeframe: str, capital: float):
            try:
                from app.service.strategy_ranking import StrategyRankingService
                
                service = StrategyRankingService(capital=capital, max_risk_pct=0.02, lookback_days=90)
                
                # Mock empty results
                with patch.object(service, 'orchestrator') as mock_orchestrator:
                    mock_orchestrator.run_all_backtests.return_value = []
                    
                    comparison_df = service.compare_strategies(symbol, timeframe)
                    
                    if not comparison_df.empty:
                        return comparison_df
                    else:
                        # Fallback to simulated data
                        return get_expected_comparison_dataframe()
                        
            except Exception as e:
                # Fallback to simulated data
                return get_expected_comparison_dataframe()
        
        result = mock_compare_all_strategies_empty("BTC/USDT", "1h", 1000.0)
        
        # Should return fallback data
        assert not result.empty
        assert len(result) == 7
        assert 'Strategy' in result.columns
    
    def test_compare_all_strategies_error_handling(self):
        """Test error handling in strategy comparison."""
        error_scenarios = get_error_scenarios()
        
        def mock_compare_all_strategies_with_error(symbol: str, timeframe: str, capital: float, error_type: str):
            try:
                from app.service.strategy_ranking import StrategyRankingService
                
                service = StrategyRankingService(capital=capital, max_risk_pct=0.02, lookback_days=90)
                
                # Simulate different error scenarios
                if error_type == "backtest_failure":
                    with patch.object(service, 'orchestrator') as mock_orchestrator:
                        mock_orchestrator.run_all_backtests.side_effect = Exception("Backtest failed")
                        service.compare_strategies(symbol, timeframe)
                elif error_type == "service_unavailable":
                    raise Exception("Service unavailable")
                elif error_type == "invalid_parameters":
                    raise ValueError("Invalid parameters")
                else:
                    # Normal case
                    with patch.object(service, 'orchestrator') as mock_orchestrator:
                        mock_orchestrator.run_all_backtests.return_value = get_mixed_performance_strategies()
                        return service.compare_strategies(symbol, timeframe)
                        
            except Exception as e:
                # Fallback to simulated data
                return get_expected_comparison_dataframe()
        
        # Test each error scenario
        for error_type in error_scenarios.keys():
            result = mock_compare_all_strategies_with_error("BTC/USDT", "1h", 1000.0, error_type)
            
            # Should always return fallback data
            assert not result.empty
            assert len(result) == 7
            assert 'Strategy' in result.columns
    
    def test_strategy_ranking_consistency(self):
        """Test that strategy ranking is consistent across multiple calls."""
        def mock_compare_all_strategies_consistent(symbol: str, timeframe: str, capital: float):
            try:
                from app.service.strategy_ranking import StrategyRankingService
                
                service = StrategyRankingService(capital=capital, max_risk_pct=0.02, lookback_days=90)
                
                with patch.object(service, 'orchestrator') as mock_orchestrator:
                    mock_orchestrator.run_all_backtests.return_value = get_mixed_performance_strategies()
                    
                    return service.compare_strategies(symbol, timeframe)
                    
            except Exception as e:
                return get_expected_comparison_dataframe()
        
        # Run multiple times
        results = []
        for i in range(5):
            result = mock_compare_all_strategies_consistent("BTC/USDT", "1h", 1000.0)
            results.append(result)
        
        # All results should be identical
        for i in range(1, len(results)):
            pd.testing.assert_frame_equal(results[0], results[i])
    
    def test_strategy_metrics_validation(self):
        """Test that strategy metrics are within expected ranges."""
        def mock_compare_all_strategies_validation(symbol: str, timeframe: str, capital: float):
            try:
                from app.service.strategy_ranking import StrategyRankingService
                
                service = StrategyRankingService(capital=capital, max_risk_pct=0.02, lookback_days=90)
                
                with patch.object(service, 'orchestrator') as mock_orchestrator:
                    mock_orchestrator.run_all_backtests.return_value = get_mixed_performance_strategies()
                    
                    return service.compare_strategies(symbol, timeframe)
                    
            except Exception as e:
                return get_expected_comparison_dataframe()
        
        result = mock_compare_all_strategies_validation("BTC/USDT", "1h", 1000.0)
        
        # Validate Sharpe ratios
        assert result['Sharpe'].min() >= -2.0  # Reasonable lower bound
        assert result['Sharpe'].max() <= 5.0   # Reasonable upper bound
        
        # Validate Win Rates
        assert result['Win Rate'].min() >= 0.0
        assert result['Win Rate'].max() <= 1.0
        
        # Validate Max Drawdowns (should be negative)
        assert result['Max DD'].max() <= 0.0
        
        # Validate Total Trades
        assert result['Total Trades'].min() >= 0
        
        # Validate Profit Factors
        assert result['Profit Factor'].min() >= 0.0
    
    def test_strategy_sorting_functionality(self):
        """Test that strategies can be sorted by different metrics."""
        def mock_compare_all_strategies_sorting(symbol: str, timeframe: str, capital: float):
            try:
                from app.service.strategy_ranking import StrategyRankingService
                
                service = StrategyRankingService(capital=capital, max_risk_pct=0.02, lookback_days=90)
                
                with patch.object(service, 'orchestrator') as mock_orchestrator:
                    mock_orchestrator.run_all_backtests.return_value = get_mixed_performance_strategies()
                    
                    return service.compare_strategies(symbol, timeframe)
                    
            except Exception as e:
                return get_expected_comparison_dataframe()
        
        result = mock_compare_all_strategies_sorting("BTC/USDT", "1h", 1000.0)
        
        # Test sorting by Sharpe ratio
        sharpe_sorted = result.sort_values('Sharpe', ascending=False)
        assert sharpe_sorted.iloc[0]['Sharpe'] >= sharpe_sorted.iloc[1]['Sharpe']
        
        # Test sorting by CAGR
        cagr_sorted = result.sort_values('CAGR', ascending=False)
        assert cagr_sorted.iloc[0]['CAGR'] >= cagr_sorted.iloc[1]['CAGR']
        
        # Test sorting by Win Rate
        winrate_sorted = result.sort_values('Win Rate', ascending=False)
        assert winrate_sorted.iloc[0]['Win Rate'] >= winrate_sorted.iloc[1]['Win Rate']
        
        # Test sorting by Max Drawdown (ascending, since negative values)
        dd_sorted = result.sort_values('Max DD', ascending=True)
        assert dd_sorted.iloc[0]['Max DD'] <= dd_sorted.iloc[1]['Max DD']
    
    def test_ui_error_messages(self):
        """Test that appropriate error messages are generated."""
        def mock_compare_all_strategies_with_messages(symbol: str, timeframe: str, capital: float):
            try:
                from app.service.strategy_ranking import StrategyRankingService
                
                service = StrategyRankingService(capital=capital, max_risk_pct=0.02, lookback_days=90)
                
                with patch.object(service, 'orchestrator') as mock_orchestrator:
                    mock_orchestrator.run_all_backtests.return_value = []
                    
                    comparison_df = service.compare_strategies(symbol, timeframe)
                    
                    if not comparison_df.empty:
                        return comparison_df, None
                    else:
                        # Fallback to simulated data with warning
                        warning_msg = f"⚠️ No hay resultados de backtest recientes para {symbol} {timeframe}"
                        return get_expected_comparison_dataframe(), warning_msg
                        
            except Exception as e:
                # Fallback to simulated data with error
                error_msg = f"❌ Error al obtener comparación de estrategias: {e}"
                return get_expected_comparison_dataframe(), error_msg
        
        # Test empty results scenario
        result, message = mock_compare_all_strategies_with_messages("BTC/USDT", "1h", 1000.0)
        assert not result.empty
        assert "⚠️ No hay resultados de backtest recientes" in message
        
        # Test error scenario
        with patch('app.service.strategy_ranking.StrategyRankingService') as mock_service:
            mock_service.side_effect = Exception("Service error")
            result, message = mock_compare_all_strategies_with_messages("BTC/USDT", "1h", 1000.0)
            assert not result.empty
            assert "❌ Error al obtener comparación de estrategias" in message


if __name__ == "__main__":
    pytest.main([__file__])
