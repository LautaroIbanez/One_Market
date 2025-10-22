"""Recommendation weights calculation for One Market platform.

This module provides algorithms for calculating strategy weights based on
performance metrics and ranking data.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class WeightConfig(BaseModel):
    """Configuration for weight calculation."""
    
    method: str = Field(default="softmax", description="Weight calculation method")
    temperature: float = Field(default=1.0, description="Temperature for softmax")
    min_weight: float = Field(default=0.01, description="Minimum weight threshold")
    max_weight: float = Field(default=0.5, description="Maximum weight threshold")
    normalize: bool = Field(default=True, description="Normalize weights to sum to 1")


class StrategyWeight(BaseModel):
    """Strategy weight result."""
    
    strategy_name: str
    timeframe: str
    weight: float
    score: float
    metrics: Dict[str, float]
    rationale: str


class RecommendationWeights(BaseModel):
    """Complete recommendation weights."""
    
    timestamp: datetime
    symbol: str
    total_weight: float
    strategy_weights: List[StrategyWeight]
    direction_weights: Dict[str, float]  # LONG, SHORT, HOLD
    confidence: float
    rationale: str


class RecommendationWeightCalculator:
    """Calculator for recommendation weights based on strategy performance."""
    
    def __init__(self, config: Optional[WeightConfig] = None):
        """Initialize weight calculator.
        
        Args:
            config: Configuration for weight calculation
        """
        self.config = config or WeightConfig()
        logger.info(f"RecommendationWeightCalculator initialized with method: {self.config.method}")
    
    def calculate_weights(
        self,
        rankings: List[Dict[str, Any]],
        symbol: str,
        date: str
    ) -> RecommendationWeights:
        """Calculate recommendation weights from rankings.
        
        Args:
            rankings: List of strategy rankings
            symbol: Trading symbol
            date: Date for weights
            
        Returns:
            RecommendationWeights with calculated weights
        """
        try:
            logger.info(f"Calculating weights for {symbol} on {date}")
            
            if not rankings:
                return self._create_empty_weights(symbol, date)
            
            # Calculate strategy weights
            strategy_weights = self._calculate_strategy_weights(rankings)
            
            # Calculate direction weights
            direction_weights = self._calculate_direction_weights(strategy_weights)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(strategy_weights, direction_weights)
            
            # Create rationale
            rationale = self._create_rationale(strategy_weights, direction_weights, confidence)
            
            return RecommendationWeights(
                timestamp=datetime.now(),
                symbol=symbol,
                total_weight=sum(sw.weight for sw in strategy_weights),
                strategy_weights=strategy_weights,
                direction_weights=direction_weights,
                confidence=confidence,
                rationale=rationale
            )
            
        except Exception as e:
            logger.error(f"Error calculating weights: {e}")
            return self._create_empty_weights(symbol, date)
    
    def _calculate_strategy_weights(self, rankings: List[Dict[str, Any]]) -> List[StrategyWeight]:
        """Calculate individual strategy weights."""
        if not rankings:
            return []
        
        # Extract scores and metrics
        scores = []
        strategies = []
        
        for ranking in rankings:
            score = ranking.get('composite_score', 0.0)
            scores.append(score)
            strategies.append(ranking)
        
        if not scores:
            return []
        
        # Calculate weights based on method
        if self.config.method == "softmax":
            weights = self._softmax_weights(scores)
        elif self.config.method == "linear":
            weights = self._linear_weights(scores)
        elif self.config.method == "rank_based":
            weights = self._rank_based_weights(scores)
        else:
            weights = self._softmax_weights(scores)
        
        # Apply constraints
        weights = self._apply_weight_constraints(weights)
        
        # Create strategy weight objects
        strategy_weights = []
        for i, (ranking, weight) in enumerate(zip(strategies, weights)):
            if weight > self.config.min_weight:
                strategy_weight = StrategyWeight(
                    strategy_name=ranking.get('strategy_name', f'Strategy_{i}'),
                    timeframe=ranking.get('timeframe', '1h'),
                    weight=weight,
                    score=ranking.get('composite_score', 0.0),
                    metrics={
                        'sharpe_ratio': ranking.get('sharpe_ratio', 0.0),
                        'win_rate': ranking.get('win_rate', 0.0),
                        'profit_factor': ranking.get('profit_factor', 0.0),
                        'max_drawdown': ranking.get('max_drawdown', 0.0),
                        'cagr': ranking.get('cagr', 0.0),
                        'total_trades': ranking.get('total_trades', 0)
                    },
                    rationale=f"Weight {weight:.3f} based on score {ranking.get('composite_score', 0.0):.3f}"
                )
                strategy_weights.append(strategy_weight)
        
        return strategy_weights
    
    def _softmax_weights(self, scores: List[float]) -> List[float]:
        """Calculate softmax weights."""
        if not scores:
            return []
        
        # Apply temperature
        scaled_scores = [score / self.config.temperature for score in scores]
        
        # Calculate softmax
        exp_scores = [np.exp(score) for score in scaled_scores]
        sum_exp = sum(exp_scores)
        
        if sum_exp == 0:
            return [1.0 / len(scores)] * len(scores)
        
        weights = [exp_score / sum_exp for exp_score in exp_scores]
        
        return weights
    
    def _linear_weights(self, scores: List[float]) -> List[float]:
        """Calculate linear normalized weights."""
        if not scores:
            return []
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [1.0 / len(scores)] * len(scores)
        
        # Normalize to 0-1
        normalized = [(score - min_score) / (max_score - min_score) for score in scores]
        
        # Normalize to sum to 1
        total = sum(normalized)
        if total == 0:
            return [1.0 / len(scores)] * len(scores)
        
        weights = [n / total for n in normalized]
        return weights
    
    def _rank_based_weights(self, scores: List[float]) -> List[float]:
        """Calculate rank-based weights (higher rank = higher weight)."""
        if not scores:
            return []
        
        # Sort by score and assign ranks
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        
        # Assign weights based on rank (exponential decay)
        weights = [0.0] * len(scores)
        for rank, idx in enumerate(sorted_indices):
            weight = np.exp(-rank * 0.5)  # Exponential decay
            weights[idx] = weight
        
        # Normalize
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
        
        return weights
    
    def _apply_weight_constraints(self, weights: List[float]) -> List[float]:
        """Apply weight constraints (min/max thresholds)."""
        if not weights:
            return []
        
        # Apply min/max constraints
        constrained_weights = []
        for weight in weights:
            constrained_weight = max(self.config.min_weight, 
                                   min(self.config.max_weight, weight))
            constrained_weights.append(constrained_weight)
        
        # Renormalize if needed
        if self.config.normalize:
            total = sum(constrained_weights)
            if total > 0:
                constrained_weights = [w / total for w in constrained_weights]
        
        return constrained_weights
    
    def _calculate_direction_weights(
        self, 
        strategy_weights: List[StrategyWeight]
    ) -> Dict[str, float]:
        """Calculate direction weights (LONG/SHORT/HOLD)."""
        if not strategy_weights:
            return {"LONG": 0.0, "SHORT": 0.0, "HOLD": 1.0}
        
        # For now, use equal distribution
        # TODO: Implement direction-based weighting based on strategy signals
        total_weight = sum(sw.weight for sw in strategy_weights)
        
        if total_weight == 0:
            return {"LONG": 0.0, "SHORT": 0.0, "HOLD": 1.0}
        
        # Simple heuristic: top strategies get LONG weight
        top_strategies = sorted(strategy_weights, key=lambda x: x.weight, reverse=True)[:3]
        top_weight = sum(sw.weight for sw in top_strategies)
        
        return {
            "LONG": top_weight * 0.6,  # 60% of top weight goes to LONG
            "SHORT": top_weight * 0.3,  # 30% of top weight goes to SHORT
            "HOLD": 1.0 - top_weight  # Remainder goes to HOLD
        }
    
    def _calculate_confidence(
        self,
        strategy_weights: List[StrategyWeight],
        direction_weights: Dict[str, float]
    ) -> float:
        """Calculate overall confidence."""
        if not strategy_weights:
            return 0.0
        
        # Base confidence on weight concentration
        weights = [sw.weight for sw in strategy_weights]
        max_weight = max(weights) if weights else 0.0
        
        # Higher concentration = higher confidence
        concentration = max_weight / sum(weights) if sum(weights) > 0 else 0.0
        
        # Scale to 0-1
        confidence = min(1.0, concentration * 2.0)
        
        return confidence
    
    def _create_rationale(
        self,
        strategy_weights: List[StrategyWeight],
        direction_weights: Dict[str, float],
        confidence: float
    ) -> str:
        """Create rationale for weights."""
        if not strategy_weights:
            return "No strategies available for weighting"
        
        top_strategy = max(strategy_weights, key=lambda x: x.weight)
        
        rationale = (
            f"Top strategy: {top_strategy.strategy_name} ({top_strategy.timeframe}) "
            f"with weight {top_strategy.weight:.3f} and score {top_strategy.score:.3f}. "
            f"Direction weights: LONG={direction_weights['LONG']:.3f}, "
            f"SHORT={direction_weights['SHORT']:.3f}, HOLD={direction_weights['HOLD']:.3f}. "
            f"Overall confidence: {confidence:.1%}"
        )
        
        return rationale
    
    def _create_empty_weights(self, symbol: str, date: str) -> RecommendationWeights:
        """Create empty weights when no data available."""
        return RecommendationWeights(
            timestamp=datetime.now(),
            symbol=symbol,
            total_weight=0.0,
            strategy_weights=[],
            direction_weights={"LONG": 0.0, "SHORT": 0.0, "HOLD": 1.0},
            confidence=0.0,
            rationale="No ranking data available for weight calculation"
        )
    
    def get_weight_summary(self, weights: RecommendationWeights) -> Dict[str, Any]:
        """Get summary of weights for display."""
        if not weights.strategy_weights:
            return {
                "total_strategies": 0,
                "top_strategy": None,
                "direction_distribution": weights.direction_weights,
                "confidence": weights.confidence
            }
        
        top_strategy = max(weights.strategy_weights, key=lambda x: x.weight)
        
        return {
            "total_strategies": len(weights.strategy_weights),
            "top_strategy": {
                "name": top_strategy.strategy_name,
                "timeframe": top_strategy.timeframe,
                "weight": top_strategy.weight,
                "score": top_strategy.score
            },
            "direction_distribution": weights.direction_weights,
            "confidence": weights.confidence,
            "rationale": weights.rationale
        }
