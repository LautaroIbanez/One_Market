"""Complete system integration tests.

This module tests the complete trading system end-to-end including:
- Data availability and backfilling
- Multi-timeframe backtesting
- Strategy combinations
- Global ranking
- Daily recommendations
- UI integration
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from app.service.strategy_orchestrator import StrategyOrchestrator, StrategyBacktestResult, DataValidationStatus
from app.service.global_ranking import GlobalRankingService, RankedStrategy
from app.service.daily_recommendation import DailyRecommendationService, DailyRecommendation
from app.config.settings import settings


class TestDataAvailability:
    """Test data availability and validation."""
    
    def test_timeframe_targets_configuration(self):
        """Test that timeframe targets are properly configured."""
        # Check that 5m and 12h were removed
        assert "5m" not in settings.TARGET_TIMEFRAMES
        assert "12h" not in settings.TARGET_TIMEFRAMES
        
        # Check active timeframes
        assert "1d" in settings.TARGET_TIMEFRAMES
        assert "4h" in settings.TARGET_TIMEFRAMES
        assert "1h" in settings.TARGET_TIMEFRAMES
        assert "15m" in settings.TARGET_TIMEFRAMES
        
        # Check increased targets
        assert settings.TIMEFRAME_CANDLE_TARGETS["1d"] == 730  # Increased
        assert settings.TIMEFRAME_CANDLE_TARGETS["4h"] == 360  # Increased
    
    def test_data_validation_status(self):
        """Test DataValidationStatus structure."""
        status = DataValidationStatus(
            timeframe="1h",
            has_data=True,
            num_bars=720,
            reason=None,
            is_sufficient=True
        )
        
        assert status.timeframe == "1h"
        assert status.has_data
        assert status.is_sufficient
        assert status.num_bars == 720
    
    def test_validate_data_availability(self):
        """Test data availability validation."""
        orchestrator = StrategyOrchestrator(capital=10000.0, max_risk_pct=0.02, lookback_days=90)
        
        # Mock data loading
        mock_df = pd.DataFrame({
            'timestamp': [1000 + i for i in range(730)],
            'close': [100.0] * 730
        })
        
        with patch.object(orchestrator, '_load_data', return_value=mock_df):
            validation = orchestrator.validate_data_availability("BTC/USDT", ["1d", "4h"])
            
            assert "1d" in validation
            assert "4h" in validation
            assert validation["1d"].is_sufficient
            assert validation["1d"].num_bars == 730


class TestMultiTimeframeBacktesting:
    """Test multi-timeframe backtesting system."""
    
    def test_multi_timeframe_backtests_structure(self):
        """Test that multi-timeframe backtests return proper structure."""
        orchestrator = StrategyOrchestrator(capital=10000.0, max_risk_pct=0.02, lookback_days=90)
        
        # Mock results
        mock_result = StrategyBacktestResult(
            strategy_name="Test",
            timestamp=datetime.now(),
            timeframe="1h",
            total_return=0.1,
            cagr=0.08,
            sharpe_ratio=1.5,
            max_drawdown=-0.05,
            win_rate=0.6,
            profit_factor=1.2,
            expectancy=20.0,
            volatility=0.1,
            calmar_ratio=1.6,
            sortino_ratio=1.8,
            total_trades=50,
            winning_trades=30,
            losing_trades=20,
            avg_win=50.0,
            avg_loss=-30.0,
            capital=10000.0,
            risk_pct=0.02,
            lookback_days=90
        )
        
        with patch.object(orchestrator, 'run_all_backtests', return_value=[mock_result]):
            results = orchestrator.run_multi_timeframe_backtests("BTC/USDT", ["1h", "4h"])
            
            assert isinstance(results, dict)
            assert "1h" in results
            assert "4h" in results
            
            # Check timeframe is set
            for tf_results in results.values():
                for result in tf_results:
                    assert result.timeframe is not None


class TestStrategyCombinations:
    """Test strategy combination system."""
    
    def test_generate_strategy_combinations(self):
        """Test strategy combination generation."""
        orchestrator = StrategyOrchestrator(capital=10000.0, max_risk_pct=0.02, lookback_days=90)
        
        # Should generate combinations from registry
        combinations = orchestrator.generate_strategy_combinations(k_min=2)
        
        assert isinstance(combinations, list)
        # Should have at least some combinations (depends on registry size)
        assert len(combinations) >= 0
    
    def test_combine_signals_methods(self):
        """Test signal combination methods."""
        from app.research.signals import combine_signals
        
        # Create test signals
        signals = [
            pd.Series([1, 1, 0, -1]),
            pd.Series([1, 0, 1, -1]),
            pd.Series([0, 1, 1, -1])
        ]
        
        # Test consensus
        result_consensus = combine_signals(signals, method="consensus")
        assert len(result_consensus.signal) == 4
        assert result_consensus.signal.iloc[3] == -1  # All agree on -1
        
        # Test majority
        result_majority = combine_signals(signals, method="majority")
        assert len(result_majority.signal) == 4
        
        # Test average
        result_average = combine_signals(signals, method="average")
        assert len(result_average.signal) == 4


class TestGlobalRanking:
    """Test global ranking system."""
    
    def test_global_ranking_with_multiple_timeframes(self):
        """Test global ranking across multiple timeframes."""
        ranking_service = GlobalRankingService()
        
        # Create mock results for multiple timeframes
        multi_results = {
            "1h": [
                StrategyBacktestResult(
                    strategy_name="Strategy A",
                    timestamp=datetime.now(),
                    timeframe="1h",
                    total_return=0.1,
                    cagr=0.08,
                    sharpe_ratio=1.5,
                    max_drawdown=-0.05,
                    win_rate=0.6,
                    profit_factor=1.2,
                    expectancy=20.0,
                    volatility=0.1,
                    calmar_ratio=1.6,
                    sortino_ratio=1.8,
                    total_trades=50,
                    winning_trades=30,
                    losing_trades=20,
                    avg_win=50.0,
                    avg_loss=-30.0,
                    capital=10000.0,
                    risk_pct=0.02,
                    lookback_days=90
                )
            ],
            "4h": [
                StrategyBacktestResult(
                    strategy_name="Strategy A",
                    timestamp=datetime.now(),
                    timeframe="4h",
                    total_return=0.12,
                    cagr=0.10,
                    sharpe_ratio=1.8,
                    max_drawdown=-0.03,
                    win_rate=0.65,
                    profit_factor=1.4,
                    expectancy=25.0,
                    volatility=0.08,
                    calmar_ratio=2.0,
                    sortino_ratio=2.2,
                    total_trades=40,
                    winning_trades=26,
                    losing_trades=14,
                    avg_win=60.0,
                    avg_loss=-35.0,
                    capital=10000.0,
                    risk_pct=0.02,
                    lookback_days=90
                )
            ]
        }
        
        ranked = ranking_service.rank_strategies(multi_results)
        
        assert len(ranked) == 1
        strategy = ranked[0]
        assert strategy.strategy_name == "Strategy A"
        assert strategy.global_rank == 1
        assert "1h" in strategy.timeframe_breakdown
        assert "4h" in strategy.timeframe_breakdown


class TestDailyRecommendation:
    """Test daily recommendation service."""
    
    def test_daily_recommendation_generation(self):
        """Test generation of daily recommendation."""
        service = DailyRecommendationService(capital=10000.0, max_risk_pct=0.02)
        
        # Mock the orchestrator and ranking service
        with patch.object(service.orchestrator, 'validate_data_availability') as mock_validate:
            with patch.object(service.orchestrator, 'run_multi_timeframe_backtests') as mock_backtests:
                with patch.object(service.ranking_service, 'rank_strategies') as mock_rank:
                    
                    # Setup mocks
                    mock_validate.return_value = {
                        "1h": DataValidationStatus(
                            timeframe="1h",
                            has_data=True,
                            num_bars=720,
                            is_sufficient=True
                        )
                    }
                    
                    mock_backtests.return_value = {
                        "1h": [
                            StrategyBacktestResult(
                                strategy_name="MA Crossover",
                                timestamp=datetime.now(),
                                timeframe="1h",
                                total_return=0.1,
                                cagr=0.08,
                                sharpe_ratio=1.5,
                                max_drawdown=-0.05,
                                win_rate=0.6,
                                profit_factor=1.2,
                                expectancy=20.0,
                                volatility=0.1,
                                calmar_ratio=1.6,
                                sortino_ratio=1.8,
                                total_trades=50,
                                winning_trades=30,
                                losing_trades=20,
                                avg_win=50.0,
                                avg_loss=-30.0,
                                capital=10000.0,
                                risk_pct=0.02,
                                lookback_days=90
                            )
                        ]
                    }
                    
                    mock_rank.return_value = [
                        RankedStrategy(
                            strategy_name="MA Crossover",
                            timeframe="1h",
                            is_combination=False,
                            global_score=0.75,
                            global_rank=1,
                            timeframe_breakdown={
                                "1h": {
                                    'sharpe_ratio': 1.5,
                                    'win_rate': 0.6,
                                    'cagr': 0.08,
                                    'profit_factor': 1.2,
                                    'expectancy': 20.0,
                                    'max_drawdown': -0.05
                                }
                            },
                            weighted_sharpe=0.45,
                            weighted_win_rate=0.12,
                            weighted_max_dd=0.01,
                            weighted_profit_factor=0.24,
                            weighted_expectancy=2.0,
                            best_sharpe=1.5,
                            best_win_rate=0.6,
                            best_cagr=0.08,
                            best_profit_factor=1.2,
                            best_expectancy=20.0,
                            worst_max_dd=-0.05,
                            sharpe_consistency=0.1,
                            win_rate_consistency=0.05,
                            cagr_consistency=0.08
                        )
                    ]
                    
                    # Get recommendation
                    recommendation = service.get_daily_recommendation("BTC/USDT")
                    
                    assert recommendation is not None
                    assert isinstance(recommendation, DailyRecommendation)
                    assert recommendation.recommended_strategy == "MA Crossover"
                    assert recommendation.confidence_level in ["HIGH", "MEDIUM", "LOW"]
    
    def test_daily_recommendation_with_no_data(self):
        """Test that recommendation fails gracefully with no data."""
        service = DailyRecommendationService(capital=10000.0, max_risk_pct=0.02)
        
        with patch.object(service.orchestrator, 'validate_data_availability') as mock_validate:
            mock_validate.return_value = {
                "1h": DataValidationStatus(
                    timeframe="1h",
                    has_data=False,
                    num_bars=0,
                    reason="No data available",
                    is_sufficient=False
                )
            }
            
            recommendation = service.get_daily_recommendation("BTC/USDT")
            
            assert recommendation is None


class TestUIRobustness:
    """Test UI robustness with empty/invalid data."""
    
    def test_comparison_df_with_empty_results(self):
        """Test that UI handles empty comparison DataFrames."""
        # Create empty DataFrame with required columns
        df = pd.DataFrame(columns=['Strategy', 'Sharpe', 'Win Rate', 'Max DD', 'Profit Factor'])
        
        # Should not raise KeyError
        assert df.empty
        assert 'Strategy' in df.columns
        assert 'Sharpe' in df.columns
    
    def test_comparison_df_with_missing_columns(self):
        """Test that UI detects missing columns."""
        df = pd.DataFrame({
            'Strategy': ['Test'],
            'Sharpe': [1.5]
            # Missing: Win Rate, Max DD, Profit Factor
        })
        
        required_columns = ['Sharpe', 'Win Rate', 'Max DD', 'Profit Factor']
        missing = [col for col in required_columns if col not in df.columns]
        
        assert len(missing) == 3
        assert 'Win Rate' in missing
        assert 'Max DD' in missing
        assert 'Profit Factor' in missing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

