"""Structured logging for One Market platform.

This module provides structured logging with JSONL format for traceability.
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
import subprocess
import os


class StructuredLogger:
    """Structured logger with JSONL format."""
    
    def __init__(self, log_file: str = "logs/one_market.log"):
        """Initialize structured logger.
        
        Args:
            log_file: Path to log file
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Get commit SHA
        self.commit_sha = self._get_commit_sha()
        
        # Setup logger
        self.logger = logging.getLogger("one_market")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Add file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Add formatter
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _get_commit_sha(self) -> str:
        """Get current commit SHA.
        
        Returns:
            Commit SHA or 'unknown' if not available
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            if result.returncode == 0:
                return result.stdout.strip()[:8]  # Short SHA
        except Exception:
            pass
        
        return "unknown"
    
    def _create_log_entry(
        self,
        level: str,
        component: str,
        message: str,
        dataset_hash: Optional[str] = None,
        params_hash: Optional[str] = None,
        run_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create structured log entry.
        
        Args:
            level: Log level
            component: Component name
            message: Log message
            dataset_hash: Dataset hash
            params_hash: Parameters hash
            run_id: Run ID
            **kwargs: Additional fields
            
        Returns:
            Structured log entry
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id or str(uuid.uuid4()),
            "component": component,
            "level": level,
            "message": message,
            "commit_sha": self.commit_sha
        }
        
        if dataset_hash:
            entry["dataset_hash"] = dataset_hash
        
        if params_hash:
            entry["params_hash"] = params_hash
        
        # Add additional fields
        entry.update(kwargs)
        
        return entry
    
    def info(
        self,
        component: str,
        message: str,
        dataset_hash: Optional[str] = None,
        params_hash: Optional[str] = None,
        run_id: Optional[str] = None,
        **kwargs
    ):
        """Log info message.
        
        Args:
            component: Component name
            message: Log message
            dataset_hash: Dataset hash
            params_hash: Parameters hash
            run_id: Run ID
            **kwargs: Additional fields
        """
        entry = self._create_log_entry(
            "INFO", component, message, dataset_hash, params_hash, run_id, **kwargs
        )
        self.logger.info(json.dumps(entry))
    
    def warning(
        self,
        component: str,
        message: str,
        dataset_hash: Optional[str] = None,
        params_hash: Optional[str] = None,
        run_id: Optional[str] = None,
        **kwargs
    ):
        """Log warning message.
        
        Args:
            component: Component name
            message: Log message
            dataset_hash: Dataset hash
            params_hash: Parameters hash
            run_id: Run ID
            **kwargs: Additional fields
        """
        entry = self._create_log_entry(
            "WARNING", component, message, dataset_hash, params_hash, run_id, **kwargs
        )
        self.logger.warning(json.dumps(entry))
    
    def error(
        self,
        component: str,
        message: str,
        dataset_hash: Optional[str] = None,
        params_hash: Optional[str] = None,
        run_id: Optional[str] = None,
        **kwargs
    ):
        """Log error message.
        
        Args:
            component: Component name
            message: Log message
            dataset_hash: Dataset hash
            params_hash: Parameters hash
            run_id: Run ID
            **kwargs: Additional fields
        """
        entry = self._create_log_entry(
            "ERROR", component, message, dataset_hash, params_hash, run_id, **kwargs
        )
        self.logger.error(json.dumps(entry))
    
    def backtest_start(
        self,
        symbol: str,
        timeframe: str,
        strategy: str,
        dataset_hash: str,
        params_hash: str,
        run_id: str
    ):
        """Log backtest start.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            strategy: Strategy name
            dataset_hash: Dataset hash
            params_hash: Parameters hash
            run_id: Run ID
        """
        self.info(
            "backtest",
            f"Starting backtest for {symbol} {timeframe} with {strategy}",
            dataset_hash=dataset_hash,
            params_hash=params_hash,
            run_id=run_id,
            symbol=symbol,
            timeframe=timeframe,
            strategy=strategy
        )
    
    def backtest_complete(
        self,
        symbol: str,
        timeframe: str,
        strategy: str,
        dataset_hash: str,
        params_hash: str,
        run_id: str,
        total_trades: int,
        sharpe_ratio: float,
        execution_time: float
    ):
        """Log backtest completion.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            strategy: Strategy name
            dataset_hash: Dataset hash
            params_hash: Parameters hash
            run_id: Run ID
            total_trades: Number of trades
            sharpe_ratio: Sharpe ratio
            execution_time: Execution time in seconds
        """
        self.info(
            "backtest",
            f"Backtest completed for {symbol} {timeframe} with {strategy}",
            dataset_hash=dataset_hash,
            params_hash=params_hash,
            run_id=run_id,
            symbol=symbol,
            timeframe=timeframe,
            strategy=strategy,
            total_trades=total_trades,
            sharpe_ratio=sharpe_ratio,
            execution_time=execution_time
        )
    
    def recommendation_generated(
        self,
        symbol: str,
        date: str,
        direction: str,
        confidence: int,
        dataset_hash: str,
        params_hash: str,
        run_id: str
    ):
        """Log recommendation generation.
        
        Args:
            symbol: Trading symbol
            date: Date
            direction: Recommendation direction
            confidence: Confidence level
            dataset_hash: Dataset hash
            params_hash: Parameters hash
            run_id: Run ID
        """
        self.info(
            "recommendation",
            f"Generated {direction} recommendation for {symbol} on {date}",
            dataset_hash=dataset_hash,
            params_hash=params_hash,
            run_id=run_id,
            symbol=symbol,
            date=date,
            direction=direction,
            confidence=confidence
        )
    
    def job_start(self, job_name: str, run_id: str):
        """Log job start.
        
        Args:
            job_name: Job name
            run_id: Run ID
        """
        self.info(
            "scheduler",
            f"Starting job {job_name}",
            run_id=run_id,
            job_name=job_name
        )
    
    def job_complete(self, job_name: str, run_id: str, success: bool, duration: float):
        """Log job completion.
        
        Args:
            job_name: Job name
            run_id: Run ID
            success: Whether job was successful
            duration: Job duration in seconds
        """
        level = "INFO" if success else "ERROR"
        message = f"Job {job_name} completed successfully" if success else f"Job {job_name} failed"
        
        entry = self._create_log_entry(
            level, "scheduler", message, run_id=run_id,
            job_name=job_name, success=success, duration=duration
        )
        
        if success:
            self.logger.info(json.dumps(entry))
        else:
            self.logger.error(json.dumps(entry))


# Global structured logger instance
structured_logger = StructuredLogger()

# Compatibility aliases for imports
logger = structured_logger
event_logger = structured_logger


def get_structured_logger() -> StructuredLogger:
    """Get the global structured logger.
    
    Returns:
        StructuredLogger instance
    """
    return structured_logger