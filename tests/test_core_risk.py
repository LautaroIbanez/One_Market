"""Tests for core.risk module."""
import pytest
import pandas as pd
import numpy as np
from app.core.risk import (
    PositionSize,
    StopLossTakeProfit,
    calculate_atr,
    calculate_atr_from_bars,
    compute_levels,
    calculate_position_size_fixed_risk,
    calculate_position_size_kelly,
    calculate_position_size_kelly_simple,
    calculate_var,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    validate_position_size,
    adjust_position_for_correlation
)


class TestPositionSizeModel:
    """Tests for PositionSize model."""
    
    def test_position_size_valid(self):
        """Test creating valid position size."""
        pos = PositionSize(
            quantity=1.5,
            notional_value=50000.0,
            risk_amount=500.0,
            risk_pct=0.01,
            leverage=1.0
        )
        
        assert pos.quantity == 1.5
        assert pos.notional_value == 50000.0
        assert pos.risk_amount == 500.0
        assert pos.risk_pct == 0.01
    
    def test_position_size_invalid_risk(self):
        """Test that excessive risk percentage is rejected."""
        with pytest.raises(ValueError, match="exceeds maximum"):
            PositionSize(
                quantity=1.0,
                notional_value=50000.0,
                risk_amount=10000.0,
                risk_pct=0.15,  # 15% > 10% max
                leverage=1.0
            )


class TestStopLossTakeProfitModel:
    """Tests for StopLossTakeProfit model."""
    
    def test_sl_tp_long(self):
        """Test creating SL/TP for long position."""
        levels = StopLossTakeProfit(
            entry_price=50000.0,
            stop_loss=49000.0,
            take_profit=52000.0,
            side="long",
            risk_amount=1000.0,
            reward_amount=2000.0,
            risk_reward_ratio=2.0,
            stop_loss_pct=0.02,
            take_profit_pct=0.04
        )
        
        assert levels.side == "long"
        assert levels.stop_loss < levels.entry_price
        assert levels.take_profit > levels.entry_price
    
    def test_sl_tp_invalid_side(self):
        """Test that invalid side is rejected."""
        with pytest.raises(ValueError, match="Invalid side"):
            StopLossTakeProfit(
                entry_price=50000.0,
                stop_loss=49000.0,
                take_profit=52000.0,
                side="invalid",
                risk_amount=1000.0,
                stop_loss_pct=0.02
            )


class TestATRCalculation:
    """Tests for ATR calculation."""
    
    def test_calculate_atr_basic(self):
        """Test basic ATR calculation."""
        high = pd.Series([102, 104, 103, 105, 106, 108, 107, 109, 110, 112, 111, 113, 114, 116, 115])
        low = pd.Series([98, 100, 99, 101, 102, 104, 103, 105, 106, 108, 107, 109, 110, 112, 111])
        close = pd.Series([100, 102, 101, 103, 104, 106, 105, 107, 108, 110, 109, 111, 112, 114, 113])
        
        atr = calculate_atr(high, low, close, period=14)
        
        assert len(atr) == len(high)
        assert atr.iloc[-1] > 0
        assert not atr.isna().all()
    
    def test_calculate_atr_from_bars(self):
        """Test ATR calculation from bar dictionaries."""
        bars = [
            {'high': 102, 'low': 98, 'close': 100},
            {'high': 104, 'low': 100, 'close': 102},
            {'high': 103, 'low': 99, 'close': 101},
            {'high': 105, 'low': 101, 'close': 103},
            {'high': 106, 'low': 102, 'close': 104},
            {'high': 108, 'low': 104, 'close': 106},
            {'high': 107, 'low': 103, 'close': 105},
            {'high': 109, 'low': 105, 'close': 107},
            {'high': 110, 'low': 106, 'close': 108},
            {'high': 112, 'low': 108, 'close': 110},
            {'high': 111, 'low': 107, 'close': 109},
            {'high': 113, 'low': 109, 'close': 111},
            {'high': 114, 'low': 110, 'close': 112},
            {'high': 116, 'low': 112, 'close': 114},
            {'high': 115, 'low': 111, 'close': 113}
        ]
        
        atr = calculate_atr_from_bars(bars, period=14)
        
        assert atr > 0
        assert np.isfinite(atr)
    
    def test_calculate_atr_insufficient_data(self):
        """Test that insufficient data raises error."""
        bars = [
            {'high': 102, 'low': 98, 'close': 100},
            {'high': 104, 'low': 100, 'close': 102}
        ]
        
        with pytest.raises(ValueError, match="Insufficient bars"):
            calculate_atr_from_bars(bars, period=14)


