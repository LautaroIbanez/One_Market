"""Advanced Risk Management Module.

This module implements sophisticated risk management techniques:
- Value at Risk (VaR) - Historical and Parametric
- Expected Shortfall (CVaR/ES)
- Cross-asset correlations
- Dynamic position sizing based on volatility/correlation
- Adaptive stops based on recent volatility
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from scipy import stats
import logging

from app.research.indicators import atr

logger = logging.getLogger(__name__)


class VaRResult(BaseModel):
    """Value at Risk calculation result."""
    var_amount: float = Field(..., description="VaR in dollar amount")
    var_pct: float = Field(..., description="VaR as percentage")
    confidence_level: float = Field(..., description="Confidence level (e.g., 0.95)")
    method: str = Field(..., description="Calculation method")
    horizon_days: int = Field(..., description="Time horizon in days")


class ExpectedShortfallResult(BaseModel):
    """Expected Shortfall (CVaR) calculation result."""
    es_amount: float = Field(..., description="Expected Shortfall in dollars")
    es_pct: float = Field(..., description="ES as percentage")
    confidence_level: float = Field(..., description="Confidence level")
    var_amount: float = Field(..., description="Corresponding VaR")


class CorrelationMatrix(BaseModel):
    """Correlation matrix for multiple assets/strategies."""
    symbols: List[str] = Field(..., description="Asset/strategy names")
    correlations: List[List[float]] = Field(..., description="Correlation matrix")
    period_days: int = Field(..., description="Calculation period")
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True
    
    def get_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Get correlation between two symbols."""
        try:
            idx1 = self.symbols.index(symbol1)
            idx2 = self.symbols.index(symbol2)
            return self.correlations[idx1][idx2]
        except (ValueError, IndexError):
            return None


class DynamicStopResult(BaseModel):
    """Dynamic stop loss calculation result."""
    stop_loss: float = Field(..., description="Stop loss price", gt=0)
    atr_value: float = Field(..., description="Current ATR")
    atr_multiplier: float = Field(..., description="ATR multiplier used")
    volatility_regime: str = Field(..., description="Volatility regime (low/normal/high)")
    adjustment_factor: float = Field(..., description="Adjustment factor applied")


