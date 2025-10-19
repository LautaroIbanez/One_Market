"""Example: Fetch data for multiple timeframes.

This example demonstrates how to:
1. Fetch the same symbol across different timeframes
2. Store each timeframe separately
3. Compare data across timeframes
"""
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.fetch import DataFetcher
from app.data.store import DataStore
from app.config.settings import settings

logging.basicConfig(level=logging.INFO, format=settings.LOG_FORMAT)
logger = logging.getLogger(__name__)


def main():
    symbol = "BTC/USDT"
    timeframes = ["15m", "1h", "4h", "1d"]
    days_back = 7
    
    since = int((datetime.utcnow() - timedelta(days=days_back)).timestamp() * 1000)
    
    logger.info(f"=" * 70)
    logger.info(f"Fetching {symbol} data across multiple timeframes")
    logger.info(f"Timeframes: {', '.join(timeframes)}")
    logger.info(f"Period: Last {days_back} days")
    logger.info(f"=" * 70)
    
    fetcher = DataFetcher(exchange_name="binance")
    store = DataStore()
    
    results = {}
    
    for tf in timeframes:
        logger.info(f"\n--- Processing timeframe: {tf} ---")
        
        try:
            bars = fetcher.fetch_incremental(symbol=symbol, timeframe=tf, since=since)
            logger.info(f"Fetched {len(bars)} bars for {tf}")
            
            validation = fetcher.validate_data(bars)
            logger.info(f"Validation: valid={validation.is_valid}, gaps={validation.gap_count}, duplicates={validation.duplicate_count}")
            
            if bars:
                stats = store.write_bars(bars)
                logger.info(f"Stored across {len(stats)} partitions")
                
                metadata = store.get_metadata(symbol, tf)
                if metadata:
                    first_time = datetime.utcfromtimestamp(metadata.first_timestamp / 1000)
                    last_time = datetime.utcfromtimestamp(metadata.last_timestamp / 1000)
                    logger.info(f"Range: {first_time} to {last_time}")
                    logger.info(f"Latest close price: ${bars[-1].close:,.2f}")
                
                results[tf] = {"bars": len(bars), "first": bars[0].timestamp, "last": bars[-1].timestamp, "close": bars[-1].close}
            else:
                logger.warning(f"No data fetched for {tf}")
                results[tf] = {"bars": 0}
                
        except Exception as e:
            logger.error(f"Error processing {tf}: {e}")
            results[tf] = {"error": str(e)}
    
    logger.info(f"\n" + "=" * 70)
    logger.info("SUMMARY - Data fetched across timeframes:")
    logger.info("=" * 70)
    
    for tf, data in results.items():
        if "error" in data:
            logger.error(f"{tf:>6}: ERROR - {data['error']}")
        elif data["bars"] > 0:
            first_time = datetime.utcfromtimestamp(data["first"] / 1000).strftime("%Y-%m-%d %H:%M")
            last_time = datetime.utcfromtimestamp(data["last"] / 1000).strftime("%Y-%m-%d %H:%M")
            logger.info(f"{tf:>6}: {data['bars']:>4} bars | {first_time} -> {last_time} | Close: ${data['close']:,.2f}")
        else:
            logger.warning(f"{tf:>6}: No data")
    
    logger.info("=" * 70)
    
    stored_symbols = store.list_stored_symbols()
    logger.info(f"\nTotal stored symbol/timeframe pairs: {len(stored_symbols)}")
    for sym, tf in sorted(stored_symbols):
        logger.info(f"  - {sym} @ {tf}")


if __name__ == "__main__":
    main()



