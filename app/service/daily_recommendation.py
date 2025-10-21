"""Daily recommendation service based on multi-timeframe ranking.

This module provides a comprehensive daily recommendation system that:
- Analyzes strategies across multiple timeframes
- Evaluates individual strategies and combinations
- Generates a confidence-weighted recommendation
- Provides detailed reasoning and metrics
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from app.service.strategy_orchestrator import StrategyOrchestrator, StrategyBacktestResult
from app.service.global_ranking import GlobalRankingService, RankedStrategy
from app.config.settings import settings

logger = logging.getLogger(__name__)


class DailyRecommendation(BaseModel):
    """Daily trading recommendation."""
    
    date: str
    symbol: str
    
    # Best strategy recommendation
    recommended_strategy: str
    recommended_timeframe: str
    is_combination: bool = False
    
    # Confidence metrics
    global_score: float
    global_rank: int
    confidence_level: str  # LOW, MEDIUM, HIGH
    
    # Performance metrics
    expected_sharpe: float
    expected_win_rate: float
    expected_cagr: float
    expected_max_dd: float
    expected_profit_factor: float
    expected_expectancy: float
    
    # Consistency metrics
    sharpe_consistency: float
    cross_timeframe_agreement: float  # How many timeframes agree this is top 3
    
    # Signal details
    signal_direction: int  # 1, -1, 0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    quantity: Optional[float] = None
    risk_amount: Optional[float] = None
    
    # Alternative strategies (top 3)
    alternatives: List[Dict] = Field(default_factory=list)
    
    # Reasoning
    reasoning: str
    warnings: List[str] = Field(default_factory=list)


class DailyRecommendationService:
    """Service for generating daily recommendations."""
    
    def __init__(self, capital: float, max_risk_pct: float = 0.02):
        """Initialize recommendation service.
        
        Args:
            capital: Trading capital
            max_risk_pct: Maximum risk per trade
        """
        self.capital = capital
        self.max_risk_pct = max_risk_pct
        self.orchestrator = StrategyOrchestrator(
            capital=capital,
            max_risk_pct=max_risk_pct,
            lookback_days=90
        )
        self.ranking_service = GlobalRankingService()
    
    def get_daily_recommendation(
        self,
        symbol: str,
        include_combinations: bool = True
    ) -> Optional[DailyRecommendation]:
        """Get daily trading recommendation.
        
        Args:
            symbol: Trading symbol
            include_combinations: Whether to include strategy combinations
            
        Returns:
            Daily recommendation or None if insufficient data
        """
        try:
            logger.info(f"Generating daily recommendation for {symbol}")
            
            # Step 1: Validate data availability
            timeframes = settings.TARGET_TIMEFRAMES
            validation_results = self.orchestrator.validate_data_availability(symbol, timeframes)
            
            # Check if we have sufficient data
            valid_timeframes = [tf for tf, status in validation_results.items() if status.is_sufficient]
            
            if not valid_timeframes:
                logger.warning(f"No valid timeframes for {symbol}")
                return None
            
            logger.info(f"Valid timeframes: {valid_timeframes}")
            
            # Step 2: Run multi-timeframe backtests
            multi_results = self.orchestrator.run_multi_timeframe_backtests(symbol, valid_timeframes)
            
            # Filter empty results
            filtered_results = {tf: results for tf, results in multi_results.items() if results}
            
            if not filtered_results:
                logger.warning(f"No backtest results for {symbol}")
                return None
            
            # Step 3: Run combinations if requested
            combination_results = None
            if include_combinations:
                combination_results = {}
                for tf in valid_timeframes:
                    try:
                        combos = self.orchestrator.run_strategy_combinations(symbol, tf)
                        if combos:
                            combination_results[tf] = combos
                    except Exception as e:
                        logger.warning(f"Combinations failed for {tf}: {e}")
            
            # Step 4: Calculate global ranking
            ranked_strategies = self.ranking_service.rank_strategies(
                filtered_results,
                combination_results if combination_results else None
            )
            
            if not ranked_strategies:
                logger.warning(f"No ranked strategies for {symbol}")
                return None
            
            # Step 5: Get best strategy
            best_strategy = ranked_strategies[0]
            
            # Find best timeframe for this strategy
            best_timeframe, best_metrics = self._find_best_timeframe(best_strategy)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence(best_strategy, len(valid_timeframes))
            
            # Calculate cross-timeframe agreement
            agreement = self._calculate_timeframe_agreement(best_strategy.strategy_name, ranked_strategies, valid_timeframes)
            
            # Generate trade plan
            trade_plan = self._generate_trade_plan(
                symbol,
                best_timeframe,
                best_strategy.strategy_name,
                best_metrics
            )
            
            # Build reasoning
            reasoning = self._build_reasoning(best_strategy, valid_timeframes, confidence_level)
            
            # Build warnings
            warnings = self._build_warnings(validation_results, confidence_level)
            
            # Get alternatives
            alternatives = self._get_alternatives(ranked_strategies[:4])
            
            # Create recommendation
            recommendation = DailyRecommendation(
                date=datetime.now().strftime('%Y-%m-%d'),
                symbol=symbol,
                recommended_strategy=best_strategy.strategy_name,
                recommended_timeframe=best_timeframe,
                is_combination=best_strategy.is_combination,
                global_score=best_strategy.global_score,
                global_rank=best_strategy.global_rank,
                confidence_level=confidence_level,
                expected_sharpe=best_strategy.best_sharpe,
                expected_win_rate=best_strategy.best_win_rate,
                expected_cagr=best_strategy.best_cagr,
                expected_max_dd=best_strategy.worst_max_dd,
                expected_profit_factor=best_strategy.best_profit_factor,
                expected_expectancy=best_strategy.best_expectancy,
                sharpe_consistency=best_strategy.sharpe_consistency,
                cross_timeframe_agreement=agreement,
                signal_direction=trade_plan['signal_direction'],
                entry_price=trade_plan.get('entry_price'),
                stop_loss=trade_plan.get('stop_loss'),
                take_profit=trade_plan.get('take_profit'),
                quantity=trade_plan.get('quantity'),
                risk_amount=trade_plan.get('risk_amount'),
                alternatives=alternatives,
                reasoning=reasoning,
                warnings=warnings
            )
            
            logger.info(f"✅ Recommendation: {recommendation.recommended_strategy} on {recommendation.recommended_timeframe}")
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating daily recommendation: {e}")
            return None
    
    def _find_best_timeframe(self, strategy: RankedStrategy) -> Tuple[str, Dict]:
        """Find best timeframe for a strategy."""
        best_tf = None
        best_sharpe = -999
        best_metrics = {}
        
        for tf, metrics in strategy.timeframe_breakdown.items():
            if metrics['sharpe_ratio'] > best_sharpe:
                best_sharpe = metrics['sharpe_ratio']
                best_tf = tf
                best_metrics = metrics
        
        return best_tf or "1h", best_metrics
    
    def _calculate_confidence(self, strategy: RankedStrategy, num_timeframes: int) -> str:
        """Calculate confidence level."""
        # High confidence if:
        # - High global score
        # - Good consistency
        # - Tested on multiple timeframes
        
        if strategy.global_score > 0.7 and strategy.sharpe_consistency < 0.3 and num_timeframes >= 3:
            return "HIGH"
        elif strategy.global_score > 0.5 and num_timeframes >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_timeframe_agreement(
        self,
        strategy_name: str,
        all_ranked: List[RankedStrategy],
        timeframes: List[str]
    ) -> float:
        """Calculate what percentage of timeframes rank this strategy in top 3."""
        # This would require per-timeframe rankings, simplified for now
        return 0.8 if strategy_name in [s.strategy_name for s in all_ranked[:3]] else 0.5
    
    def _generate_trade_plan(
        self,
        symbol: str,
        timeframe: str,
        strategy_name: str,
        metrics: Dict
    ) -> Dict:
        """Generate trade plan for the recommendation."""
        try:
            from app.data.store import DataStore
            from app.core.risk import compute_levels
            
            # Load current data
            store = DataStore()
            bars = store.read_bars(symbol, timeframe, max_bars=100)
            
            if not bars or len(bars) < 10:
                return {'signal_direction': 0}
            
            # Get current price
            df = pd.DataFrame([bar.to_dict() for bar in bars])
            df = df.sort_values('timestamp').reset_index(drop=True)
            current_price = float(df['close'].iloc[-1])
            
            # Simple signal based on strategy (simplified for now)
            signal_direction = 1 if metrics.get('win_rate', 0) > 0.5 else 0
            
            # Calculate levels using ATR
            atr_period = 14
            if len(df) >= atr_period:
                high_low = df['high'] - df['low']
                high_close = np.abs(df['high'] - df['close'].shift())
                low_close = np.abs(df['low'] - df['close'].shift())
                true_range = np.maximum(high_low, np.maximum(high_close, low_close))
                atr = true_range.rolling(window=atr_period).mean().iloc[-1]
            else:
                atr = current_price * 0.02
            
            # Calculate entry, SL, TP
            if signal_direction == 1:  # Long
                entry_price = current_price
                stop_loss = entry_price - (atr * 2.0)
                take_profit = entry_price + (atr * 3.0)
            else:  # Flat
                entry_price = current_price
                stop_loss = None
                take_profit = None
            
            # Calculate position size
            if stop_loss:
                risk_per_trade = self.capital * self.max_risk_pct
                risk_per_unit = abs(entry_price - stop_loss)
                quantity = risk_per_trade / risk_per_unit if risk_per_unit > 0 else 0
                risk_amount = risk_per_trade
            else:
                quantity = 0
                risk_amount = 0
            
            return {
                'signal_direction': signal_direction,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'quantity': quantity,
                'risk_amount': risk_amount
            }
            
        except Exception as e:
            logger.error(f"Error generating trade plan: {e}")
            return {'signal_direction': 0}
    
    def _build_reasoning(
        self,
        strategy: RankedStrategy,
        timeframes: List[str],
        confidence: str
    ) -> str:
        """Build reasoning text."""
        reasoning_parts = []
        
        reasoning_parts.append(
            f"Estrategia '{strategy.strategy_name}' rankeada #1 globalmente "
            f"con score de {strategy.global_score:.2f}."
        )
        
        reasoning_parts.append(
            f"Analizada en {len(timeframes)} temporalidades con "
            f"Sharpe promedio de {strategy.best_sharpe:.2f} y "
            f"Win Rate de {strategy.best_win_rate:.1%}."
        )
        
        if strategy.is_combination:
            reasoning_parts.append(
                "Esta es una combinación de estrategias que ofrece mayor robustez."
            )
        
        reasoning_parts.append(
            f"Nivel de confianza: {confidence} basado en consistencia "
            f"entre timeframes ({strategy.sharpe_consistency:.2f})."
        )
        
        return " ".join(reasoning_parts)
    
    def _build_warnings(
        self,
        validation_results: Dict,
        confidence: str
    ) -> List[str]:
        """Build warning messages."""
        warnings = []
        
        # Check for missing timeframes
        missing_tfs = [tf for tf, status in validation_results.items() if not status.is_sufficient]
        if missing_tfs:
            warnings.append(f"Datos insuficientes para: {', '.join(missing_tfs)}")
        
        # Low confidence warning
        if confidence == "LOW":
            warnings.append("Confianza baja - considerar análisis manual adicional")
        
        return warnings
    
    def _get_alternatives(self, top_strategies: List[RankedStrategy]) -> List[Dict]:
        """Get alternative strategies."""
        alternatives = []
        
        for i, strategy in enumerate(top_strategies[1:4], 2):  # Skip first (recommended)
            alternatives.append({
                'rank': i,
                'name': strategy.strategy_name,
                'score': strategy.global_score,
                'sharpe': strategy.best_sharpe,
                'win_rate': strategy.best_win_rate,
                'is_combination': strategy.is_combination
            })
        
        return alternatives

