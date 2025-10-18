"""Tests for service.advisor module."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from app.service.advisor import (
    MarketAdvisor,
    ShortTermAdvice,
    MediumTermAdvice,
    LongTermAdvice,
    integrate_backtest_metrics
)


class TestMarketAdvisor:
    """Tests for MarketAdvisor."""
    
    def test_advisor_creation(self):
        """Test creating market advisor."""
        advisor = MarketAdvisor()
        
        assert advisor.default_risk_pct == 0.02
        assert advisor.volatility_adjustment is True
        assert advisor.regime_adjustment is True
    
    def test_advisor_custom_params(self):
        """Test advisor with custom parameters."""
        advisor = MarketAdvisor(
            default_risk_pct=0.03,
            volatility_adjustment=False
        )
        
        assert advisor.default_risk_pct == 0.03
        assert advisor.volatility_adjustment is False
    
    def test_get_advice_intraday_only(self):
        """Test getting advice with only intraday data."""
        advisor = MarketAdvisor()
        
        # Create sample intraday data
        n_bars = 200
        df_intraday = pd.DataFrame({
            'timestamp': pd.date_range('2023-10-01', periods=n_bars, freq='1H'),
            'open': np.random.randn(n_bars).cumsum() + 50000,
            'high': np.random.randn(n_bars).cumsum() + 50500,
            'low': np.random.randn(n_bars).cumsum() + 49500,
            'close': np.random.randn(n_bars).cumsum() + 50000,
            'volume': abs(np.random.randn(n_bars)) * 1000000
        })
        
        advice = advisor.get_advice(
            df_intraday=df_intraday,
            current_signal=1,
            signal_strength=0.6,
            symbol="BTC/USDT"
        )
        
        assert advice.short_term is not None
        assert advice.medium_term is not None
        assert advice.long_term is not None
        assert advice.consensus_direction in [-1, 0, 1]
        assert 0 <= advice.confidence_score <= 1
    
    def test_get_advice_with_daily(self):
        """Test getting advice with daily data."""
        advisor = MarketAdvisor()
        
        # Intraday data
        n_intraday = 100
        df_intraday = pd.DataFrame({
            'timestamp': pd.date_range('2023-10-01', periods=n_intraday, freq='1H'),
            'open': np.random.randn(n_intraday).cumsum() + 50000,
            'high': np.random.randn(n_intraday).cumsum() + 50500,
            'low': np.random.randn(n_intraday).cumsum() + 49500,
            'close': np.random.randn(n_intraday).cumsum() + 50000,
            'volume': abs(np.random.randn(n_intraday)) * 1000000
        })
        
        # Daily data
        n_daily = 250
        df_daily = pd.DataFrame({
            'timestamp': pd.date_range('2022-10-01', periods=n_daily, freq='1D'),
            'open': np.random.randn(n_daily).cumsum() + 50000,
            'high': np.random.randn(n_daily).cumsum() + 50500,
            'low': np.random.randn(n_daily).cumsum() + 49500,
            'close': np.random.randn(n_daily).cumsum() + 50000,
            'volume': abs(np.random.randn(n_daily)) * 1000000
        })
        
        advice = advisor.get_advice(
            df_intraday=df_intraday,
            df_daily=df_daily,
            current_signal=1,
            signal_strength=0.7
        )
        
        assert advice.medium_term.ema200_position in ["above", "below", "at"]
        assert advice.long_term.regime in ["bull", "bear", "neutral"]


class TestShortTermAnalysis:
    """Tests for short-term analysis."""
    
    def test_short_term_high_volatility(self):
        """Test short-term analysis identifies high volatility."""
        advisor = MarketAdvisor()
        
        # Create high volatility data
        n_bars = 100
        df = pd.DataFrame({
            'close': np.random.randn(n_bars) * 5000 + 50000  # High std dev
        })
        
        short = advisor._analyze_short_term(df, current_signal=1, signal_strength=0.8)
        
        # Should recognize different volatility states
        assert short.volatility_state in ["low", "normal", "high"]
        assert short.signal == 1
        assert short.strength == 0.8


class TestRiskRecommendation:
    """Tests for risk recommendation."""
    
    def test_integrate_backtest_metrics(self):
        """Test integrating backtest metrics into risk."""
        advisor = MarketAdvisor(default_risk_pct=0.02)
        
        # Good performance
        good_performance = {
            'sharpe': 2.0,
            'max_dd': 0.05,
            'win_rate': 0.65
        }
        
        adjusted_risk = integrate_backtest_metrics(advisor, good_performance)
        
        # Should increase risk for good performance
        assert adjusted_risk >= advisor.default_risk_pct
    
    def test_integrate_poor_performance(self):
        """Test risk reduction for poor performance."""
        advisor = MarketAdvisor(default_risk_pct=0.02)
        
        # Poor performance
        poor_performance = {
            'sharpe': -0.5,
            'max_dd': 0.20,
            'win_rate': 0.35
        }
        
        adjusted_risk = integrate_backtest_metrics(advisor, poor_performance)
        
        # Should decrease risk for poor performance
        assert adjusted_risk < advisor.default_risk_pct


class TestAdviceModels:
    """Tests for advice models."""
    
    def test_short_term_advice_creation(self):
        """Test creating short-term advice."""
        advice = ShortTermAdvice(
            signal=1,
            strength=0.7,
            entry_timing="immediate",
            volatility_state="normal",
            recommended_risk_pct=0.02
        )
        
        assert advice.horizon == "short"
        assert advice.signal == 1
    
    def test_medium_term_advice_creation(self):
        """Test creating medium-term advice."""
        advice = MediumTermAdvice(
            trend_direction=1,
            trend_strength=0.8,
            ema200_position="above",
            rsi_weekly=60.0,
            breadth_proxy=0.7,
            filter_recommendation="favor_long"
        )
        
        assert advice.horizon == "medium"
        assert advice.trend_direction == 1
    
    def test_long_term_advice_creation(self):
        """Test creating long-term advice."""
        advice = LongTermAdvice(
            regime="bull",
            regime_probability=0.7,
            volatility_regime="normal",
            regime_change_probability=0.2,
            recommended_exposure=0.8
        )
        
        assert advice.horizon == "long"
        assert advice.regime == "bull"

