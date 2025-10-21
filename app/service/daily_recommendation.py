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
                    entry_price REAL,
                    entry_band_min REAL,
                    entry_band_max REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    quantity REAL,
                    risk_amount REAL,
                    risk_percentage REAL,
                    rationale TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    dataset_hash TEXT NOT NULL,
                    params_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    UNIQUE(date, symbol, timeframe)
                )
            """)
            
            # Create signals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    direction INTEGER NOT NULL,
                    strength REAL NOT NULL,
                    components_json TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    def get_daily_recommendation(
        self, 
        symbol: str, 
        date: str,
        timeframes: List[str] = None
    ) -> Recommendation:
        """Generate daily recommendation for symbol/date.
        
        Args:
            symbol: Trading symbol
            date: Date in YYYY-MM-DD format
            timeframes: List of timeframes to analyze
            
        Returns:
            Recommendation object or HOLD with reason
        """
        if timeframes is None:
            timeframes = ["15m", "1h", "4h", "1d"]
        
        try:
            logger.info(f"Generating recommendation for {symbol} on {date}")
            
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
                entry_price=trade_plan["entry_price"],
                stop_loss=trade_plan["stop_loss"],
                take_profit=trade_plan["take_profit"],
                quantity=trade_plan["quantity"],
                risk_amount=trade_plan["risk_amount"],
                risk_percentage=trade_plan["risk_percentage"],
                rationale=trade_plan["rationale"],
                confidence=int(confidence * 100),
                dataset_hash=trade_plan["dataset_hash"],
                params_hash=trade_plan["params_hash"],
                expires_at=datetime.fromisoformat(date) + timedelta(hours=24)
            )
            
            # Persist recommendation
            self._persist_recommendation(recommendation)
            
            logger.info(f"Generated recommendation: {direction} with confidence {confidence:.2f}")
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return self._create_hold_recommendation(
                symbol, date, f"Error in analysis: {str(e)}"
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
                        signal_output = generate_signal(df['close'], strategy)
                        if signal_output and not signal_output.signal.empty:
                            # Get latest signal
                            latest_signal = signal_output.signal.iloc[-1]
                            signal_strength = abs(latest_signal)
                            
                            tf_signals[strategy] = {
                                "direction": int(latest_signal),
                                "strength": float(signal_strength),
                                "timestamp": df['timestamp'].iloc[-1],
                                "price": float(df['close'].iloc[-1])
                            }
                    except Exception as e:
                        logger.warning(f"Error generating {strategy} signal for {tf}: {e}")
                        continue
                
                if tf_signals:
                    mtf_signals[tf] = {
                        "signals": tf_signals,
                        "current_price": float(df['close'].iloc[-1]),
                        "atr": self._calculate_atr(df, period=14)
                    }
                    
            except Exception as e:
                logger.error(f"Error loading signals for {tf}: {e}")
                continue
        
        return mtf_signals
    
    def _compute_combined_score(self, mtf_signals: Dict[str, Dict]) -> Tuple[float, int, float]:
        """Compute combined score from multi-timeframe signals."""
        if not mtf_signals:
            return 0.0, 0, 0.0
        
        # Weights for different timeframes (longer = more weight)
        timeframe_weights = {
            "15m": 0.1,
            "1h": 0.2,
            "4h": 0.3,
            "1d": 0.4
        }
        
        total_score = 0.0
        total_weight = 0.0
        direction_votes = []
        
        for tf, data in mtf_signals.items():
            weight = timeframe_weights.get(tf, 0.1)
            
            # Aggregate signals for this timeframe
            tf_direction = 0
            tf_strength = 0.0
            
            for strategy, signal_data in data["signals"].items():
                direction = signal_data["direction"]
                strength = signal_data["strength"]
                
                if direction != 0:  # Only count non-zero signals
                    tf_direction += direction
                    tf_strength += strength
            
            if tf_direction != 0:
                # Normalize direction (-1, 0, 1)
                tf_direction = 1 if tf_direction > 0 else -1
                tf_score = tf_strength * weight
                
                total_score += tf_score * tf_direction
                total_weight += weight
                direction_votes.append(tf_direction)
        
        if total_weight == 0:
            return 0.0, 0, 0.0
        
        # Normalize score
        normalized_score = total_score / total_weight
        
        # Determine final direction
        if len(direction_votes) >= 2:
            # Majority vote
            final_direction = 1 if sum(direction_votes) > 0 else -1
        else:
            final_direction = 1 if normalized_score > 0 else -1
        
        # Calculate confidence based on agreement
        agreement = len([d for d in direction_votes if d == final_direction]) / len(direction_votes) if direction_votes else 0.0
        confidence = min(abs(normalized_score), agreement)
        
        return abs(normalized_score), final_direction, confidence
    
    def _has_strong_conflict(self, mtf_signals: Dict[str, Dict]) -> bool:
        """Check for strong directional conflicts between timeframes."""
        directions = []
        
        for tf, data in mtf_signals.items():
            tf_direction = 0
            for strategy, signal_data in data["signals"].items():
                if signal_data["direction"] != 0:
                    tf_direction += signal_data["direction"]
            
            if tf_direction != 0:
                directions.append(1 if tf_direction > 0 else -1)
        
        if len(directions) < 2:
            return False
        
        # Check for strong conflict (opposite directions)
        positive_count = sum(1 for d in directions if d > 0)
        negative_count = sum(1 for d in directions if d < 0)
        
        # Strong conflict if we have both positive and negative with at least 2 each
        return positive_count >= 2 and negative_count >= 2
    
    def _generate_trade_plan(self, symbol: str, date: str, direction: int, mtf_signals: Dict[str, Dict]) -> Optional[Dict]:
        """Generate detailed trade plan."""
        try:
            # Find best timeframe (highest confidence)
            best_tf = max(mtf_signals.keys(), key=lambda tf: mtf_signals[tf].get("signals", {}))
            best_data = mtf_signals[best_tf]
            
            current_price = best_data["current_price"]
            atr = best_data["atr"]
            
            # Calculate entry band
            entry_band = [
                current_price * 0.995,  # 0.5% below
                current_price * 1.005   # 0.5% above
            ]
            
            # Calculate stop loss and take profit
            if direction > 0:  # LONG
                stop_loss = current_price - (atr * 2.0)
                take_profit = current_price + (atr * 3.0)
            else:  # SHORT
                stop_loss = current_price + (atr * 2.0)
                take_profit = current_price - (atr * 3.0)
            
            # Calculate position size
            risk_per_trade = self.capital * (self.max_risk_pct / 100)
            risk_per_unit = abs(current_price - stop_loss)
            quantity = risk_per_trade / risk_per_unit if risk_per_unit > 0 else 0
            
            # Generate rationale
            rationale = f"Multi-timeframe analysis shows {direction} signal with ATR-based risk management"
            
            # Create hashes for data integrity
            dataset_content = json.dumps({tf: data for tf, data in mtf_signals.items()}, sort_keys=True)
            dataset_hash = hashlib.sha256(dataset_content.encode()).hexdigest()
            
            params_content = json.dumps({
                "capital": self.capital,
                "max_risk_pct": self.max_risk_pct,
                "atr_multiplier_sl": 2.0,
                "atr_multiplier_tp": 3.0
            }, sort_keys=True)
            params_hash = hashlib.sha256(params_content.encode()).hexdigest()
            
            return {
                "timeframe": best_tf,
                "entry_band": entry_band,
                "entry_price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "quantity": quantity,
                "risk_amount": risk_per_trade,
                "risk_percentage": self.max_risk_pct,
                "rationale": rationale,
                "dataset_hash": dataset_hash,
                "params_hash": params_hash
            }
            
        except Exception as e:
            logger.error(f"Error generating trade plan: {e}")
            return None
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range."""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            # True Range calculation
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean().iloc[-1]
            
            return float(atr) if not pd.isna(atr) else df['close'].iloc[-1] * 0.02  # 2% fallback
        except Exception:
            return df['close'].iloc[-1] * 0.02  # 2% fallback
    
    def _create_hold_recommendation(self, symbol: str, date: str, reason: str) -> Recommendation:
        """Create HOLD recommendation with reason."""
        return Recommendation(
            date=date,
            symbol=symbol,
            timeframe="1h",
            direction=PlanDirection.HOLD,
            rationale=f"HOLD: {reason}",
            confidence=0,
            dataset_hash="hold_hash",
            params_hash="hold_params"
        )
    
    def _persist_recommendation(self, recommendation: Recommendation):
        """Persist recommendation to database."""
        db_path = self.store.base_path / "recommendations.db"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO recommendations 
                (date, symbol, timeframe, direction, entry_price, entry_band_min, entry_band_max,
                 stop_loss, take_profit, quantity, risk_amount, risk_percentage, rationale,
                 confidence, dataset_hash, params_hash, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recommendation.date,
                recommendation.symbol,
                recommendation.timeframe,
                recommendation.direction.value,
                recommendation.entry_price,
                recommendation.entry_band[0] if recommendation.entry_band else None,
                recommendation.entry_band[1] if recommendation.entry_band else None,
                recommendation.stop_loss,
                recommendation.take_profit,
                recommendation.quantity,
                recommendation.risk_amount,
                recommendation.risk_percentage,
                recommendation.rationale,
                recommendation.confidence,
                recommendation.dataset_hash,
                recommendation.params_hash,
                recommendation.created_at.isoformat(),
                recommendation.expires_at.isoformat() if recommendation.expires_at else None
            ))
            
            conn.commit()
    
    def get_recommendation_history(
        self, 
        symbol: str, 
        from_date: str, 
        to_date: str
    ) -> List[Recommendation]:
        """Get recommendation history for symbol and date range."""
        db_path = self.store.base_path / "recommendations.db"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT date, symbol, timeframe, direction, entry_price, entry_band_min, entry_band_max,
                       stop_loss, take_profit, quantity, risk_amount, risk_percentage, rationale,
                       confidence, dataset_hash, params_hash, created_at, expires_at
                FROM recommendations 
                WHERE symbol = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC
            """, (symbol, from_date, to_date))
            
            rows = cursor.fetchall()
            
            recommendations = []
            for row in rows:
                recommendations.append(Recommendation(
                    date=row[0],
                    symbol=row[1],
                    timeframe=row[2],
                    direction=PlanDirection(row[3]),
                    entry_price=row[4],
                    entry_band=[row[5], row[6]] if row[5] and row[6] else None,
                    stop_loss=row[7],
                    take_profit=row[8],
                    quantity=row[9],
                    risk_amount=row[10],
                    risk_percentage=row[11],
                    rationale=row[12],
                    confidence=row[13],
                    dataset_hash=row[14],
                    params_hash=row[15],
                    created_at=datetime.fromisoformat(row[16]),
                    expires_at=datetime.fromisoformat(row[17]) if row[17] else None
                ))
            
            return recommendations