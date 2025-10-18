"""Logging configuration for One Market platform."""
import logging
import sys
from pathlib import Path
from app.config.settings import settings


def setup_logging(log_file: str = None):
    """Setup logging configuration for the application.
    
    Args:
        log_file: Optional log file path. If None, logs only to console.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(level=log_level, format=settings.LOG_FORMAT, handlers=handlers, force=True)
    
    logging.getLogger("ccxt").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level {settings.LOG_LEVEL}")
    
    return logger


