"""Recommendation contract for One Market platform.

This module defines the core recommendation data structures
and contracts for the trading system.
"""
from datetime import datetime
from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class PlanDirection(str, Enum):
    """Trading direction enum."""
    LONG = "LONG"
    SHORT = "SHORT" 
    HOLD = "HOLD"


class Recommendation(BaseModel):
    """Trading recommendation with complete plan."""
    
    date: str = Field(..., description="Recommendation date (YYYY-MM-DD)")
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Recommended timeframe")
    direction: PlanDirection = Field(..., description="Trading direction")
    
    # Entry conditions
    entry_band: Optional[List[float]] = Field(None, description="Entry price range [min, max]")
    entry_price: Optional[float] = Field(None, description="Specific entry price")
    
    # Risk management
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    
    # Position sizing
    quantity: Optional[float] = Field(None, description="Position quantity")
    risk_amount: Optional[float] = Field(None, description="Risk amount in USD")
    risk_percentage: Optional[float] = Field(None, description="Risk as percentage of capital")
    
    # Analysis
    rationale: str = Field(..., description="Reasoning for recommendation")
    confidence: int = Field(..., ge=0, le=100, description="Confidence level (0-100)")
    
    # Strategy information (new fields)
    strategy_name: Optional[str] = Field(None, description="Best strategy name")
    strategy_score: Optional[float] = Field(None, description="Strategy composite score")
    sharpe_ratio: Optional[float] = Field(None, description="Strategy Sharpe ratio")
    win_rate: Optional[float] = Field(None, description="Strategy win rate")
    max_drawdown: Optional[float] = Field(None, description="Strategy max drawdown")
    
    # Multi-timeframe analysis (new fields)
    mtf_analysis: Optional[Dict[str, Any]] = Field(None, description="Multi-timeframe analysis details")
    ranking_weights: Optional[Dict[str, float]] = Field(None, description="Strategy ranking weights")
    
    # Data integrity
    dataset_hash: str = Field(..., description="Hash of dataset used")
    params_hash: str = Field(..., description="Hash of parameters used")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Recommendation expiration")
    
    @validator('entry_band')
    def validate_entry_band(cls, v):
        """Validate entry band format."""
        if v is not None:
            if len(v) != 2:
                raise ValueError('entry_band must have exactly 2 values [min, max]')
            if v[0] >= v[1]:
                raise ValueError('entry_band min must be < max')
        return v
    
    @validator('stop_loss')
    def validate_stop_loss(cls, v, values):
        """Validate stop loss relative to direction."""
        if v is not None and 'direction' in values and 'entry_price' in values:
            direction = values['direction']
            entry_price = values['entry_price']
            
            if direction == PlanDirection.LONG and v >= entry_price:
                raise ValueError('Stop loss for LONG must be < entry price')
            elif direction == PlanDirection.SHORT and v <= entry_price:
                raise ValueError('Stop loss for SHORT must be > entry price')
        return v
    
    @validator('take_profit')
    def validate_take_profit(cls, v, values):
        """Validate take profit relative to direction."""
        if v is not None and 'direction' in values and 'entry_price' in values:
            direction = values['direction']
            entry_price = values['entry_price']
            
            if direction == PlanDirection.LONG and v <= entry_price:
                raise ValueError('Take profit for LONG must be > entry price')
            elif direction == PlanDirection.SHORT and v >= entry_price:
                raise ValueError('Take profit for SHORT must be < entry price')
        return v
    
    def is_valid(self) -> bool:
        """Check if recommendation is valid and actionable."""
        if self.direction == PlanDirection.HOLD:
            return True
        
        # For LONG/SHORT, we need entry price and risk management
        required_fields = [self.entry_price, self.stop_loss, self.take_profit]
        return all(field is not None for field in required_fields)
    
    def get_risk_reward_ratio(self) -> Optional[float]:
        """Calculate risk/reward ratio."""
        if not self.is_valid() or self.direction == PlanDirection.HOLD:
            return None
        
        entry = self.entry_price
        sl = self.stop_loss
        tp = self.take_profit
        
        if entry is None or sl is None or tp is None:
            return None
        
        if self.direction == PlanDirection.LONG:
            risk = entry - sl
            reward = tp - entry
        else:  # SHORT
            risk = sl - entry
            reward = entry - tp
        
        if risk <= 0:
            return None
        
        return reward / risk


class RecommendationRequest(BaseModel):
    """Request for generating recommendation."""
    
    symbol: str = Field(..., description="Trading symbol")
    date: str = Field(..., description="Date for recommendation (YYYY-MM-DD)")
    capital: float = Field(default=10000.0, description="Available capital")
    risk_percentage: float = Field(default=2.0, description="Risk percentage per trade")
    timeframes: List[str] = Field(default=["15m", "1h", "4h", "1d"], description="Timeframes to analyze")


class RecommendationResponse(BaseModel):
    """Response for recommendation request."""
    
    success: bool = Field(..., description="Request success status")
    recommendation: Optional[Recommendation] = Field(None, description="Generated recommendation")
    message: str = Field(..., description="Status message")
    data_quality: Dict[str, Any] = Field(default_factory=dict, description="Data quality metrics")
    analysis_time: float = Field(default=0.0, description="Analysis time in seconds")


def make_recommendation(symbol: str, date: str) -> Recommendation:
    """Generate trading recommendation (stub implementation).
    
    Args:
        symbol: Trading symbol
        date: Date for recommendation
        
    Returns:
        Recommendation object
    """
    # This is a stub implementation
    # TODO: Implement actual recommendation logic
    
    return Recommendation(
        date=date,
        symbol=symbol,
        timeframe="1h",
        direction=PlanDirection.HOLD,
        rationale="Recommendation system not yet implemented",
        confidence=0,
        dataset_hash="stub_hash",
        params_hash="stub_params_hash"
    )
