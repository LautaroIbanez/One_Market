"""Multi-horizon market advisor.

This module provides market analysis across different timeframes:
- Short-term (today): Intraday signals and entry timing
- Medium-term (week): Trend filters (EMA200, RSI weekly, breadth proxies)
- Long-term (regime): Market regime probability and risk adjustments
"""
import pandas as pd
import numpy as np
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.research.indicators import ema, rsi
from app.research.features import trend_strength, relative_volatility


class ShortTermAdvice(BaseModel):
    """Short-term (intraday) advice."""
    
    horizon: str = Field(default="short", description="Time horizon")
    signal: int = Field(..., description="Intraday signal: 1, -1, 0")
    strength: float = Field(..., description="Signal strength")
    entry_timing: Literal["immediate", "pullback", "wait"] = Field(..., description="Entry timing advice")
    volatility_state: Literal["low", "normal", "high"] = Field(..., description="Volatility state")
    recommended_risk_pct: float = Field(..., description="Recommended risk %")


class MediumTermAdvice(BaseModel):
    """Medium-term (weekly) advice."""
    
    horizon: str = Field(default="medium", description="Time horizon")
    trend_direction: int = Field(..., description="Weekly trend: 1, -1, 0")
    trend_strength: float = Field(..., description="Trend strength (0-1)")
    ema200_position: Literal["above", "below", "at"] = Field(..., description="Price vs EMA200")
    rsi_weekly: float = Field(..., description="Weekly RSI")
    breadth_proxy: float = Field(..., description="Breadth proxy estimate")
    filter_recommendation: Literal["favor_long", "favor_short", "neutral"] = Field(..., description="Direction filter")


class LongTermAdvice(BaseModel):
    """Long-term (regime) advice."""
    
    horizon: str = Field(default="long", description="Time horizon")
    regime: Literal["bull", "bear", "neutral"] = Field(..., description="Market regime")
    regime_probability: float = Field(..., description="Regime probability (0-1)")
    volatility_regime: Literal["low", "normal", "high", "crisis"] = Field(..., description="Vol regime")
    regime_change_probability: float = Field(..., description="Probability of regime change")
    recommended_exposure: float = Field(..., description="Recommended exposure (0-1)")


class MultiHorizonAdvice(BaseModel):
    """Complete multi-horizon advice."""
    
    timestamp: datetime = Field(..., description="Advice timestamp")
    symbol: str = Field(..., description="Symbol")
    
    short_term: ShortTermAdvice = Field(..., description="Short-term advice")
    medium_term: MediumTermAdvice = Field(..., description="Medium-term advice")
    long_term: LongTermAdvice = Field(..., description="Long-term advice")
    
    # Consensus
    consensus_direction: int = Field(..., description="Consensus direction across horizons")
    confidence_score: float = Field(..., description="Overall confidence (0-1)")
    
    # Risk recommendations
    recommended_risk_pct: float = Field(..., description="Final recommended risk %")
    recommended_position_size: Literal["small", "normal", "large"] = Field(..., description="Position size rec")


