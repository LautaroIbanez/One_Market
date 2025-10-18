"""Setup script for One Market platform.

Run this script to perform initial setup:
- Create storage directories
- Validate configuration
- Run health checks
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config.settings import settings
from app.utils.logging_config import setup_logging

logger = setup_logging()


def create_directories():
    """Create necessary directories."""
    logger.info("Creating storage directories...")
    settings.STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    (settings.PROJECT_ROOT / "logs").mkdir(parents=True, exist_ok=True)
    logger.info("[OK] Directories created")


def validate_config():
    """Validate configuration."""
    logger.info("Validating configuration...")
    
    logger.info(f"  - Storage path: {settings.STORAGE_PATH}")
    logger.info(f"  - Exchange: {settings.EXCHANGE_NAME}")
    logger.info(f"  - Rate limit: {settings.RATE_LIMIT_REQUESTS} req/min")
    logger.info(f"  - Compression: {settings.PARQUET_COMPRESSION}")
    
    if settings.EXCHANGE_API_KEY:
        logger.info("  - API credentials: configured")
    else:
        logger.warning("  - API credentials: not configured (public access only)")
    
    logger.info("[OK] Configuration valid")


def test_dependencies():
    """Test critical dependencies."""
    logger.info("Testing dependencies...")
    
    try:
        import ccxt
        logger.info(f"  - ccxt: {ccxt.__version__}")
    except ImportError:
        logger.error("  - ccxt: NOT FOUND")
        return False
    
    try:
        import pyarrow
        logger.info(f"  - pyarrow: {pyarrow.__version__}")
    except ImportError:
        logger.error("  - pyarrow: NOT FOUND")
        return False
    
    try:
        import fastapi
        logger.info(f"  - fastapi: {fastapi.__version__}")
    except ImportError:
        logger.error("  - fastapi: NOT FOUND")
        return False
    
    logger.info("[OK] Dependencies OK")
    return True


def main():
    """Run setup."""
    logger.info("=" * 60)
    logger.info("One Market Platform - Setup")
    logger.info("=" * 60)
    
    create_directories()
    validate_config()
    
    if not test_dependencies():
        logger.error("Setup failed: missing dependencies")
        logger.info("Run: pip install -r requirements.txt")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("[SUCCESS] Setup completed successfully!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Configure .env file (copy from env.example)")
    logger.info("  2. Run example: python examples/example_fetch_data.py")
    logger.info("  3. Run tests: pytest")


if __name__ == "__main__":
    main()

