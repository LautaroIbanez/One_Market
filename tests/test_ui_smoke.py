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

