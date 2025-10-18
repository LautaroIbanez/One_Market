"""Example: Read stored OHLCV data with filtering.

This example demonstrates how to:
1. List stored symbols
2. Read data with timestamp filtering
3. Access metadata
"""
import logging
from datetime import datetime, timedelta
from app.data.store import DataStore
from app.config.settings import settings

logging.basicConfig(level=logging.INFO, format=settings.LOG_FORMAT)
logger = logging.getLogger(__name__)


def main():
    store = DataStore()
    
    stored_symbols = store.list_stored_symbols()
    logger.info(f"Stored symbols: {stored_symbols}")
    
    if not stored_symbols:
        logger.warning("No data stored yet. Run example_fetch_data.py first.")
        return
    
    symbol, timeframe = stored_symbols[0]
    logger.info(f"Reading data for {symbol} {timeframe}")
    
    metadata = store.get_metadata(symbol, timeframe)
    if metadata:
        logger.info(f"Metadata: {metadata.record_count} records")
        logger.info(f"Range: {datetime.utcfromtimestamp(metadata.first_timestamp/1000)} to {datetime.utcfromtimestamp(metadata.last_timestamp/1000)}")
        logger.info(f"Has gaps: {metadata.has_gaps} ({metadata.gap_count} gaps)")
    
    all_bars = store.read_bars(symbol, timeframe)
    logger.info(f"Read {len(all_bars)} total bars")
    
    if all_bars:
        last_24h_start = all_bars[-1].timestamp - (24 * 60 * 60 * 1000)
        recent_bars = store.read_bars(symbol, timeframe, start_timestamp=last_24h_start)
        logger.info(f"Last 24 hours: {len(recent_bars)} bars")
        
        if recent_bars:
            logger.info(f"Latest bar: timestamp={datetime.utcfromtimestamp(recent_bars[-1].timestamp/1000)}, close={recent_bars[-1].close}")
    
    validation = store.validate_storage_consistency(symbol, timeframe)
    logger.info(f"Storage consistency: valid={validation.is_valid}, gaps={validation.gap_count}, duplicates={validation.duplicate_count}")


if __name__ == "__main__":
    main()