class TestComputeLevels:
    """Tests for stop loss and take profit level computation."""
    
    def test_compute_levels_long(self):
        """Test computing levels for long position."""
        levels = compute_levels(
            entry_price=50000.0,
            atr=1000.0,
            side="long",
            atr_multiplier_sl=2.0,
            atr_multiplier_tp=3.0
        )
        
        assert levels.side == "long"
        assert levels.stop_loss < levels.entry_price
        assert levels.take_profit > levels.entry_price
        assert levels.stop_loss == 48000.0  # 50000 - 2*1000
        assert levels.take_profit == 53000.0  # 50000 + 3*1000
        assert levels.risk_reward_ratio >= 1.5
    
    def test_compute_levels_short(self):
        """Test computing levels for short position."""
        levels = compute_levels(
            entry_price=50000.0,
            atr=1000.0,
            side="short",
            atr_multiplier_sl=2.0,
            atr_multiplier_tp=3.0
        )
        
        assert levels.side == "short"
        assert levels.stop_loss > levels.entry_price
        assert levels.take_profit < levels.entry_price
        assert levels.stop_loss == 52000.0  # 50000 + 2*1000
        assert levels.take_profit == 47000.0  # 50000 - 3*1000
    
    def test_compute_levels_min_rr_adjustment(self):
        """Test that minimum R/R ratio is enforced."""
        levels = compute_levels(
            entry_price=50000.0,
            atr=1000.0,
            side="long",
            atr_multiplier_sl=2.0,
            atr_multiplier_tp=2.5,  # R/R = 1.25, below min 1.5
            min_rr_ratio=1.5
        )
        
        assert levels.risk_reward_ratio >= 1.5
    
    def test_compute_levels_invalid_price(self):
        """Test that invalid entry price raises error."""
        with pytest.raises(ValueError, match="Entry price must be positive"):
            compute_levels(entry_price=-100, atr=1000, side="long")
    
    def test_compute_levels_invalid_atr(self):
        """Test that invalid ATR raises error."""
        with pytest.raises(ValueError, match="ATR must be positive"):
            compute_levels(entry_price=50000, atr=0, side="long")
    
    def test_compute_levels_invalid_side(self):
        """Test that invalid side raises error."""
        with pytest.raises(ValueError, match="Invalid side"):
            compute_levels(entry_price=50000, atr=1000, side="invalid")


class TestPositionSizeCalculations:
    """Tests for position sizing calculations."""
    
    def test_calculate_position_size_fixed_risk(self):
        """Test fixed risk position sizing."""
        pos = calculate_position_size_fixed_risk(
            capital=100000.0,
            risk_pct=0.02,  # 2%
            entry_price=50000.0,
            stop_loss=49000.0,
            leverage=1.0
        )
        
        assert pos.risk_amount == 2000.0  # 2% of 100k
        assert pos.risk_pct == 0.02
        assert pos.quantity == 2.0  # 2000 / 1000 risk per unit
    
    def test_calculate_position_size_invalid_capital(self):
        """Test that invalid capital raises error."""
        with pytest.raises(ValueError, match="Capital must be positive"):
            calculate_position_size_fixed_risk(
                capital=-100,
                risk_pct=0.02,
                entry_price=50000,
                stop_loss=49000
            )
    
    def test_calculate_position_size_excessive_risk(self):
        """Test that excessive risk percentage raises error."""
        with pytest.raises(ValueError, match="Risk percentage must be between"):
            calculate_position_size_fixed_risk(
                capital=100000,
                risk_pct=0.15,  # 15% > 10% max
                entry_price=50000,
                stop_loss=49000
            )
    
    def test_calculate_position_size_same_entry_stop(self):
        """Test that same entry and stop raises error."""
        with pytest.raises(ValueError, match="cannot be the same"):
            calculate_position_size_fixed_risk(
                capital=100000,
                risk_pct=0.02,
                entry_price=50000,
                stop_loss=50000
            )


