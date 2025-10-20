"""Storage utilities for optimization results.

This module provides storage and retrieval of optimization results
using SQLite and Parquet formats.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
from pydantic import BaseModel, Field


class OptimizationResult(BaseModel):
    """Single optimization result."""
    
    run_id: str = Field(..., description="Unique run identifier")
    strategy_name: str = Field(..., description="Strategy name")
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe")
    parameters: Dict[str, Any] = Field(..., description="Strategy parameters")
    metrics: Dict[str, float] = Field(..., description="Performance metrics")
    score: float = Field(..., description="Optimization score")
    timestamp: datetime = Field(default_factory=datetime.now, description="Optimization timestamp")
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class OptimizationStorage:
    """Storage manager for optimization results."""
    
    def __init__(self, storage_path: str = "storage/optimization"):
        """Initialize optimization storage.
        
        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_path / "optimization.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_results (
                run_id TEXT PRIMARY KEY,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                parameters TEXT NOT NULL,
                metrics TEXT NOT NULL,
                score REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_strategy_symbol 
            ON optimization_results(strategy_name, symbol, timeframe)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_score 
            ON optimization_results(score DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def save_result(self, result: OptimizationResult):
        """Save optimization result to database.
        
        Args:
            result: Optimization result to save
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO optimization_results 
            (run_id, strategy_name, symbol, timeframe, parameters, metrics, score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.run_id,
            result.strategy_name,
            result.symbol,
            result.timeframe,
            json.dumps(result.parameters),
            json.dumps(result.metrics),
            result.score,
            result.timestamp.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def save_results_batch(self, results: List[OptimizationResult]):
        """Save multiple optimization results.
        
        Args:
            results: List of optimization results
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        data = [
            (
                r.run_id,
                r.strategy_name,
                r.symbol,
                r.timeframe,
                json.dumps(r.parameters),
                json.dumps(r.metrics),
                r.score,
                r.timestamp.isoformat()
            )
            for r in results
        ]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO optimization_results 
            (run_id, strategy_name, symbol, timeframe, parameters, metrics, score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        
        conn.commit()
        conn.close()
    
    def get_best_parameters(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        top_n: int = 1
    ) -> List[OptimizationResult]:
        """Get best parameters for a strategy.
        
        Args:
            strategy_name: Strategy name
            symbol: Trading symbol
            timeframe: Timeframe
            top_n: Number of top results to return
            
        Returns:
            List of best optimization results
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT run_id, strategy_name, symbol, timeframe, parameters, metrics, score, timestamp
            FROM optimization_results
            WHERE strategy_name = ? AND symbol = ? AND timeframe = ?
            ORDER BY score DESC
            LIMIT ?
        """, (strategy_name, symbol, timeframe, top_n))
        
        results = []
        for row in cursor.fetchall():
            results.append(OptimizationResult(
                run_id=row[0],
                strategy_name=row[1],
                symbol=row[2],
                timeframe=row[3],
                parameters=json.loads(row[4]),
                metrics=json.loads(row[5]),
                score=row[6],
                timestamp=datetime.fromisoformat(row[7])
            ))
        
        conn.close()
        return results
    
    def get_all_results(
        self,
        strategy_name: Optional[str] = None,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        min_score: Optional[float] = None
    ) -> List[OptimizationResult]:
        """Get all optimization results with optional filters.
        
        Args:
            strategy_name: Filter by strategy name
            symbol: Filter by symbol
            timeframe: Filter by timeframe
            min_score: Minimum score threshold
            
        Returns:
            List of optimization results
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        query = "SELECT run_id, strategy_name, symbol, timeframe, parameters, metrics, score, timestamp FROM optimization_results WHERE 1=1"
        params = []
        
        if strategy_name:
            query += " AND strategy_name = ?"
            params.append(strategy_name)
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if timeframe:
            query += " AND timeframe = ?"
            params.append(timeframe)
        
        if min_score is not None:
            query += " AND score >= ?"
            params.append(min_score)
        
        query += " ORDER BY score DESC"
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append(OptimizationResult(
                run_id=row[0],
                strategy_name=row[1],
                symbol=row[2],
                timeframe=row[3],
                parameters=json.loads(row[4]),
                metrics=json.loads(row[5]),
                score=row[6],
                timestamp=datetime.fromisoformat(row[7])
            ))
        
        conn.close()
        return results
    
    def export_to_parquet(self, output_path: Optional[str] = None) -> str:
        """Export all results to Parquet file.
        
        Args:
            output_path: Output file path (default: storage/optimization/results.parquet)
            
        Returns:
            Path to exported file
        """
        if output_path is None:
            output_path = str(self.storage_path / "results.parquet")
        
        results = self.get_all_results()
        
        # Convert to DataFrame
        data = []
        for r in results:
            row = {
                'run_id': r.run_id,
                'strategy_name': r.strategy_name,
                'symbol': r.symbol,
                'timeframe': r.timeframe,
                'score': r.score,
                'timestamp': r.timestamp
            }
            # Flatten parameters and metrics
            for k, v in r.parameters.items():
                row[f'param_{k}'] = v
            for k, v in r.metrics.items():
                row[f'metric_{k}'] = v
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_parquet(output_path, index=False)
        
        return output_path
    
    def clear_results(
        self,
        strategy_name: Optional[str] = None,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None
    ):
        """Clear optimization results.
        
        Args:
            strategy_name: Filter by strategy name
            symbol: Filter by symbol
            timeframe: Filter by timeframe
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if strategy_name or symbol or timeframe:
            query = "DELETE FROM optimization_results WHERE 1=1"
            params = []
            
            if strategy_name:
                query += " AND strategy_name = ?"
                params.append(strategy_name)
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if timeframe:
                query += " AND timeframe = ?"
                params.append(timeframe)
            
            cursor.execute(query, params)
        else:
            cursor.execute("DELETE FROM optimization_results")
        
        conn.commit()
        conn.close()

