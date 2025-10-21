"""Tests for structural improvements to the trading system.

This module tests the fixes for:
1. Homogeneous data loading across timeframes
2. Multi-timeframe backtesting
3. Strategy combinations
4. Global ranking system
5. UI integration
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from app.data.store import DataStore
from app.service.strategy_orchestrator import StrategyOrchestrator, StrategyBacktestResult
from app.service.global_ranking import GlobalRankingService, RankedStrategy
from app.config.settings import settings


class TestHomogeneousDataLoading:
    """Test homogeneous data loading across timeframes."""
    
    def test_timeframe_candle_targets_config(self):
        """Test that timeframe candle targets are properly configured."""
        assert "1d" in settings.TIMEFRAME_CANDLE_TARGETS
        assert "1h" in settings.TIMEFRAME_CANDLE_TARGETS
        assert "15m" in settings.TIMEFRAME_CANDLE_TARGETS
        
        # Check that targets are reasonable
        assert settings.TIMEFRAME_CANDLE_TARGETS["1d"] == 365  # ~1 year
        assert settings.TIMEFRAME_CANDLE_TARGETS["1h"] == 168  # ~1 week
        assert settings.TIMEFRAME_CANDLE_TARGETS["15m"] == 672  # ~1 week
    
    def test_data_store_max_bars_parameter(self):
        """Test that DataStore.read_bars accepts max_bars parameter."""
        store = DataStore()
        
        # Mock data
        mock_bars = [
            Mock(timestamp=1000 + i, open=100.0, high=101.0, low=99.0, close=100.5, volume=1000.0, symbol="BTC/USDT", timeframe="1h")
            for i in range(1000)
        ]
        
        with patch.object(store, '_read_partition_file', return_value=mock_bars):
            # Test with max_bars
            bars = store.read_bars("BTC/USDT", "1h", max_bars=100)
            assert len(bars) == 100
            
            # Test without max_bars
            bars = store.read_bars("BTC/USDT", "1h")
            assert len(bars) == 1000
    
    def test_strategy_orchestrator_homogeneous_loading(self):
        """Test that StrategyOrchestrator uses homogeneous data loading."""
        orchestrator = StrategyOrchestrator(capital=10000.0, max_risk_pct=0.02, lookback_days=90)
        
        # Mock data loading
        mock_df = pd.DataFrame({
            'timestamp': [1000 + i for i in range(365)],
            'open': [100.0] * 365,
            'high': [101.0] * 365,
            'low': [99.0] * 365,
            'close': [100.0] * 365,
            'volume': [1000.0] * 365
        })
        
        with patch.object(orchestrator.store, 'read_bars') as mock_read:
            mock_read.return_value = [Mock(to_dict=lambda: mock_df.iloc[0].to_dict()) for _ in range(365)]
            
            df = orchestrator._load_data("BTC/USDT", "1d", datetime.now())
            
            # Should use max_bars from settings
            mock_read.assert_called_once()
            call_args = mock_read.call_args
            assert 'max_bars' in call_args.kwargs
            assert call_args.kwargs['max_bars'] == settings.TIMEFRAME_CANDLE_TARGETS["1d"]


class TestMultiTimeframeBacktesting:
    """Test multi-timeframe backtesting functionality."""
    
    def test_multi_timeframe_backtests(self):
        """Test running backtests across multiple timeframes."""
        orchestrator = StrategyOrchestrator(capital=10000.0, max_risk_pct=0.02, lookback_days=90)
        
        # Mock data loading
        mock_df = pd.DataFrame({
            'timestamp': [1000 + i for i in range(100)],
            'open': [100.0] * 100,
            'high': [101.0] * 100,
            'low': [99.0] * 100,
            'close': [100.0] * 100,
            'volume': [1000.0] * 100
        })
        
        with patch.object(orchestrator, '_load_data', return_value=mock_df):
            with patch.object(orchestrator, 'run_all_backtests') as mock_run:
                # Mock results for each timeframe
                mock_results = [
                    StrategyBacktestResult(
                        strategy_name="Test Strategy",
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
                mock_run.return_value = mock_results
                
                timeframes = ["1h", "4h", "1d"]
                results = orchestrator.run_multi_timeframe_backtests("BTC/USDT", timeframes)
                
                # Should have results for each timeframe
                assert len(results) == 3
                assert "1h" in results
                assert "4h" in results
                assert "1d" in results
                
                # Each result should have timeframe set
                for tf, tf_results in results.items():
                    for result in tf_results:
                        assert result.timeframe == tf


class TestStrategyCombinations:
    """Test strategy combination functionality."""
    
    def test_generate_strategy_combinations(self):
        """Test generation of strategy combinations."""
        orchestrator = StrategyOrchestrator(capital=10000.0, max_risk_pct=0.02, lookback_days=90)
        
        # Mock strategy registry with proper attributes
        from app.service.strategy_orchestrator import StrategyDefinition
        
        mock_strategies = [
            StrategyDefinition(
                name="MA Crossover",
                func_name="ma_crossover",
                params={},
                enabled=True
            ),
            StrategyDefinition(
                name="RSI Regime",
                func_name="rsi_regime_pullback",
                params={},
                enabled=True
            ),
            StrategyDefinition(
                name="Trend EMA",
                func_name="trend_following_ema",
                params={},
                enabled=True
            )
        ]
        
        with patch.object(orchestrator, 'STRATEGY_REGISTRY', mock_strategies):
            combinations = orchestrator.generate_strategy_combinations(k_min=2)
            
            # Should have combinations of size 2 and 3
            assert len(combinations) > 0
            
            # Check combination names
            combo_names = [name for name, _ in combinations]
            assert any("MA Crossover + RSI Regime" in name for name in combo_names)
            assert any("MA Crossover + RSI Regime + Trend EMA" in name for name in combo_names)
    
    def test_combine_signals_function(self):
        """Test the combine_signals function."""
        from app.research.signals import combine_signals
        
        # Create mock signals
        signals_list = [
            pd.Series([1, 0, -1, 1, 0]),
            pd.Series([0, 1, -1, 0, 1]),
            pd.Series([1, 1, 0, 1, 0])
        ]
        
        # Test consensus method
        result = combine_signals(signals_list, method="consensus")
        assert len(result.signal) == 5
        assert result.metadata["method"] == "consensus"
        assert result.metadata["num_signals"] == 3
        
        # Test majority method
        result = combine_signals(signals_list, method="majority")
        assert len(result.signal) == 5
        assert result.metadata["method"] == "majority"
        
        # Test average method
        result = combine_signals(signals_list, method="average")
        assert len(result.signal) == 5
        assert result.metadata["method"] == "average"


class TestGlobalRanking:
    """Test global ranking system."""
    
    def test_global_ranking_service(self):
        """Test global ranking service."""
        ranking_service = GlobalRankingService()
        
        # Create mock multi-timeframe results
        mock_results = {
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
        
        # Test ranking
        ranked_strategies = ranking_service.rank_strategies(mock_results)
        
        assert len(ranked_strategies) == 1
        strategy = ranked_strategies[0]
        
        assert strategy.strategy_name == "Strategy A"
        assert strategy.global_rank == 1
        assert strategy.global_score > 0
        assert not strategy.is_combination
        assert "1h" in strategy.timeframe_breakdown
        assert "4h" in strategy.timeframe_breakdown
    
    def test_ranking_weights_configuration(self):
        """Test that ranking weights are properly configured."""
        weights = settings.RANKING_WEIGHTS
        
        # Check that all required weights are present
        required_weights = ["sharpe_ratio", "win_rate", "max_drawdown", "profit_factor", "expectancy"]
        for weight in required_weights:
            assert weight in weights
        
        # Check that weights sum to 1.0
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001
    
    def test_top_strategies_filtering(self):
        """Test filtering of top strategies."""
        ranking_service = GlobalRankingService()
        
        # Create mock ranked strategies
        mock_strategies = [
            RankedStrategy(
                strategy_name="Strategy A",
                global_score=0.8,
                global_rank=1,
                is_combination=False,
                weighted_sharpe=0.3,
                weighted_win_rate=0.2,
                weighted_max_dd=0.2,
                weighted_profit_factor=0.2,
                weighted_expectancy=0.1,
                best_sharpe=1.5,
                best_win_rate=0.6,
                best_cagr=0.08,
                best_profit_factor=1.2,
                best_expectancy=20.0,
                worst_max_dd=-0.05,
                sharpe_consistency=0.1,
                win_rate_consistency=0.05,
                cagr_consistency=0.08
            ),
            RankedStrategy(
                strategy_name="Combination A + B",
                global_score=0.7,
                global_rank=2,
                is_combination=True,
                weighted_sharpe=0.25,
                weighted_win_rate=0.18,
                weighted_max_dd=0.18,
                weighted_profit_factor=0.18,
                weighted_expectancy=0.09,
                best_sharpe=1.3,
                best_win_rate=0.55,
                best_cagr=0.06,
                best_profit_factor=1.1,
                best_expectancy=18.0,
                worst_max_dd=-0.08,
                sharpe_consistency=0.15,
                win_rate_consistency=0.08,
                cagr_consistency=0.12
            )
        ]
        
        # Test top strategies including combinations
        top_all = ranking_service.get_top_strategies(mock_strategies, top_n=2, include_combinations=True)
        assert len(top_all) == 2
        
        # Test top strategies excluding combinations
        top_individual = ranking_service.get_top_strategies(mock_strategies, top_n=2, include_combinations=False)
        assert len(top_individual) == 1
        assert not top_individual[0].is_combination


class TestUIIntegration:
    """Test UI integration with new features."""
    
    def test_multi_timeframe_ui_flow(self):
        """Test multi-timeframe UI flow."""
        # This would test the UI functions that were updated
        # For now, we'll test the key functions exist and can be called
        
        # Test that the functions exist and can be imported
        from ui.app_enhanced import compare_multi_timeframe_strategies, get_asset_metrics
        
        assert callable(compare_multi_timeframe_strategies)
        assert callable(get_asset_metrics)
    
    def test_global_ranking_ui_display(self):
        """Test that global ranking can be displayed in UI format."""
        ranking_service = GlobalRankingService()
        
        # Create mock ranked strategies
        mock_strategies = [
            RankedStrategy(
                strategy_name="Strategy A",
                global_score=0.8,
                global_rank=1,
                is_combination=False,
                weighted_sharpe=0.3,
                weighted_win_rate=0.2,
                weighted_max_dd=0.2,
                weighted_profit_factor=0.2,
                weighted_expectancy=0.1,
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
        
        # Test export functionality
        csv_content = ranking_service.export_ranking_report(mock_strategies)
        assert "Rank,Strategy,Type,Global Score" in csv_content
        assert "Strategy A" in csv_content


if __name__ == "__main__":
    pytest.main([__file__])