class AdvancedRiskManager:
    """Advanced risk management system."""
    
    def __init__(
        self,
        capital: float = 100000.0,
        max_portfolio_var_pct: float = 0.02,
        var_confidence: float = 0.95,
        correlation_lookback_days: int = 60
    ):
        """Initialize advanced risk manager.
        
        Args:
            capital: Total capital
            max_portfolio_var_pct: Maximum portfolio VaR as % of capital
            var_confidence: Confidence level for VaR calculations
            correlation_lookback_days: Lookback period for correlation matrix
        """
        self.capital = capital
        self.max_portfolio_var_pct = max_portfolio_var_pct
        self.var_confidence = var_confidence
        self.correlation_lookback_days = correlation_lookback_days
    
    def calculate_var_historical(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        horizon_days: int = 1
    ) -> VaRResult:
        """Calculate Value at Risk using historical method.
        
        Args:
            returns: Historical returns series
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            horizon_days: Time horizon in days
            
        Returns:
            VaRResult with VaR calculation
        """
        if len(returns) < 30:
            logger.warning("Insufficient data for VaR calculation")
            return VaRResult(
                var_amount=0.0,
                var_pct=0.0,
                confidence_level=confidence_level,
                method="historical",
                horizon_days=horizon_days
            )
        
        # Remove NaN values
        returns_clean = returns.dropna()
        
        # Calculate percentile
        var_percentile = 1 - confidence_level
        var_return = returns_clean.quantile(var_percentile)
        
        # Scale to horizon
        var_return_scaled = var_return * np.sqrt(horizon_days)
        
        # Convert to dollar amount
        var_amount = abs(var_return_scaled * self.capital)
        var_pct = abs(var_return_scaled)
        
        return VaRResult(
            var_amount=var_amount,
            var_pct=var_pct,
            confidence_level=confidence_level,
            method="historical",
            horizon_days=horizon_days
        )
    
    def calculate_var_parametric(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        horizon_days: int = 1
    ) -> VaRResult:
        """Calculate Value at Risk using parametric method (assumes normal distribution).
        
        Args:
            returns: Historical returns series
            confidence_level: Confidence level
            horizon_days: Time horizon in days
            
        Returns:
            VaRResult with VaR calculation
        """
        if len(returns) < 30:
            logger.warning("Insufficient data for parametric VaR")
            return VaRResult(
                var_amount=0.0,
                var_pct=0.0,
                confidence_level=confidence_level,
                method="parametric",
                horizon_days=horizon_days
            )
        
        # Calculate mean and std
        returns_clean = returns.dropna()
        mean_return = returns_clean.mean()
        std_return = returns_clean.std()
        
        # Get z-score for confidence level
        z_score = stats.norm.ppf(1 - confidence_level)
        
        # Calculate VaR
        var_return = mean_return + z_score * std_return
        
        # Scale to horizon
        var_return_scaled = var_return * np.sqrt(horizon_days)
        
        # Convert to dollar amount
        var_amount = abs(var_return_scaled * self.capital)
        var_pct = abs(var_return_scaled)
        
        return VaRResult(
            var_amount=var_amount,
            var_pct=var_pct,
            confidence_level=confidence_level,
            method="parametric",
            horizon_days=horizon_days
        )
    
    def calculate_expected_shortfall(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        horizon_days: int = 1
    ) -> ExpectedShortfallResult:
        """Calculate Expected Shortfall (Conditional VaR).
        
        Expected Shortfall is the average loss given that loss exceeds VaR.
        
        Args:
            returns: Historical returns series
            confidence_level: Confidence level
            horizon_days: Time horizon in days
            
        Returns:
            ExpectedShortfallResult with ES calculation
        """
        # First calculate VaR
        var_result = self.calculate_var_historical(returns, confidence_level, horizon_days)
        
        if len(returns) < 30:
            return ExpectedShortfallResult(
                es_amount=var_result.var_amount,
                es_pct=var_result.var_pct,
                confidence_level=confidence_level,
                var_amount=var_result.var_amount
            )
        
        # Calculate ES as average of returns beyond VaR
        returns_clean = returns.dropna()
        var_percentile = 1 - confidence_level
        var_threshold = returns_clean.quantile(var_percentile)
        
        # Get tail returns (worse than VaR)
        tail_returns = returns_clean[returns_clean <= var_threshold]
        
        if len(tail_returns) == 0:
            es_return = var_threshold
        else:
            es_return = tail_returns.mean()
        
        # Scale to horizon
        es_return_scaled = es_return * np.sqrt(horizon_days)
        
        # Convert to dollar amount
        es_amount = abs(es_return_scaled * self.capital)
        es_pct = abs(es_return_scaled)
        
        return ExpectedShortfallResult(
            es_amount=es_amount,
            es_pct=es_pct,
            confidence_level=confidence_level,
            var_amount=var_result.var_amount
        )
    
    def calculate_correlation_matrix(
        self,
        returns_dict: Dict[str, pd.Series],
        min_periods: int = 30
    ) -> CorrelationMatrix:
        """Calculate correlation matrix for multiple assets/strategies.
        
        Args:
            returns_dict: Dictionary of {symbol: returns_series}
            min_periods: Minimum periods for correlation calculation
            
        Returns:
            CorrelationMatrix with correlations
        """
        if not returns_dict or len(returns_dict) < 2:
            logger.warning("Need at least 2 assets for correlation matrix")
            return CorrelationMatrix(
                symbols=list(returns_dict.keys()),
                correlations=[[1.0]],
                period_days=0
            )
        
        # Align returns to same index
        returns_df = pd.DataFrame(returns_dict)
        returns_df = returns_df.dropna()
        
        if len(returns_df) < min_periods:
            logger.warning(f"Insufficient data for correlation ({len(returns_df)} < {min_periods})")
        
        # Calculate correlation matrix
        corr_matrix = returns_df.corr()
        
        # Convert to list of lists
        symbols = list(returns_dict.keys())
        correlations = corr_matrix.values.tolist()
        
        return CorrelationMatrix(
            symbols=symbols,
            correlations=correlations,
            period_days=len(returns_df)
        )
    
    def calculate_portfolio_var(
        self,
        positions: Dict[str, float],
        returns_dict: Dict[str, pd.Series],
        confidence_level: float = 0.95
    ) -> VaRResult:
        """Calculate portfolio VaR accounting for correlations.
        
        Args:
            positions: Dictionary of {symbol: dollar_amount}
            returns_dict: Dictionary of {symbol: returns_series}
            confidence_level: Confidence level
            
        Returns:
            VaRResult for entire portfolio
        """
        if not positions or not returns_dict:
            return VaRResult(
                var_amount=0.0,
                var_pct=0.0,
                confidence_level=confidence_level,
                method="portfolio",
                horizon_days=1
            )
        
        # Calculate correlation matrix
        corr_matrix = self.calculate_correlation_matrix(returns_dict)
        
        # Calculate individual VaRs
        individual_vars = {}
        for symbol, amount in positions.items():
            if symbol in returns_dict:
                returns = returns_dict[symbol]
                std_return = returns.std()
                z_score = stats.norm.ppf(1 - confidence_level)
                var = abs(amount * std_return * z_score)
                individual_vars[symbol] = var
        
        if not individual_vars:
            return VaRResult(
                var_amount=0.0,
                var_pct=0.0,
                confidence_level=confidence_level,
                method="portfolio",
                horizon_days=1
            )
        
        # Calculate portfolio VaR with correlations
        symbols = list(individual_vars.keys())
        vars_array = np.array([individual_vars[s] for s in symbols])
        
        # Get correlation sub-matrix
        corr_values = []
        for s1 in symbols:
            row = []
            for s2 in symbols:
                corr = corr_matrix.get_correlation(s1, s2)
                row.append(corr if corr is not None else 1.0 if s1 == s2 else 0.0)
            corr_values.append(row)
        
        corr_array = np.array(corr_values)
        
        # Portfolio VaR = sqrt(V^T * Corr * V) where V is vector of individual VaRs
        portfolio_var = np.sqrt(vars_array @ corr_array @ vars_array.T)
        
        total_position = sum(positions.values())
        var_pct = portfolio_var / total_position if total_position > 0 else 0.0
        
        return VaRResult(
            var_amount=portfolio_var,
            var_pct=var_pct,
            confidence_level=confidence_level,
            method="portfolio",
            horizon_days=1
        )
    
    def calculate_position_size_var_adjusted(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        returns: pd.Series,
        max_var_pct: Optional[float] = None
    ) -> float:
        """Calculate position size adjusted for VaR constraint.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            returns: Historical returns
            max_var_pct: Maximum VaR as % of capital (defaults to instance setting)
            
        Returns:
            Position size in units
        """
        if max_var_pct is None:
            max_var_pct = self.max_portfolio_var_pct
        
        # Calculate VaR
        var_result = self.calculate_var_historical(returns, self.var_confidence)
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit == 0:
            return 0.0
        
        # Max position based on VaR constraint
        max_var_dollars = self.capital * max_var_pct
        max_position_var = max_var_dollars / var_result.var_pct if var_result.var_pct > 0 else 0
        
        # Max position based on stop loss
        max_position_sl = (self.capital * max_var_pct) / risk_per_unit
        
        # Use minimum of both constraints
        position_size = min(max_position_var, max_position_sl)
        
        return max(0.0, position_size)
    
    def calculate_dynamic_stop(
        self,
        df: pd.DataFrame,
        entry_price: float,
        signal_direction: int,
        atr_period: int = 14,
        base_atr_multiplier: float = 2.0,
        volatility_lookback: int = 50
    ) -> DynamicStopResult:
        """Calculate dynamic stop loss adjusted for current volatility regime.
        
        Args:
            df: DataFrame with OHLCV data
            entry_price: Entry price
            signal_direction: 1 for long, -1 for short
            atr_period: ATR calculation period
            base_atr_multiplier: Base ATR multiplier
            volatility_lookback: Lookback period for volatility regime
            
        Returns:
            DynamicStopResult with adaptive stop
        """
        if len(df) < max(atr_period, volatility_lookback):
            # Fallback to simple ATR stop
            atr_val = atr(df['high'], df['low'], df['close'], atr_period).iloc[-1]
            if signal_direction == 1:
                stop_loss = entry_price - (atr_val * base_atr_multiplier)
            else:
                stop_loss = entry_price + (atr_val * base_atr_multiplier)
            
            return DynamicStopResult(
                stop_loss=stop_loss,
                atr_value=atr_val,
                atr_multiplier=base_atr_multiplier,
                volatility_regime="normal",
                adjustment_factor=1.0
            )
        
        # Calculate ATR
        atr_series = atr(df['high'], df['low'], df['close'], atr_period)
        current_atr = atr_series.iloc[-1]
        
        # Determine volatility regime
        recent_atr = atr_series.tail(volatility_lookback)
        atr_mean = recent_atr.mean()
        atr_std = recent_atr.std()
        
        # Z-score of current ATR
        atr_zscore = (current_atr - atr_mean) / atr_std if atr_std > 0 else 0
        
        # Classify volatility regime
        if atr_zscore > 1.0:
            volatility_regime = "high"
            adjustment_factor = 1.3  # Wider stops in high volatility
        elif atr_zscore < -1.0:
            volatility_regime = "low"
            adjustment_factor = 0.8  # Tighter stops in low volatility
        else:
            volatility_regime = "normal"
            adjustment_factor = 1.0
        
        # Adjust ATR multiplier
        adjusted_multiplier = base_atr_multiplier * adjustment_factor
        
        # Calculate stop loss
        if signal_direction == 1:  # Long
            stop_loss = entry_price - (current_atr * adjusted_multiplier)
        else:  # Short
            stop_loss = entry_price + (current_atr * adjusted_multiplier)
        
        # Ensure positive price
        stop_loss = max(stop_loss, entry_price * 0.5)
        
        return DynamicStopResult(
            stop_loss=stop_loss,
            atr_value=current_atr,
            atr_multiplier=adjusted_multiplier,
            volatility_regime=volatility_regime,
            adjustment_factor=adjustment_factor
        )
    
    def check_portfolio_risk_limits(
        self,
        current_positions: Dict[str, float],
        returns_dict: Dict[str, pd.Series],
        proposed_trade: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Check if portfolio is within risk limits.
        
        Args:
            current_positions: Current positions {symbol: dollar_amount}
            returns_dict: Returns for each position
            proposed_trade: Optional proposed trade to check
            
        Returns:
            Tuple of (is_within_limits, reason)
        """
        # Calculate current portfolio VaR
        current_var = self.calculate_portfolio_var(
            current_positions,
            returns_dict,
            self.var_confidence
        )
        
        max_var_dollars = self.capital * self.max_portfolio_var_pct
        
        if current_var.var_amount > max_var_dollars:
            return False, f"Portfolio VaR ({current_var.var_amount:.2f}) exceeds limit ({max_var_dollars:.2f})"
        
        # Check proposed trade if provided
        if proposed_trade:
            symbol = proposed_trade.get('symbol')
            amount = proposed_trade.get('amount', 0)
            
            if symbol and amount:
                # Simulate adding proposed position
                proposed_positions = current_positions.copy()
                proposed_positions[symbol] = proposed_positions.get(symbol, 0) + amount
                
                # Calculate new VaR
                proposed_var = self.calculate_portfolio_var(
                    proposed_positions,
                    returns_dict,
                    self.var_confidence
                )
                
                if proposed_var.var_amount > max_var_dollars:
                    return False, f"Proposed trade would increase VaR to {proposed_var.var_amount:.2f} (limit: {max_var_dollars:.2f})"
        
        return True, "Portfolio within risk limits"
    
    def get_risk_summary(
        self,
        returns: pd.Series,
        positions: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive risk summary.
        
        Args:
            returns: Returns series
            positions: Optional current positions
            
        Returns:
            Dictionary with risk metrics
        """
        var_hist = self.calculate_var_historical(returns, self.var_confidence)
        var_param = self.calculate_var_parametric(returns, self.var_confidence)
        es = self.calculate_expected_shortfall(returns, self.var_confidence)
        
        summary = {
            'var_historical_amount': var_hist.var_amount,
            'var_historical_pct': var_hist.var_pct,
            'var_parametric_amount': var_param.var_amount,
            'var_parametric_pct': var_param.var_pct,
            'expected_shortfall_amount': es.es_amount,
            'expected_shortfall_pct': es.es_pct,
            'confidence_level': self.var_confidence,
            'max_portfolio_var': self.capital * self.max_portfolio_var_pct
        }
        
        if positions:
            summary['num_positions'] = len(positions)
            summary['total_exposure'] = sum(positions.values())
            summary['exposure_pct'] = sum(positions.values()) / self.capital
        
        return summary

