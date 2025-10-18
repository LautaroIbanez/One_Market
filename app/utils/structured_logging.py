"""Structured logging with structlog.

This module provides structured logging with context for:
- Symbol and timeframe tracking
- Job execution logging
- Critical events (entry, TP/SL hits, forced close)
- Event persistence
"""
import structlog
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json

from app.config.settings import settings


def configure_structlog():
    """Configure structlog with processors and renderers."""
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if settings.STRUCTURED_LOGGING:
        # JSON renderer for structured logs
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Console renderer for human-readable logs
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Get log level as integer
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Configure on import
import logging
configure_structlog()

# Get logger
logger = structlog.get_logger()


class EventLogger:
    """Logger for critical trading events."""
    
    def __init__(self, events_file: Optional[Path] = None):
        """Initialize event logger.
        
        Args:
            events_file: Path to events file (defaults to logs/events.jsonl)
        """
        if events_file is None:
            events_file = settings.LOG_FILE_PATH.parent / "events.jsonl"
        
        self.events_file = events_file
        self.events_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log a critical event.
        
        Args:
            event_type: Type of event (entry, exit, forced_close, etc.)
            data: Event data
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **data
        }
        
        # Log to structlog
        logger.info(
            f"Event: {event_type}",
            event_type=event_type,
            **data
        )
        
        # Persist to file
        with open(self.events_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def log_entry(self, symbol: str, signal: int, entry_price: float, stop_loss: float, take_profit: float, position_size: float):
        """Log trade entry event."""
        self.log_event("entry", {
            "symbol": symbol,
            "signal": signal,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "position_size": position_size
        })
    
    def log_exit(self, symbol: str, exit_price: float, pnl: float, exit_reason: str):
        """Log trade exit event."""
        self.log_event("exit", {
            "symbol": symbol,
            "exit_price": exit_price,
            "pnl": pnl,
            "exit_reason": exit_reason
        })
    
    def log_forced_close(self, symbol: str, exit_price: float, pnl: float):
        """Log forced close event."""
        self.log_event("forced_close", {
            "symbol": symbol,
            "exit_price": exit_price,
            "pnl": pnl
        })
    
    def log_signal_generated(self, symbol: str, timeframe: str, strategy: str, signal: int, strength: float):
        """Log signal generation event."""
        self.log_event("signal_generated", {
            "symbol": symbol,
            "timeframe": timeframe,
            "strategy": strategy,
            "signal": signal,
            "strength": strength
        })
    
    def log_decision(self, symbol: str, decision_data: Dict[str, Any]):
        """Log daily decision event."""
        self.log_event("daily_decision", {
            "symbol": symbol,
            **decision_data
        })
    
    def read_events(self, event_type: Optional[str] = None, symbol: Optional[str] = None, limit: int = 100) -> list[Dict[str, Any]]:
        """Read events from log file.
        
        Args:
            event_type: Filter by event type
            symbol: Filter by symbol
            limit: Maximum events to return
            
        Returns:
            List of events
        """
        if not self.events_file.exists():
            return []
        
        events = []
        
        with open(self.events_file, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    # Apply filters
                    if event_type and event.get('event_type') != event_type:
                        continue
                    
                    if symbol and event.get('symbol') != symbol:
                        continue
                    
                    events.append(event)
                    
                    if len(events) >= limit:
                        break
                
                except json.JSONDecodeError:
                    continue
        
        return events[-limit:]  # Return last N events


# Global event logger
event_logger = EventLogger()

