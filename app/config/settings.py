"""Configuration settings for One Market platform."""
import os
from pathlib import Path
from typing import Literal, Dict
from pydantic_settings import BaseSettings
from pydantic import Field, BaseModel


# ============================================================
# RISK PROFILES (NEW v2.0)
# ============================================================

class RiskProfile(BaseModel):
    """Risk profile configuration for different capital levels."""
    
    name: str
    display_name: str
    description: str
    
    # Capital constraints
    min_capital: float
    max_capital: float
    
    # Risk parameters
    default_risk_pct: float
    max_risk_pct: float
    min_position_size_usd: float
    
    # Fee/slippage
    commission_pct: float
    slippage_pct: float
    
    # Position sizing
    max_position_pct: float  # Max % of capital per position
    max_leverage: float
    
    # TP/SL defaults
    default_atr_multiplier_sl: float
    default_atr_multiplier_tp: float


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


# ============================================================
# PREDEFINED RISK PROFILES (NEW v2.0)
# ============================================================

RISK_PROFILES: Dict[str, RiskProfile] = {
    "starter_1k": RiskProfile(
        name="starter_1k",
        display_name="🌱 Starter - $1K",
        description="Para capital inicial de $1,000 - Conservador y educativo",
        min_capital=500.0,
        max_capital=2000.0,
        default_risk_pct=0.015,  # 1.5%
        max_risk_pct=0.02,  # 2.0%
        min_position_size_usd=10.0,
        commission_pct=0.001,  # 0.1% Binance spot
        slippage_pct=0.0005,
        max_position_pct=0.20,  # Max 20% en una posición
        max_leverage=1.0,  # Sin leverage
        default_atr_multiplier_sl=2.5,
        default_atr_multiplier_tp=4.0
    ),
    "intermediate_5k": RiskProfile(
        name="intermediate_5k",
        display_name="📈 Intermediate - $5K",
        description="Para capital de $5,000 - Balance entre crecimiento y protección",
        min_capital=3000.0,
        max_capital=10000.0,
        default_risk_pct=0.02,  # 2.0%
        max_risk_pct=0.03,  # 3.0%
        min_position_size_usd=50.0,
        commission_pct=0.001,
        slippage_pct=0.0005,
        max_position_pct=0.25,
        max_leverage=1.0,
        default_atr_multiplier_sl=2.0,
        default_atr_multiplier_tp=3.5
    ),
    "advanced_25k": RiskProfile(
        name="advanced_25k",
        display_name="💎 Advanced - $25K",
        description="Para capital de $25,000+ - Activo con gestión profesional",
        min_capital=15000.0,
        max_capital=100000.0,
        default_risk_pct=0.02,  # 2.0%
        max_risk_pct=0.04,  # 4.0%
        min_position_size_usd=200.0,
        commission_pct=0.001,
        slippage_pct=0.0003,  # Mejor ejecución
        max_position_pct=0.30,
        max_leverage=1.0,
        default_atr_multiplier_sl=1.8,
        default_atr_multiplier_tp=3.0
    ),
    "pro_100k": RiskProfile(
        name="pro_100k",
        display_name="🏆 Professional - $100K+",
        description="Para capital profesional de $100,000+ - Máxima flexibilidad",
        min_capital=75000.0,
        max_capital=1000000.0,
        default_risk_pct=0.02,  # 2.0%
        max_risk_pct=0.05,  # 5.0%
        min_position_size_usd=500.0,
        commission_pct=0.0008,  # VIP tier
        slippage_pct=0.0002,
        max_position_pct=0.35,
        max_leverage=2.0,  # Puede usar leverage
        default_atr_multiplier_sl=1.5,
        default_atr_multiplier_tp=2.5
    )
}


def get_risk_profile_for_capital(capital: float) -> RiskProfile:
    """Get appropriate risk profile based on capital amount."""
    if capital < 2000:
        return RISK_PROFILES["starter_1k"]
    elif capital < 10000:
        return RISK_PROFILES["intermediate_5k"]
    elif capital < 100000:
        return RISK_PROFILES["advanced_25k"]
    else:
        return RISK_PROFILES["pro_100k"]



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