class TestKellyPositionSizing:
    """Tests for Kelly Criterion position sizing."""
    
    def test_kelly_simple_positive_expectancy(self):
        """Test Kelly sizing with positive expectancy."""
        risk_pct = calculate_position_size_kelly_simple(
            capital=100000,
            win_rate=0.6,
            risk_reward_ratio=2.0,
            kelly_fraction=0.25,
            max_risk_pct=0.05
        )
        
        assert risk_pct > 0
        assert risk_pct <= 0.05  # Capped at max
    
    def test_kelly_simple_negative_expectancy(self):
        """Test Kelly sizing with negative expectancy."""
        risk_pct = calculate_position_size_kelly_simple(
            capital=100000,
            win_rate=0.3,
            risk_reward_ratio=1.0,
            kelly_fraction=0.25,
            max_risk_pct=0.05
        )
        
        assert risk_pct == 0  # Should return 0 for negative expectancy
    
    def test_kelly_full_calculation(self):
        """Test full Kelly calculation."""
        risk_pct = calculate_position_size_kelly(
            capital=100000,
            win_rate=0.55,
            avg_win=0.03,
            avg_loss=0.015,
            kelly_fraction=0.25,
            max_risk_pct=0.05
        )
        
        assert risk_pct > 0
        assert risk_pct <= 0.05
    
    def test_kelly_invalid_win_rate(self):
        """Test that invalid win rate raises error."""
        with pytest.raises(ValueError, match="Win rate must be between"):
            calculate_position_size_kelly_simple(
                capital=100000,
                win_rate=1.5,
                risk_reward_ratio=2.0
            )


class TestRiskMetrics:
    """Tests for risk metrics calculations."""
    
    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        returns = pd.Series([0.01, -0.005, 0.015, 0.02, -0.01, 0.005, 0.01])
        
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.0, periods_per_year=252)
        
        assert np.isfinite(sharpe)
    
    def test_calculate_sharpe_zero_std(self):
        """Test Sharpe ratio with zero standard deviation."""
        returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        
        sharpe = calculate_sharpe_ratio(returns)
        
        assert sharpe == 0.0
    
    def test_calculate_var_historical(self):
        """Test historical VaR calculation."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 1000))
        
        var = calculate_var(returns, confidence_level=0.95, method="historical")
        
        assert var >= 0  # VaR is positive (represents loss)
    
    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        equity = pd.Series([100, 110, 105, 115, 108, 120, 115, 125])
        
        max_dd, peak_idx, trough_idx = calculate_max_drawdown(equity)
        
        assert max_dd >= 0
        assert max_dd <= 1.0
        assert peak_idx <= trough_idx
    
    def test_calculate_max_drawdown_no_drawdown(self):
        """Test max drawdown with no drawdown."""
        equity = pd.Series([100, 110, 120, 130])
        
        max_dd, peak_idx, trough_idx = calculate_max_drawdown(equity)
        
        assert max_dd == 0.0


class TestPositionValidation:
    """Tests for position validation."""
    
    def test_validate_position_size_valid(self):
        """Test validating valid position size."""
        is_valid, msg = validate_position_size(
            quantity=1.0,
            entry_price=50000.0,
            capital=100000.0,
            max_position_pct=0.2
        )
        
        assert is_valid is True
        assert msg == "Position size is valid"
    
    def test_validate_position_size_too_large(self):
        """Test validating oversized position."""
        is_valid, msg = validate_position_size(
            quantity=10.0,
            entry_price=50000.0,
            capital=100000.0,
            max_position_pct=0.2
        )
        
        assert is_valid is False
        assert "exceeds maximum" in msg
    
    def test_validate_position_size_exceeds_capital(self):
        """Test position exceeding capital."""
        is_valid, msg = validate_position_size(
            quantity=3.0,
            entry_price=50000.0,
            capital=100000.0,
            max_position_pct=0.5
        )
        
        assert is_valid is False
        assert "exceeds capital" in msg


class TestCorrelationAdjustment:
    """Tests for correlation-based position adjustment."""
    
    def test_adjust_position_for_correlation(self):
        """Test position adjustment for correlation."""
        portfolio = [
            {'symbol': 'BTC-USDT', 'size': 1.0},
            {'symbol': 'ETH-USDT', 'size': 5.0}
        ]
        
        corr_matrix = pd.DataFrame({
            'BTC-USDT': [1.0, 0.8, 0.6],
            'ETH-USDT': [0.8, 1.0, 0.7],
            'XRP-USDT': [0.6, 0.7, 1.0]
        }, index=['BTC-USDT', 'ETH-USDT', 'XRP-USDT'])
        
        adjusted = adjust_position_for_correlation(
            base_position_size=10.0,
            portfolio_positions=portfolio,
            correlation_matrix=corr_matrix,
            new_symbol='XRP-USDT',
            reduction_factor=0.5
        )
        
        # Should be reduced due to correlation
        assert adjusted < 10.0
    
    def test_adjust_position_no_correlation_data(self):
        """Test adjustment with no correlation data."""
        adjusted = adjust_position_for_correlation(
            base_position_size=10.0,
            portfolio_positions=[],
            correlation_matrix=pd.DataFrame(),
            new_symbol='BTC-USDT'
        )
        
        # Should return base size unchanged
        assert adjusted == 10.0

