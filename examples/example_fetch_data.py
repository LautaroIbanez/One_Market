"""Example: Fetch and store OHLCV data incrementally.

This example demonstrates how to:
1. Fetch OHLCV data from an exchange
2. Validate the data
3. Store it in partitioned parquet files
"""
import logging
from datetime import datetime, timedelta
from app.data.fetch import DataFetcher
from app.data.store import DataStore
from app.config.settings import settings

logging.basicConfig(level=logging.INFO, format=settings.LOG_FORMAT)
logger = logging.getLogger(__name__)


def main():
    symbol = "BTC/USDT"
    timeframe = "1h"
    days_back = 7
    
    since = int((datetime.utcnow() - timedelta(days=days_back)).timestamp() * 1000)
    
    logger.info(f"Fetching {symbol} {timeframe} data from {datetime.utcfromtimestamp(since/1000)}")
    
    fetcher = DataFetcher(exchange_name="binance")
    
    bars = fetcher.fetch_incremental(symbol=symbol, timeframe=timeframe, since=since)
    
    logger.info(f"Fetched {len(bars)} bars")
    
    validation = fetcher.validate_data(bars)
    logger.info(f"Validation result: valid={validation.is_valid}, gaps={validation.gap_count}, duplicates={validation.duplicate_count}")
    
    if validation.validation_errors:
        for error in validation.validation_errors:
            logger.warning(f"Validation error: {error}")
    
    store = DataStore()
    stats = store.write_bars(bars)
    
    logger.info(f"Stored data across {len(stats)} partitions:")
    for partition, count in stats.items():
        logger.info(f"  {partition}: {count} bars")
    
    metadata = store.get_metadata(symbol, timeframe)
    if metadata:
        logger.info(f"Dataset metadata: {metadata.record_count} records, range: {datetime.utcfromtimestamp(metadata.first_timestamp/1000)} to {datetime.utcfromtimestamp(metadata.last_timestamp/1000)}")


if __name__ == "__main__":
    main()


