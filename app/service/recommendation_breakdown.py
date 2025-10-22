"""Recommendation breakdown storage and retrieval.

This module handles storing and retrieving detailed breakdowns of
recommendation calculations for transparency and auditability.
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class RecommendationBreakdown(BaseModel):
    """Detailed breakdown of recommendation calculation."""
    
    id: Optional[int] = None
    recommendation_id: str
    symbol: str
    date: str
    timestamp: datetime
    
    # Strategy weights
    strategy_weights: List[Dict[str, Any]]
    direction_weights: Dict[str, float]
    
    # Calculation details
    calculation_method: str
    confidence: float
    rationale: str
    
    # Performance metrics
    top_strategy: Dict[str, Any]
    metrics_summary: Dict[str, Any]
    
    # Metadata
    created_at: datetime
    updated_at: datetime


class RecommendationBreakdownDB:
    """Database operations for recommendation breakdowns."""
    
    def __init__(self, db_path: str = "storage/recommendations.db"):
        """Initialize breakdown database.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_db()
        logger.info(f"RecommendationBreakdownDB initialized with path: {db_path}")
    
    def _init_db(self):
        """Initialize database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create breakdown table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS recommendation_breakdowns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recommendation_id TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        date TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        strategy_weights TEXT NOT NULL,
                        direction_weights TEXT NOT NULL,
                        calculation_method TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        rationale TEXT NOT NULL,
                        top_strategy TEXT NOT NULL,
                        metrics_summary TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_breakdown_recommendation_id 
                    ON recommendation_breakdowns(recommendation_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_breakdown_symbol_date 
                    ON recommendation_breakdowns(symbol, date)
                """)
                
                conn.commit()
                logger.info("Recommendation breakdown database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing breakdown database: {e}")
            raise
    
    def save_breakdown(self, breakdown: RecommendationBreakdown) -> bool:
        """Save recommendation breakdown.
        
        Args:
            breakdown: Breakdown to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO recommendation_breakdowns (
                        recommendation_id, symbol, date, timestamp,
                        strategy_weights, direction_weights, calculation_method,
                        confidence, rationale, top_strategy, metrics_summary,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    breakdown.recommendation_id,
                    breakdown.symbol,
                    breakdown.date,
                    breakdown.timestamp.isoformat(),
                    json.dumps(breakdown.strategy_weights),
                    json.dumps(breakdown.direction_weights),
                    breakdown.calculation_method,
                    breakdown.confidence,
                    breakdown.rationale,
                    json.dumps(breakdown.top_strategy),
                    json.dumps(breakdown.metrics_summary),
                    breakdown.created_at.isoformat(),
                    breakdown.updated_at.isoformat()
                ))
                
                conn.commit()
                logger.info(f"Breakdown saved for recommendation {breakdown.recommendation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving breakdown: {e}")
            return False
    
    def get_breakdown(self, recommendation_id: str) -> Optional[RecommendationBreakdown]:
        """Get breakdown by recommendation ID.
        
        Args:
            recommendation_id: ID of recommendation
            
        Returns:
            Breakdown if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM recommendation_breakdowns 
                    WHERE recommendation_id = ?
                """, (recommendation_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return self._row_to_breakdown(row)
                
        except Exception as e:
            logger.error(f"Error getting breakdown: {e}")
            return None
    
    def get_breakdowns_by_symbol_date(
        self, 
        symbol: str, 
        date: str
    ) -> List[RecommendationBreakdown]:
        """Get breakdowns for symbol and date.
        
        Args:
            symbol: Trading symbol
            date: Date string
            
        Returns:
            List of breakdowns
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM recommendation_breakdowns 
                    WHERE symbol = ? AND date = ?
                    ORDER BY timestamp DESC
                """, (symbol, date))
                
                rows = cursor.fetchall()
                return [self._row_to_breakdown(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting breakdowns by symbol/date: {e}")
            return []
    
    def get_recent_breakdowns(self, limit: int = 10) -> List[RecommendationBreakdown]:
        """Get recent breakdowns.
        
        Args:
            limit: Maximum number of breakdowns
            
        Returns:
            List of recent breakdowns
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM recommendation_breakdowns 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                return [self._row_to_breakdown(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting recent breakdowns: {e}")
            return []
    
    def _row_to_breakdown(self, row: tuple) -> RecommendationBreakdown:
        """Convert database row to breakdown object."""
        return RecommendationBreakdown(
            id=row[0],
            recommendation_id=row[1],
            symbol=row[2],
            date=row[3],
            timestamp=datetime.fromisoformat(row[4]),
            strategy_weights=json.loads(row[5]),
            direction_weights=json.loads(row[6]),
            calculation_method=row[7],
            confidence=row[8],
            rationale=row[9],
            top_strategy=json.loads(row[10]),
            metrics_summary=json.loads(row[11]),
            created_at=datetime.fromisoformat(row[12]),
            updated_at=datetime.fromisoformat(row[13])
        )
    
    def delete_old_breakdowns(self, days: int = 30) -> int:
        """Delete old breakdowns.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of deleted records
        """
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM recommendation_breakdowns 
                    WHERE created_at < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Deleted {deleted_count} old breakdowns")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error deleting old breakdowns: {e}")
            return 0


class RecommendationBreakdownService:
    """Service for managing recommendation breakdowns."""
    
    def __init__(self, db_path: str = "storage/recommendations.db"):
        """Initialize breakdown service.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db = RecommendationBreakdownDB(db_path)
        logger.info("RecommendationBreakdownService initialized")
    
    def create_breakdown(
        self,
        recommendation_id: str,
        symbol: str,
        date: str,
        strategy_weights: List[Dict[str, Any]],
        direction_weights: Dict[str, float],
        calculation_method: str,
        confidence: float,
        rationale: str,
        top_strategy: Dict[str, Any],
        metrics_summary: Dict[str, Any]
    ) -> bool:
        """Create and save breakdown.
        
        Args:
            recommendation_id: ID of recommendation
            symbol: Trading symbol
            date: Date string
            strategy_weights: List of strategy weights
            direction_weights: Direction weight distribution
            calculation_method: Method used for calculation
            confidence: Overall confidence
            rationale: Explanation
            top_strategy: Best strategy details
            metrics_summary: Summary of metrics
            
        Returns:
            True if successful, False otherwise
        """
        try:
            now = datetime.now()
            
            breakdown = RecommendationBreakdown(
                recommendation_id=recommendation_id,
                symbol=symbol,
                date=date,
                timestamp=now,
                strategy_weights=strategy_weights,
                direction_weights=direction_weights,
                calculation_method=calculation_method,
                confidence=confidence,
                rationale=rationale,
                top_strategy=top_strategy,
                metrics_summary=metrics_summary,
                created_at=now,
                updated_at=now
            )
            
            return self.db.save_breakdown(breakdown)
            
        except Exception as e:
            logger.error(f"Error creating breakdown: {e}")
            return False
    
    def get_breakdown(self, recommendation_id: str) -> Optional[RecommendationBreakdown]:
        """Get breakdown by ID."""
        return self.db.get_breakdown(recommendation_id)
    
    def get_breakdowns_for_date(
        self, 
        symbol: str, 
        date: str
    ) -> List[RecommendationBreakdown]:
        """Get breakdowns for specific date."""
        return self.db.get_breakdowns_by_symbol_date(symbol, date)
    
    def get_recent_breakdowns(self, limit: int = 10) -> List[RecommendationBreakdown]:
        """Get recent breakdowns."""
        return self.db.get_recent_breakdowns(limit)
    
    def cleanup_old_breakdowns(self, days: int = 30) -> int:
        """Clean up old breakdowns."""
        return self.db.delete_old_breakdowns(days)
