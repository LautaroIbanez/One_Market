"""Health check script for One Market platform.

Validates:
- Storage integrity
- Data consistency
- Exchange connectivity
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.data.store import DataStore
from app.data.fetch import DataFetcher
from app.config.settings import settings
from app.utils.logging_config import setup_logging

logger = setup_logging()


def check_storage():
    """Check storage health."""
    logger.info("Checking storage...")
    
    store = DataStore()
    stored_symbols = store.list_stored_symbols()
    
    if not stored_symbols:
        logger.warning("  - No data stored yet")
        return True
    
    logger.info(f"  - Found {len(stored_symbols)} symbol/timeframe pairs")
    
    issues = 0
    for symbol, timeframe in stored_symbols:
        metadata = store.get_metadata(symbol, timeframe)
        if metadata:
            logger.info(f"  - {symbol} {timeframe}: {metadata.record_count} records, gaps={metadata.gap_count}")
            
            validation = store.validate_storage_consistency(symbol, timeframe)
            if not validation.is_valid:
                logger.warning(f"    ! Validation issues: {validation.validation_errors}")
                issues += 1
        else:
            logger.warning(f"  - {symbol} {timeframe}: metadata missing")
            issues += 1
    
    if issues == 0:
        logger.info("[OK] Storage healthy")
        return True
    else:
        logger.warning(f"[WARNING] Storage has {issues} issues")
        return False


def check_exchange_connectivity():
    """Check exchange connectivity."""
    logger.info("Checking exchange connectivity...")
    
    try:
        fetcher = DataFetcher(exchange_name=settings.EXCHANGE_NAME)
        
        timestamp = fetcher.get_latest_timestamp("BTC/USDT", "1h")
        
        if timestamp:
            from datetime import datetime
            logger.info(f"  - Exchange responsive: latest BTC/USDT 1h at {datetime.utcfromtimestamp(timestamp/1000)}")
            logger.info("[OK] Exchange connectivity OK")
            return True
        else:
            logger.warning("  - Could not fetch latest timestamp")
            return False
            
    except Exception as e:
        logger.error(f"  - Exchange connection failed: {e}")
        return False


def main():
    """Run health checks."""
    logger.info("=" * 60)
    logger.info("One Market Platform - Health Check")
    logger.info("=" * 60)
    
    checks = {"Storage": check_storage(), "Exchange": check_exchange_connectivity()}
    
    logger.info("=" * 60)
    
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    if passed == total:
        logger.info(f"[SUCCESS] All checks passed ({passed}/{total})")
        sys.exit(0)
    else:
        logger.warning(f"[WARNING] Some checks failed ({passed}/{total} passed)")
        sys.exit(1)


if __name__ == "__main__":
    main()

