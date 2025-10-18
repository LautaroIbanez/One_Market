"""Configuration settings for One Market platform."""
import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    STORAGE_PATH: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "storage")
    
    # Exchange configuration
    EXCHANGE_NAME: str = Field(default="binance", description="Default exchange")
    EXCHANGE_API_KEY: str = Field(default="", description="Exchange API key")
    EXCHANGE_API_SECRET: str = Field(default="", description="Exchange API secret")
    EXCHANGE_TESTNET: bool = Field(default=False, description="Use testnet")
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=1200, description="Max requests per minute")
    RATE_LIMIT_COOLDOWN: float = Field(default=0.1, description="Cooldown between requests (seconds)")
    
    # Data fetching
    DEFAULT_FETCH_LIMIT: int = Field(default=1000, ge=1, le=1000, description="Default fetch limit")
    MAX_RETRY_ATTEMPTS: int = Field(default=3, ge=1, description="Max retry attempts for failed requests")
    RETRY_BACKOFF_FACTOR: float = Field(default=2.0, description="Exponential backoff factor")
    
    # Data validation
    ALLOW_GAPS: bool = Field(default=True, description="Allow temporal gaps in data")
    MAX_GAP_TOLERANCE: int = Field(default=2, description="Max allowed gap multiplier for timeframe")
    DUPLICATE_HANDLING: Literal["error", "skip", "overwrite"] = Field(default="skip", description="How to handle duplicates")
    
    # Storage
    PARQUET_COMPRESSION: str = Field(default="snappy", description="Parquet compression codec")
    SCHEMA_VERSION: str = Field(default="1.0", description="Current schema version")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Performance
    PERFORMANCE_TARGET_MS: int = Field(default=1000, description="Target response time for signal generation (ms)")
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_RELOAD: bool = Field(default=False, description="Auto-reload on code changes")
    API_WORKERS: int = Field(default=1, description="Number of worker processes")
    
    # CORS
    CORS_ORIGINS: list = Field(default=["*"], description="Allowed CORS origins")
    
    # Trading Configuration
    DEFAULT_SYMBOLS: list = Field(default=["BTC/USDT", "ETH/USDT"], description="Default trading symbols")
    DEFAULT_TIMEFRAMES: list = Field(default=["1h", "4h", "1d"], description="Default timeframes")
    
    # Risk Management
    DEFAULT_RISK_PCT: float = Field(default=0.02, description="Default risk per trade (2%)")
    MAX_RISK_PCT: float = Field(default=0.05, description="Maximum risk per trade (5%)")
    INITIAL_CAPITAL: float = Field(default=100000.0, description="Initial capital")
    
    # Trading Rules
    ONE_TRADE_PER_DAY: bool = Field(default=True, description="Enforce one trade per day")
    SKIP_WINDOW_B_IF_A_EXECUTED: bool = Field(default=True, description="Skip window B if A traded")
    USE_TRADING_WINDOWS: bool = Field(default=True, description="Use trading windows")
    USE_FORCED_CLOSE: bool = Field(default=True, description="Use forced close")
    
    # Trading Windows (local time UTC-3)
    WINDOW_A_START: str = Field(default="09:00", description="Window A start (HH:MM)")
    WINDOW_A_END: str = Field(default="12:30", description="Window A end (HH:MM)")
    WINDOW_B_START: str = Field(default="14:00", description="Window B start (HH:MM)")
    WINDOW_B_END: str = Field(default="17:00", description="Window B end (HH:MM)")
    FORCED_CLOSE_TIME: str = Field(default="16:45", description="Forced close time (HH:MM)")
    
    # Entry Band Configuration
    ENTRY_BAND_BETA: float = Field(default=0.003, description="Entry band beta (0.3%)")
    USE_VWAP_ENTRY: bool = Field(default=True, description="Use VWAP for entry mid")
    
    # TP/SL Configuration
    TPSL_METHOD: Literal["atr", "swing", "hybrid"] = Field(default="atr", description="TP/SL method")
    ATR_PERIOD: int = Field(default=14, description="ATR period")
    ATR_MULTIPLIER_SL: float = Field(default=2.0, description="ATR multiplier for SL")
    ATR_MULTIPLIER_TP: float = Field(default=3.0, description="ATR multiplier for TP")
    MIN_RR_RATIO: float = Field(default=1.5, description="Minimum R/R ratio")
    
    # Commission and Slippage
    COMMISSION_SPOT: float = Field(default=0.001, description="Spot commission (0.1%)")
    COMMISSION_FUTURES: float = Field(default=0.0004, description="Futures commission (0.04%)")
    SLIPPAGE: float = Field(default=0.0005, description="Slippage (0.05%)")
    
    # Scheduler Configuration
    SCHEDULER_ENABLED: bool = Field(default=False, description="Enable job scheduler")
    DATA_UPDATE_INTERVAL: int = Field(default=5, description="Data update interval (minutes)")
    BACKTEST_SCHEDULE: str = Field(default="0 2 * * *", description="Backtest schedule (cron)")
    
    # Paper Trading
    PAPER_TRADING_ENABLED: bool = Field(default=True, description="Enable paper trading")
    PAPER_TRADING_DB: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "storage" / "paper_trading.db")
    
    # Logging (Extended)
    LOG_TO_FILE: bool = Field(default=True, description="Log to file")
    LOG_FILE_PATH: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs" / "one_market.log")
    LOG_ROTATION: str = Field(default="100 MB", description="Log rotation size")
    LOG_RETENTION: str = Field(default="30 days", description="Log retention period")
    STRUCTURED_LOGGING: bool = Field(default=True, description="Use structured logging (JSON)")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Timeframe mappings to milliseconds
TIMEFRAME_TO_MS = {
    "1m": 60 * 1000,
    "3m": 3 * 60 * 1000,
    "5m": 5 * 60 * 1000,
    "15m": 15 * 60 * 1000,
    "30m": 30 * 60 * 1000,
    "1h": 60 * 60 * 1000,
    "2h": 2 * 60 * 60 * 1000,
    "4h": 4 * 60 * 60 * 1000,
    "6h": 6 * 60 * 60 * 1000,
    "8h": 8 * 60 * 60 * 1000,
    "12h": 12 * 60 * 60 * 1000,
    "1d": 24 * 60 * 60 * 1000,
    "3d": 3 * 24 * 60 * 60 * 1000,
    "1w": 7 * 24 * 60 * 60 * 1000,
}


def get_timeframe_ms(timeframe: str) -> int:
    """Get milliseconds for a timeframe string."""
    if timeframe not in TIMEFRAME_TO_MS:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return TIMEFRAME_TO_MS[timeframe]


