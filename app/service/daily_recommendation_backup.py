"""Daily recommendation service for One Market platform.

This module provides the core recommendation logic that analyzes
multi-timeframe signals and generates actionable trading recommendations.
"""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
import numpy as np
import logging

from app.data import DataStore, DataFetcher
from app.research.signals import generate_signal, get_strategy_list
from app.service.recommendation_contract import Recommendation, PlanDirection, RecommendationRequest, RecommendationResponse
from app.service.strategy_ranking import StrategyRankingService, StrategyRecommendation
from app.service.recommendation_weights import RecommendationWeightCalculator, WeightConfig
from app.config.settings import settings

logger = logging.getLogger(__name__)


class DailyRecommendationService:
    """Service for generating daily trading recommendations."""
    
    def __init__(self, capital: float = 10000.0, max_risk_pct: float = 2.0):
        """Initialize recommendation service.
        
        Args:
            capital: Available capital
            max_risk_pct: Maximum risk percentage per trade
        """
        self.capital = capital
        self.max_risk_pct = max_risk_pct
        self.store = DataStore()
        self.fetcher = DataFetcher()
        
        # Initialize strategy ranking service
        self.strategy_ranking = StrategyRankingService(
            capital=capital,
            max_risk_pct=max_risk_pct,
            lookback_days=90
        )
        
        # Initialize weight calculator
        self.weight_calculator = RecommendationWeightCalculator(
            config=WeightConfig(
                method="softmax",
                temperature=1.0,
                min_weight=0.01,
                max_weight=0.5,
                normalize=True
            )
        )
        
        # Initialize recommendation database
        self._init_recommendation_db()
        
        logger.info(f"DailyRecommendationService initialized with capital=${capital:,.2f}")
    
    def _init_recommendation_db(self):
        """Initialize SQLite database for recommendations."""
        db_path = self.store.base_path / "recommendations.db"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create recommendations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    rationale TEXT,
                    dataset_hash TEXT,
                    params_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, symbol)
                )
            """)
            
            conn.commit()
    
    def get_daily_recommendation(
        self, 
        symbol: str, 
        date: str,
        timeframes: List[str] = None,
        use_strategy_ranking: bool = True
    ) -> Recommendation:
        """Generate daily recommendation for symbol/date.
        
        Args:
            symbol: Trading symbol
            date: Date in YYYY-MM-DD format
            timeframes: List of timeframes to analyze
            use_strategy_ranking: Whether to use strategy ranking for recommendation
            
        Returns:
            Recommendation object or HOLD with reason
        """
        if timeframes is None:
            timeframes = ["1h", "4h", "1d"]
        
        try:
            logger.info(f"Generating recommendation for {symbol} on {date}")
            
            # Use strategy ranking if enabled
            if use_strategy_ranking:
                return self._get_ranking_based_recommendation(symbol, date, timeframes)
            else:
                return self._get_signal_based_recommendation(symbol, date, timeframes)
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return self._create_hold_recommendation(
                symbol, date, f"Error in recommendation generation: {str(e)}"
            )
    
    def _get_ranking_based_recommendation(
        self, 
        symbol: str, 
        date: str, 
        timeframes: List[str]
    ) -> Recommendation:
        """Generate recommendation based on strategy ranking with weights."""
        try:
            # Get rankings for all timeframes
            all_rankings = []
            for tf in timeframes:
                # Get rankings for this timeframe
                rankings = self._get_timeframe_rankings(symbol, tf, date)
                if rankings:
                    all_rankings.extend(rankings)
            
            if not all_rankings:
                return self._create_hold_recommendation(
                    symbol, date, "No ranking data available"
                )
            
            # Calculate weights based on rankings
            weights = self.weight_calculator.calculate_weights(all_rankings, symbol, date)
            
            if weights.confidence < 0.3:
                return self._create_hold_recommendation(
                    symbol, date, f"Low confidence: {weights.confidence:.2f}"
                )
            
            # Get best strategy from weights
            if not weights.strategy_weights:
                return self._create_hold_recommendation(
                    symbol, date, "No valid strategy weights"
                )
            
            best_strategy_weight = max(weights.strategy_weights, key=lambda x: x.weight)
            
            # Determine direction based on weights
            direction = self._determine_direction_from_weights(weights.direction_weights)
            
            # Create enhanced recommendation with weights
            return self._create_weighted_recommendation(
                symbol, date, best_strategy_weight, weights, direction
            )
            
        except Exception as e:
            logger.error(f"Error in ranking-based recommendation: {e}")
            return self._create_hold_recommendation(
                symbol, date, f"Ranking error: {str(e)}"
            )
    
    def _get_signal_based_recommendation(
        self, 
        symbol: str, 
        date: str, 
        timeframes: List[str]
    ) -> Recommendation:
        """Generate recommendation based on multi-timeframe signals (legacy method)."""
            # Load multi-timeframe signals
            mtf_signals = self._load_mtf_signals(symbol, date, timeframes)
            
            if not mtf_signals:
                return self._create_hold_recommendation(
                    symbol, date, "No signals available for analysis"
                )
        
        # Compute combined score
        combined_score, direction, confidence = self._compute_combined_score(mtf_signals)
        
        if combined_score < 0.3:  # Low confidence threshold
            return self._create_hold_recommendation(
                symbol, date, f"Low confidence score: {combined_score:.2f}"
            )
        
        # Check for strong conflicts
        if self._has_strong_conflict(mtf_signals):
            return self._create_hold_recommendation(
                symbol, date, "Strong directional conflict between timeframes"
            )
        
        # Generate trade plan
        trade_plan = self._generate_trade_plan(symbol, date, direction, mtf_signals)
        
        if not trade_plan:
            return self._create_hold_recommendation(
                symbol, date, "Unable to generate valid trade plan"
            )
        
        # Create recommendation
        recommendation = Recommendation(
            date=date,
            symbol=symbol,
            timeframe=trade_plan["timeframe"],
            direction=PlanDirection.LONG if direction > 0 else PlanDirection.SHORT,
            entry_band=trade_plan["entry_band"],
            stop_loss=trade_plan["stop_loss"],
            take_profit=trade_plan["take_profit"],
            quantity=trade_plan["quantity"],
            risk_amount=trade_plan["risk_amount"],
            risk_percentage=trade_plan["risk_percentage"],
            confidence=confidence,
            rationale=f"Multi-timeframe analysis: {combined_score:.2f} score",
            dataset_hash=self._compute_dataset_hash(symbol, date, timeframes),
            params_hash=self._compute_params_hash()
        )
        
        # Save recommendation
        self._save_recommendation(recommendation)
        
            return recommendation
            
    def _combine_strategy_rankings(self, best_strategies: Dict[str, StrategyRecommendation]) -> Tuple[float, int, float]:
        """Combine strategy rankings across timeframes."""
        if not best_strategies:
            return 0.0, 0, 0.0
        
        # Weight timeframes (shorter = higher weight for responsiveness)
        timeframe_weights = {"1h": 0.5, "4h": 0.3, "1d": 0.2}
        
        total_score = 0.0
        total_weight = 0.0
        directions = []
        confidences = []
        
        for tf, strategy in best_strategies.items():
            weight = timeframe_weights.get(tf, 0.1)
            total_score += strategy.composite_score * weight
            total_weight += weight
            directions.append(strategy.signal_direction)
            confidences.append(strategy.confidence)
        
        if total_weight == 0:
            return 0.0, 0, 0.0
        
        combined_score = total_score / total_weight
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        # Determine direction (majority vote)
        direction = 1 if sum(directions) > 0 else -1 if sum(directions) < 0 else 0
        
        return combined_score, direction, avg_confidence
    
    def _create_enhanced_recommendation(
        self,
        symbol: str,
        date: str,
        best_strategy: StrategyRecommendation,
        direction: int,
        confidence: float,
        combined_score: float
    ) -> Recommendation:
        """Create enhanced recommendation with strategy details."""
        # Determine plan direction
        plan_direction = PlanDirection.LONG if direction > 0 else PlanDirection.SHORT if direction < 0 else PlanDirection.HOLD
        
        # Create enhanced rationale
        rationale = f"Best strategy: {best_strategy.strategy_name} (Score: {best_strategy.composite_score:.2f}, Sharpe: {best_strategy.sharpe_ratio:.2f})"
        
        return Recommendation(
            date=date,
            symbol=symbol,
            timeframe=best_strategy.timeframe,
            direction=plan_direction,
            entry_band=best_strategy.entry_price if hasattr(best_strategy, 'entry_price') else None,
            stop_loss=best_strategy.stop_loss if hasattr(best_strategy, 'stop_loss') else None,
            take_profit=best_strategy.take_profit if hasattr(best_strategy, 'take_profit') else None,
            quantity=best_strategy.quantity if hasattr(best_strategy, 'quantity') else None,
            risk_amount=best_strategy.risk_amount if hasattr(best_strategy, 'risk_amount') else None,
            risk_percentage=best_strategy.risk_percentage if hasattr(best_strategy, 'risk_percentage') else None,
            confidence=confidence,
            rationale=rationale,
            # Strategy information
            strategy_name=best_strategy.strategy_name,
            strategy_score=best_strategy.composite_score,
            sharpe_ratio=best_strategy.sharpe_ratio,
            win_rate=best_strategy.win_rate,
            max_drawdown=best_strategy.max_drawdown,
            # Multi-timeframe analysis
            mtf_analysis={
                "combined_score": combined_score,
                "direction": direction,
                "confidence": confidence
            },
            ranking_weights={
                "1h": 0.5,
                "4h": 0.3,
                "1d": 0.2
            },
            dataset_hash=f"strategy_{best_strategy.strategy_name}_{date}",
            params_hash=f"ranking_{combined_score:.2f}"
        )
    
    def _create_hold_recommendation(self, symbol: str, date: str, reason: str) -> Recommendation:
        """Create HOLD recommendation with reason."""
        return Recommendation(
            date=date,
            symbol=symbol,
            timeframe="1h",
            direction=PlanDirection.HOLD,
            entry_band=None,
            stop_loss=None,
            take_profit=None,
            quantity=None,
            risk_amount=None,
            risk_percentage=None,
            confidence=0.0,
            rationale=f"HOLD: {reason}",
            dataset_hash=f"hold_{date}",
            params_hash="hold_params"
            )
    
    def _load_mtf_signals(self, symbol: str, date: str, timeframes: List[str]) -> Dict[str, Dict]:
        """Load multi-timeframe signals for analysis."""
        mtf_signals = {}
        
        for tf in timeframes:
            try:
                # Load data for the specific date
                target_date = datetime.fromisoformat(date)
                start_date = target_date - timedelta(days=1)
                end_date = target_date + timedelta(days=1)
                
                bars = self.store.read_bars(symbol, tf, since=start_date, until=end_date)
                
                if not bars:
                    logger.warning(f"No data for {symbol} {tf} on {date}")
                    continue
                
                # Convert to DataFrame
                if isinstance(bars, list):
                    df = pd.DataFrame([bar.to_dict() for bar in bars])
                    df = df.sort_values('timestamp').reset_index(drop=True)
                
                # Filter to target date
                target_ts = int(target_date.timestamp() * 1000)
                df = df[df['timestamp'] <= target_ts]
                
                if len(df) < 50:  # Need minimum data for signals
                    continue
                
                # Generate signals for multiple strategies
                strategies = ["ma_crossover", "rsi_regime_pullback", "trend_following_ema"]
                tf_signals = {}
                
                for strategy in strategies:
                    try:
                        signal_output = generate_signal(strategy, df)
                        if signal_output and not signal_output.signal.empty:
                            tf_signals[strategy] = {
                                'signal': signal_output.signal.iloc[-1],
                                'strength': signal_output.strength.iloc[-1] if signal_output.strength is not None else 0.0,
                                'metadata': signal_output.metadata
                            }
                    except Exception as e:
                        logger.warning(f"Error generating {strategy} signal for {tf}: {e}")
                        continue
                
                if tf_signals:
                    mtf_signals[tf] = tf_signals
                    
            except Exception as e:
                logger.error(f"Error loading signals for {tf}: {e}")
                continue
        
        return mtf_signals
    
    def _compute_combined_score(self, mtf_signals: Dict[str, Dict]) -> Tuple[float, int, float]:
        """Compute combined score from multi-timeframe signals."""
        if not mtf_signals:
            return 0.0, 0, 0.0
        
        # Weight timeframes
        timeframe_weights = {"1h": 0.5, "4h": 0.3, "1d": 0.2}
        
        total_score = 0.0
        total_weight = 0.0
        directions = []
        confidences = []
        
        for tf, signals in mtf_signals.items():
            weight = timeframe_weights.get(tf, 0.1)
            
            # Average signal strength across strategies
            tf_score = 0.0
            tf_directions = []
            tf_confidences = []
            
            for strategy, data in signals.items():
                signal = data['signal']
                strength = data['strength']
                
                tf_score += signal * strength
                tf_directions.append(signal)
                tf_confidences.append(abs(strength))
            
            if tf_directions:
                tf_score = tf_score / len(tf_directions)
                total_score += tf_score * weight
                total_weight += weight
                directions.append(1 if tf_score > 0 else -1 if tf_score < 0 else 0)
                confidences.append(np.mean(tf_confidences))
        
        if total_weight == 0:
            return 0.0, 0, 0.0
        
        combined_score = total_score / total_weight
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        # Determine direction (majority vote)
        direction = 1 if sum(directions) > 0 else -1 if sum(directions) < 0 else 0
        
        return combined_score, direction, avg_confidence
    
    def _has_strong_conflict(self, mtf_signals: Dict[str, Dict]) -> bool:
        """Check for strong directional conflicts between timeframes."""
        if len(mtf_signals) < 2:
            return False
        
        directions = []
        for tf, signals in mtf_signals.items():
            tf_directions = []
            for strategy, data in signals.items():
                signal = data['signal']
                if signal != 0:
                    tf_directions.append(signal)
            
            if tf_directions:
                # Majority direction for this timeframe
                tf_direction = 1 if sum(tf_directions) > 0 else -1 if sum(tf_directions) < 0 else 0
                directions.append(tf_direction)
        
        if len(directions) < 2:
            return False
        
        # Check for strong conflicts (opposite directions)
        long_count = sum(1 for d in directions if d > 0)
        short_count = sum(1 for d in directions if d < 0)
        
        return long_count > 0 and short_count > 0 and abs(long_count - short_count) <= 1
    
    def _generate_trade_plan(self, symbol: str, date: str, direction: int, mtf_signals: Dict[str, Dict]) -> Optional[Dict[str, Any]]:
        """Generate trade plan from signals."""
        if direction == 0:
            return None
        
        try:
            # Get latest price
            latest_tf = max(mtf_signals.keys(), key=lambda tf: len(mtf_signals[tf]))
            latest_signals = mtf_signals[latest_tf]
            
            # Use the strongest signal
            best_strategy = max(latest_signals.keys(), 
                              key=lambda s: abs(latest_signals[s]['strength']))
            
            signal_data = latest_signals[best_strategy]
            strength = signal_data['strength']
            
            # Load current price
            target_date = datetime.fromisoformat(date)
            bars = self.store.read_bars(symbol, "1h", since=target_date - timedelta(hours=1), until=target_date)
            
            if not bars:
                return None
            
            current_price = bars[-1].close
            
            # Calculate position size
            risk_amount = self.capital * self.max_risk_pct
            quantity = risk_amount / current_price
            
            # Calculate stop loss and take profit
            if direction > 0:  # Long
                stop_loss = current_price * 0.95  # 5% stop loss
                take_profit = current_price * 1.10  # 10% take profit
            else:  # Short
                stop_loss = current_price * 1.05  # 5% stop loss
                take_profit = current_price * 0.90  # 10% take profit
            
            return {
                "timeframe": latest_tf,
                "entry_band": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "quantity": quantity,
                "risk_amount": risk_amount,
                "risk_percentage": self.max_risk_pct,
                "rationale": f"Based on {best_strategy} with strength {strength:.2f}",
                "dataset_hash": self._compute_dataset_hash(symbol, date, list(mtf_signals.keys())),
                "params_hash": self._compute_params_hash()
            }
            
        except Exception as e:
            logger.error(f"Error generating trade plan: {e}")
            return None
    
    def _compute_dataset_hash(self, symbol: str, date: str, timeframes: List[str]) -> str:
        """Compute dataset hash for reproducibility."""
        data_str = f"{symbol}_{date}_{'_'.join(timeframes)}"
        return hashlib.md5(data_str.encode()).hexdigest()[:8]
    
    def _compute_params_hash(self) -> str:
        """Compute parameters hash."""
        params = {
            "capital": self.capital,
            "max_risk_pct": self.max_risk_pct
        }
        return hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]
    
    def _save_recommendation(self, recommendation: Recommendation):
        """Save recommendation to database."""
        try:
        db_path = self.store.base_path / "recommendations.db"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO recommendations 
                    (date, symbol, timeframe, direction, confidence, rationale, dataset_hash, params_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recommendation.date,
                recommendation.symbol,
                recommendation.timeframe,
                recommendation.direction.value,
                    recommendation.confidence,
                recommendation.rationale,
                recommendation.dataset_hash,
                    recommendation.params_hash
            ))
            
            conn.commit()
    
        except Exception as e:
            logger.error(f"Error saving recommendation: {e}")
    
    def _get_timeframe_rankings(self, symbol: str, timeframe: str, date: str) -> List[Dict[str, Any]]:
        """Get rankings for a specific timeframe."""
        try:
            # Get rankings from strategy ranking service
            rankings = self.strategy_ranking.get_rankings(
                symbol=symbol,
                timeframe=timeframe,
                limit=10
            )
            
            # Convert to format expected by weight calculator
            ranking_data = []
            for ranking in rankings:
                ranking_data.append({
                    'strategy_name': ranking.get('strategy_name', 'Unknown'),
                    'timeframe': timeframe,
                    'composite_score': ranking.get('composite_score', 0.0),
                    'sharpe_ratio': ranking.get('sharpe_ratio', 0.0),
                    'win_rate': ranking.get('win_rate', 0.0),
                    'profit_factor': ranking.get('profit_factor', 0.0),
                    'max_drawdown': ranking.get('max_drawdown', 0.0),
                    'cagr': ranking.get('cagr', 0.0),
                    'total_trades': ranking.get('total_trades', 0),
                    'direction': ranking.get('direction', 0)
                })
            
            return ranking_data
            
        except Exception as e:
            logger.error(f"Error getting timeframe rankings for {timeframe}: {e}")
            return []
    
    def _determine_direction_from_weights(self, direction_weights: Dict[str, float]) -> int:
        """Determine direction from weight distribution."""
        if direction_weights['LONG'] > direction_weights['SHORT'] and direction_weights['LONG'] > direction_weights['HOLD']:
            return 1  # LONG
        elif direction_weights['SHORT'] > direction_weights['LONG'] and direction_weights['SHORT'] > direction_weights['HOLD']:
            return -1  # SHORT
        else:
            return 0  # HOLD
    
    def _create_weighted_recommendation(
        self,
        symbol: str,
        date: str,
        best_strategy_weight,
        weights,
        direction: int
    ) -> Recommendation:
        """Create recommendation with weight information."""
        plan_direction = PlanDirection.LONG if direction > 0 else PlanDirection.SHORT if direction < 0 else PlanDirection.HOLD
        
        # Create rationale with weight information
        rationale = (
            f"Best strategy: {best_strategy_weight.strategy_name} "
            f"(Weight: {best_strategy_weight.weight:.3f}, Score: {best_strategy_weight.score:.3f}). "
            f"Direction weights: LONG={weights.direction_weights['LONG']:.3f}, "
            f"SHORT={weights.direction_weights['SHORT']:.3f}, HOLD={weights.direction_weights['HOLD']:.3f}. "
            f"Overall confidence: {weights.confidence:.1%}"
        )
        
        return Recommendation(
            date=date,
            symbol=symbol,
            timeframe=best_strategy_weight.timeframe,
            direction=plan_direction,
            entry_band=None,  # Will be calculated by strategy
            stop_loss=None,
            take_profit=None,
            quantity=None,
            risk_amount=None,
            risk_percentage=None,
            confidence=weights.confidence,
            rationale=rationale,
            strategy_name=best_strategy_weight.strategy_name,
            strategy_score=best_strategy_weight.score,
            sharpe_ratio=best_strategy_weight.metrics.get('sharpe_ratio', 0.0),
            win_rate=best_strategy_weight.metrics.get('win_rate', 0.0),
            max_drawdown=best_strategy_weight.metrics.get('max_drawdown', 0.0),
            mtf_analysis={
                "combined_score": weights.confidence,
                "direction": direction,
                "confidence": weights.confidence,
                "weight_distribution": weights.direction_weights,
                "strategy_weights": [
                    {
                        "strategy": sw.strategy_name,
                        "timeframe": sw.timeframe,
                        "weight": sw.weight,
                        "score": sw.score
                    } for sw in weights.strategy_weights
                ]
            },
            ranking_weights=weights.direction_weights,
            dataset_hash=f"weighted_{best_strategy_weight.strategy_name}_{date}",
            params_hash=f"weights_{weights.confidence:.2f}"
        )