class MarketAdvisor:
    """Multi-horizon market advisor."""
    
    def __init__(
        self,
        default_risk_pct: float = 0.02,
        volatility_adjustment: bool = True,
        regime_adjustment: bool = True
    ):
        """Initialize advisor.
        
        Args:
            default_risk_pct: Default risk percentage
            volatility_adjustment: Adjust risk based on volatility
            regime_adjustment: Adjust risk based on regime
        """
        self.default_risk_pct = default_risk_pct
        self.volatility_adjustment = volatility_adjustment
        self.regime_adjustment = regime_adjustment
    
    def get_advice(
        self,
        df_intraday: pd.DataFrame,
        df_daily: Optional[pd.DataFrame] = None,
        current_signal: int = 0,
        signal_strength: float = 0.0,
        symbol: str = "UNKNOWN"
    ) -> MultiHorizonAdvice:
        """Get complete multi-horizon advice.
        
        Args:
            df_intraday: Intraday DataFrame (1h or 15m)
            df_daily: Daily DataFrame (optional, for medium/long-term)
            current_signal: Current intraday signal
            signal_strength: Signal strength
            symbol: Trading symbol
            
        Returns:
            MultiHorizonAdvice with all horizons
        """
        # Short-term advice
        short = self._analyze_short_term(
            df_intraday, current_signal, signal_strength
        )
        
        # Medium-term advice
        if df_daily is not None and len(df_daily) >= 200:
            medium = self._analyze_medium_term(df_daily)
        else:
            # Use intraday as proxy
            medium = self._analyze_medium_term_from_intraday(df_intraday)
        
        # Long-term advice
        if df_daily is not None and len(df_daily) >= 100:
            long = self._analyze_long_term(df_daily)
        else:
            # Use intraday as proxy
            long = self._analyze_long_term_from_intraday(df_intraday)
        
        # Calculate consensus
        consensus = self._calculate_consensus(short, medium, long)
        confidence = self._calculate_confidence(short, medium, long)
        
        # Risk recommendation
        recommended_risk = self._calculate_risk_recommendation(
            short, medium, long
        )
        
        # Position size recommendation
        if recommended_risk < 0.015:
            position_size_rec = "small"
        elif recommended_risk > 0.03:
            position_size_rec = "large"
        else:
            position_size_rec = "normal"
        
        return MultiHorizonAdvice(
            timestamp=datetime.now(),
            symbol=symbol,
            short_term=short,
            medium_term=medium,
            long_term=long,
            consensus_direction=consensus,
            confidence_score=confidence,
            recommended_risk_pct=recommended_risk,
            recommended_position_size=position_size_rec
        )
    
    def _analyze_short_term(
        self,
        df: pd.DataFrame,
        current_signal: int,
        signal_strength: float
    ) -> ShortTermAdvice:
        """Analyze short-term (intraday).
        
        Args:
            df: Intraday DataFrame
            current_signal: Current signal
            signal_strength: Signal strength
            
        Returns:
            ShortTermAdvice
        """
        # Volatility state
        rel_vol = relative_volatility(df['close'], short_period=10, long_period=50)
        current_rel_vol = float(rel_vol.iloc[-1]) if not pd.isna(rel_vol.iloc[-1]) else 1.0
        
        if current_rel_vol > 1.3:
            vol_state = "high"
            risk_adjustment = 0.5  # Reduce risk
        elif current_rel_vol < 0.7:
            vol_state = "low"
            risk_adjustment = 1.2  # Can increase risk slightly
        else:
            vol_state = "normal"
            risk_adjustment = 1.0
        
        # Entry timing
        if abs(signal_strength) > 0.7:
            entry_timing = "immediate"
        elif abs(signal_strength) > 0.3:
            entry_timing = "pullback"
        else:
            entry_timing = "wait"
        
        # Calculate recommended risk
        base_risk = self.default_risk_pct
        recommended_risk = base_risk * risk_adjustment if self.volatility_adjustment else base_risk
        recommended_risk = min(recommended_risk, 0.05)  # Cap at 5%
        
        return ShortTermAdvice(
            signal=current_signal,
            strength=signal_strength,
            entry_timing=entry_timing,
            volatility_state=vol_state,
            recommended_risk_pct=recommended_risk
        )
    
    def _analyze_medium_term(self, df_daily: pd.DataFrame) -> MediumTermAdvice:
        """Analyze medium-term (weekly).
        
        Args:
            df_daily: Daily DataFrame
            
        Returns:
            MediumTermAdvice
        """
        # Calculate EMA 200
        ema_200 = ema(df_daily['close'], period=200)
        current_price = float(df_daily['close'].iloc[-1])
        current_ema200 = float(ema_200.iloc[-1]) if not pd.isna(ema_200.iloc[-1]) else current_price
        
        # Price vs EMA200
        if current_price > current_ema200 * 1.01:
            ema_position = "above"
            trend_dir = 1
        elif current_price < current_ema200 * 0.99:
            ema_position = "below"
            trend_dir = -1
        else:
            ema_position = "at"
            trend_dir = 0
        
        # Calculate weekly RSI (approximate from daily)
        rsi_val = rsi(df_daily['close'], period=14)
        rsi_weekly = float(rsi_val.iloc[-1]) if not pd.isna(rsi_val.iloc[-1]) else 50.0
        
        # Trend strength
        trend_str = trend_strength(df_daily['close'], period=50)
        current_trend_strength = float(trend_str.iloc[-1]) if not pd.isna(trend_str.iloc[-1]) else 0.5
        
        # Breadth proxy (using price vs MA as proxy)
        above_ma_pct = (df_daily['close'].iloc[-20:] > ema_200.iloc[-20:]).mean()
        breadth_proxy = float(above_ma_pct)
        
        # Filter recommendation
        if trend_dir == 1 and current_trend_strength > 0.6:
            filter_rec = "favor_long"
        elif trend_dir == -1 and current_trend_strength > 0.6:
            filter_rec = "favor_short"
        else:
            filter_rec = "neutral"
        
        return MediumTermAdvice(
            trend_direction=trend_dir,
            trend_strength=current_trend_strength,
            ema200_position=ema_position,
            rsi_weekly=rsi_weekly,
            breadth_proxy=breadth_proxy,
            filter_recommendation=filter_rec
        )
    
    def _analyze_medium_term_from_intraday(self, df: pd.DataFrame) -> MediumTermAdvice:
        """Analyze medium-term using intraday data as proxy.
        
        Args:
            df: Intraday DataFrame
            
        Returns:
            MediumTermAdvice (approximated)
        """
        # Use longer periods on intraday data
        ema_long = ema(df['close'], period=min(200, len(df) // 2))
        current_price = float(df['close'].iloc[-1])
        current_ema = float(ema_long.iloc[-1]) if not pd.isna(ema_long.iloc[-1]) else current_price
        
        if current_price > current_ema:
            ema_position = "above"
            trend_dir = 1
        elif current_price < current_ema:
            ema_position = "below"
            trend_dir = -1
        else:
            ema_position = "at"
            trend_dir = 0
        
        # Approximate RSI weekly
        rsi_val = rsi(df['close'], period=14)
        rsi_weekly = float(rsi_val.iloc[-1]) if not pd.isna(rsi_val.iloc[-1]) else 50.0
        
        # Trend strength
        trend_str = trend_strength(df['close'], period=min(50, len(df) // 4))
        current_trend_strength = float(trend_str.iloc[-1]) if not pd.isna(trend_str.iloc[-1]) else 0.5
        
        return MediumTermAdvice(
            trend_direction=trend_dir,
            trend_strength=current_trend_strength,
            ema200_position=ema_position,
            rsi_weekly=rsi_weekly,
            breadth_proxy=0.5,  # Neutral proxy
            filter_recommendation="neutral"
        )
    
    def _analyze_long_term(self, df_daily: pd.DataFrame) -> LongTermAdvice:
        """Analyze long-term (regime).
        
        Args:
            df_daily: Daily DataFrame
            
        Returns:
            LongTermAdvice
        """
        # Calculate returns
        returns = df_daily['close'].pct_change()
        
        # Rolling statistics for regime detection
        rolling_mean = returns.rolling(window=60).mean()
        rolling_vol = returns.rolling(window=60).std()
        
        current_mean = float(rolling_mean.iloc[-1]) if not pd.isna(rolling_mean.iloc[-1]) else 0
        current_vol = float(rolling_vol.iloc[-1]) if not pd.isna(rolling_vol.iloc[-1]) else 0.02
        
        # Regime classification
        if current_mean > 0.001 and current_vol < 0.025:
            regime = "bull"
            regime_prob = 0.7
            exposure = 0.8
        elif current_mean < -0.001 and current_vol > 0.03:
            regime = "bear"
            regime_prob = 0.7
            exposure = 0.5
        else:
            regime = "neutral"
            regime_prob = 0.5
            exposure = 0.6
        
        # Volatility regime
        if current_vol > 0.04:
            vol_regime = "crisis"
        elif current_vol > 0.03:
            vol_regime = "high"
        elif current_vol < 0.015:
            vol_regime = "low"
        else:
            vol_regime = "normal"
        
        # Regime change probability (using trend strength as proxy)
        trend_str = trend_strength(df_daily['close'], period=30)
        regime_stability = float(trend_str.iloc[-1]) if not pd.isna(trend_str.iloc[-1]) else 0.5
        regime_change_prob = 1 - regime_stability
        
        return LongTermAdvice(
            regime=regime,
            regime_probability=regime_prob,
            volatility_regime=vol_regime,
            regime_change_probability=regime_change_prob,
            recommended_exposure=exposure
        )
    
    def _analyze_long_term_from_intraday(self, df: pd.DataFrame) -> LongTermAdvice:
        """Analyze long-term using intraday data as proxy.
        
        Args:
            df: Intraday DataFrame
            
        Returns:
            LongTermAdvice (approximated)
        """
        # Use intraday data with longer periods
        returns = df['close'].pct_change()
        
        mean_return = float(returns.mean())
        vol_return = float(returns.std())
        
        # Simple regime classification
        if mean_return > 0:
            regime = "bull"
        elif mean_return < 0:
            regime = "bear"
        else:
            regime = "neutral"
        
        # Volatility regime (annualized)
        ann_vol = vol_return * np.sqrt(252 * 24)  # Hourly to annual
        
        if ann_vol > 1.0:
            vol_regime = "crisis"
        elif ann_vol > 0.6:
            vol_regime = "high"
        elif ann_vol < 0.3:
            vol_regime = "low"
        else:
            vol_regime = "normal"
        
        return LongTermAdvice(
            regime=regime,
            regime_probability=0.5,
            volatility_regime=vol_regime,
            regime_change_probability=0.3,
            recommended_exposure=0.6
        )
    
    def _calculate_consensus(
        self,
        short: ShortTermAdvice,
        medium: MediumTermAdvice,
        long: LongTermAdvice
    ) -> int:
        """Calculate consensus direction across horizons.
        
        Args:
            short: Short-term advice
            medium: Medium-term advice
            long: Long-term advice
            
        Returns:
            Consensus direction: 1, -1, or 0
        """
        # Weight votes
        votes = {
            'short': short.signal,
            'medium': medium.trend_direction,
            'long': 1 if long.regime == "bull" else (-1 if long.regime == "bear" else 0)
        }
        
        # Simple majority
        vote_sum = sum(votes.values())
        
        if vote_sum >= 2:
            return 1
        elif vote_sum <= -2:
            return -1
        else:
            return 0
    
    def _calculate_confidence(
        self,
        short: ShortTermAdvice,
        medium: MediumTermAdvice,
        long: LongTermAdvice
    ) -> float:
        """Calculate overall confidence score.
        
        Args:
            short: Short-term advice
            medium: Medium-term advice
            long: Long-term advice
            
        Returns:
            Confidence score (0-1)
        """
        # Combine strengths
        short_conf = abs(short.strength) if not np.isnan(short.strength) else 0
        medium_conf = medium.trend_strength
        long_conf = long.regime_probability
        
        # Weighted average
        confidence = (short_conf * 0.5 + medium_conf * 0.3 + long_conf * 0.2)
        
        return float(np.clip(confidence, 0, 1))
    
    def _calculate_risk_recommendation(
        self,
        short: ShortTermAdvice,
        medium: MediumTermAdvice,
        long: LongTermAdvice
    ) -> float:
        """Calculate recommended risk percentage.
        
        Args:
            short: Short-term advice
            medium: Medium-term advice
            long: Long-term advice
            
        Returns:
            Recommended risk percentage
        """
        base_risk = self.default_risk_pct
        
        # Volatility adjustment
        if self.volatility_adjustment:
            if short.volatility_state == "high":
                base_risk *= 0.5
            elif short.volatility_state == "low":
                base_risk *= 1.2
        
        # Regime adjustment
        if self.regime_adjustment:
            if long.volatility_regime == "crisis":
                base_risk *= 0.3
            elif long.volatility_regime == "high":
                base_risk *= 0.7
        
        # Exposure adjustment
        base_risk *= long.recommended_exposure
        
        # Cap at reasonable limits
        return float(np.clip(base_risk, 0.005, 0.05))


def integrate_backtest_metrics(
    advisor: MarketAdvisor,
    recent_performance: Dict[str, float],
    lookback_period: int = 30
) -> float:
    """Integrate recent backtest metrics into risk recommendation.
    
    Args:
        advisor: MarketAdvisor instance
        recent_performance: Dict with recent performance metrics
        lookback_period: Rolling period for metrics
        
    Returns:
        Adjusted risk percentage
    """
    base_risk = advisor.default_risk_pct
    
    # Adjust based on recent Sharpe
    sharpe = recent_performance.get('sharpe', 0)
    if sharpe > 1.5:
        risk_multiplier = 1.3
    elif sharpe > 1.0:
        risk_multiplier = 1.1
    elif sharpe < 0:
        risk_multiplier = 0.5
    else:
        risk_multiplier = 1.0
    
    # Adjust based on recent drawdown
    max_dd = abs(recent_performance.get('max_dd', 0))
    if max_dd > 0.15:
        risk_multiplier *= 0.7
    elif max_dd < 0.05:
        risk_multiplier *= 1.1
    
    # Adjust based on win rate
    win_rate = recent_performance.get('win_rate', 0.5)
    if win_rate > 0.6:
        risk_multiplier *= 1.1
    elif win_rate < 0.4:
        risk_multiplier *= 0.8
    
    adjusted_risk = base_risk * risk_multiplier
    
    # Cap at limits
    return float(np.clip(adjusted_risk, 0.005, 0.05))

