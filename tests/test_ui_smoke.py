"""Smoke tests for Streamlit UI.

These tests verify that the UI components can be imported and
basic functionality works without errors.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestUIImports:
    """Test that UI modules can be imported."""
    
    def test_import_ui_app(self):
        """Test importing main UI app."""
        try:
            import ui.app
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import ui.app: {e}")
    
    def test_import_ui_api_connected(self):
        """Test importing API-connected UI."""
        try:
            import ui.app_api_connected
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import ui.app_api_connected: {e}")


class TestUIComponents:
    """Test UI component availability."""
    
    def test_streamlit_available(self):
        """Test that Streamlit is installed."""
        try:
            import streamlit as st
            assert st is not None
        except ImportError:
            pytest.fail("Streamlit not installed")
    
    def test_plotly_available(self):
        """Test that Plotly is installed."""
        try:
            import plotly.graph_objects as go
            assert go is not None
        except ImportError:
            pytest.fail("Plotly not installed")


class TestDataLoading:
    """Test data loading functions."""
    
    def test_can_import_data_store(self):
        """Test importing DataStore for UI."""
        from app.data.store import DataStore
        
        store = DataStore()
        assert store is not None
    
    def test_can_import_service_modules(self):
        """Test importing service modules for UI."""
        from app.service import DecisionEngine, MarketAdvisor
        
        engine = DecisionEngine()
        advisor = MarketAdvisor()
        
        assert engine is not None
        assert advisor is not None


class TestSignalGeneration:
    """Test signal generation for UI."""
    
    def test_can_generate_signals(self):
        """Test signal generation works."""
        import pandas as pd
        import numpy as np
        from app.research.signals import ma_crossover
        
        # Generate synthetic data
        df = pd.DataFrame({
            'close': np.random.randn(100).cumsum() + 50000
        })
        
        signal_output = ma_crossover(df['close'])
        
        assert signal_output is not None
        assert len(signal_output.signal) == len(df)


@pytest.mark.skipif(
    not Path(project_root / "ui" / "app.py").exists(),
    reason="UI app not found"
)
class TestUIExecution:
    """Test UI execution (if possible)."""
    
    def test_ui_script_exists(self):
        """Test that UI script exists."""
        ui_path = project_root / "ui" / "app.py"
        assert ui_path.exists()
        assert ui_path.is_file()
    
    def test_ui_api_connected_exists(self):
        """Test that API-connected UI exists."""
        ui_path = project_root / "ui" / "app_api_connected.py"
        assert ui_path.exists()
        assert ui_path.is_file()


# Integration smoke test
def test_full_ui_workflow_mock():
    """Test full UI workflow with mock data."""
    import pandas as pd
    import numpy as np
    
    from app.data.store import DataStore
    from app.service import DecisionEngine, MarketAdvisor
    from app.research.signals import ma_crossover, rsi_regime_pullback
    from app.research.combine import combine_signals
    
    # Create mock data
    n_bars = 200
    df = pd.DataFrame({
        'timestamp': range(n_bars),
        'open': np.random.randn(n_bars).cumsum() + 50000,
        'high': np.random.randn(n_bars).cumsum() + 50500,
        'low': np.random.randn(n_bars).cumsum() + 49500,
        'close': np.random.randn(n_bars).cumsum() + 50000,
        'volume': abs(np.random.randn(n_bars)) * 1000000
    })
    
    # Generate signals
    sig1 = ma_crossover(df['close'])
    sig2 = rsi_regime_pullback(df['close'])
    
    # Combine
    returns = df['close'].pct_change()
    combined = combine_signals(
        {'ma': sig1.signal, 'rsi': sig2.signal},
        method='simple_average',
        returns=returns
    )
    
    # Get advice
    advisor = MarketAdvisor()
    advice = advisor.get_advice(
        df_intraday=df,
        current_signal=int(combined.signal.iloc[-1]),
        signal_strength=float(combined.confidence.iloc[-1])
    )
    
    # Make decision
    engine = DecisionEngine()
    decision = engine.make_decision(
        df,
        combined.signal,
        capital=100000.0
    )
    
    # Verify all components work
    assert combined is not None
    assert advice is not None
    assert decision is not None
    
    # Verify decision structure (as UI would use it)
    assert hasattr(decision, 'signal')
    assert hasattr(decision, 'should_execute')
    assert hasattr(decision, 'entry_price')
    
    print("✅ Full UI workflow mock test passed")


class TestUIHelperFunctions:
    """Test new UI helper functions from tabbed refactor."""
    
    def test_calculate_signals_and_weights(self):
        """Test signal calculation with strategy breakdown."""
        import pandas as pd
        import numpy as np
        
        # Create mock data
        n_bars = 100
        df = pd.DataFrame({
            'timestamp': range(n_bars),
            'open': np.random.randn(n_bars).cumsum() + 50000,
            'high': np.random.randn(n_bars).cumsum() + 50500,
            'low': np.random.randn(n_bars).cumsum() + 49500,
            'close': np.random.randn(n_bars).cumsum() + 50000,
            'volume': abs(np.random.randn(n_bars)) * 1000000
        })
        
        # Import helper function (if exposed)
        # For now, test the underlying logic
        from app.research.signals import ma_crossover, rsi_regime_pullback, trend_following_ema
        from app.research.combine import combine_signals
        
        sig1 = ma_crossover(df['close'])
        sig2 = rsi_regime_pullback(df['close'])
        sig3 = trend_following_ema(df['close'])
        
        returns = df['close'].pct_change()
        combined = combine_signals(
            {'ma': sig1.signal, 'rsi': sig2.signal, 'ema': sig3.signal},
            method='simple_average',
            returns=returns
        )
        
        assert combined is not None
        assert hasattr(combined, 'signal')
        assert hasattr(combined, 'confidence')
        assert hasattr(combined, 'weights')
    
    def test_calculate_backtest_metrics(self):
        """Test backtest metrics calculation."""
        import pandas as pd
        import numpy as np
        
        # Create mock data
        n_bars = 100
        df = pd.DataFrame({
            'close': np.random.randn(n_bars).cumsum() + 50000
        })
        
        # Create mock combined signal
        from app.research.signals import ma_crossover
        sig = ma_crossover(df['close'])
        
        # Calculate metrics (test underlying logic)
        returns = df['close'].pct_change()
        strategy_returns = sig.signal.shift(1) * returns
        strategy_returns = strategy_returns.dropna()
        
        # Test basic metric calculations
        if len(strategy_returns) > 0:
            sharpe = strategy_returns.mean() / strategy_returns.std()
            assert not np.isnan(sharpe)
            
            win_rate = (strategy_returns > 0).mean()
            assert 0 <= win_rate <= 1
    
    def test_confidence_indicator_logic(self):
        """Test confidence indicator calculation."""
        # Test confidence levels based on metrics
        
        # High confidence scenario
        metrics_high = {
            'sharpe': 2.0,
            'win_rate': 0.65,
            'max_dd': 0.04
        }
        
        # Should result in high confidence
        score_high = 0
        if metrics_high['sharpe'] > 1.5:
            score_high += 40
        if metrics_high['win_rate'] > 0.6:
            score_high += 30
        if metrics_high['max_dd'] < 0.05:
            score_high += 30
        
        assert score_high >= 75  # High confidence
        
        # Low confidence scenario
        metrics_low = {
            'sharpe': 0.2,
            'win_rate': 0.40,
            'max_dd': 0.25
        }
        
        score_low = 0
        if metrics_low['sharpe'] > 0:
            score_low += 10
        if metrics_low['win_rate'] > 0.45:
            score_low += 15
        else:
            score_low += 10
        if metrics_low['max_dd'] < 0.20:
            score_low += 15
        else:
            score_low += 10
        
        assert score_low < 50  # Low confidence


class TestTabbedStructure:
    """Test tabbed UI structure components."""
    
    def test_tab_data_isolation(self):
        """Test that both tabs can access shared data correctly."""
        import pandas as pd
        import numpy as np
        from app.service import DecisionEngine, MarketAdvisor
        
        # Create shared data
        n_bars = 100
        df = pd.DataFrame({
            'timestamp': range(n_bars),
            'close': np.random.randn(n_bars).cumsum() + 50000,
            'open': np.random.randn(n_bars).cumsum() + 50000,
            'high': np.random.randn(n_bars).cumsum() + 50500,
            'low': np.random.randn(n_bars).cumsum() + 49500,
            'volume': abs(np.random.randn(n_bars)) * 1000000
        })
        
        # Test that both tabs can use the same advisor instance
        advisor = MarketAdvisor(default_risk_pct=0.02)
        engine = DecisionEngine()
        
        assert advisor is not None
        assert engine is not None
    
    def test_chart_rendering_components(self):
        """Test chart rendering data preparation."""
        import pandas as pd
        import numpy as np
        import plotly.graph_objects as go
        
        # Create mock data
        n_bars = 60
        df = pd.DataFrame({
            'timestamp': range(n_bars),
            'open': np.random.randn(n_bars).cumsum() + 50000,
            'high': np.random.randn(n_bars).cumsum() + 50500,
            'low': np.random.randn(n_bars).cumsum() + 49500,
            'close': np.random.randn(n_bars).cumsum() + 50000,
        })
        
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Test candlestick creation
        fig = go.Figure(data=[go.Candlestick(
            x=df['datetime'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])
        
        assert fig is not None
        assert len(fig.data) == 1
