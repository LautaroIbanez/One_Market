"""Example: Analyze stored data across timeframes.

This example demonstrates how to:
1. Read data from different timeframes
2. Calculate basic statistics
3. Compare prices across timeframes
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.store import DataStore
from app.config.settings import settings

logging.basicConfig(level=logging.INFO, format=settings.LOG_FORMAT)
logger = logging.getLogger(__name__)


def main():
    store = DataStore()
    
    stored = store.list_stored_symbols()
    logger.info(f"Analyzing {len(stored)} stored datasets\n")
    
    for symbol, timeframe in sorted(stored, key=lambda x: (x[0], ['15m', '1h', '4h', '1d'].index(x[1]) if x[1] in ['15m', '1h', '4h', '1d'] else 99)):
        logger.info(f"=" * 70)
        logger.info(f"Symbol: {symbol} | Timeframe: {timeframe}")
        logger.info(f"=" * 70)
        
        bars = store.read_bars(symbol, timeframe)
        
        if not bars:
            logger.warning("No bars found")
            continue
        
        prices = [b.close for b in bars]
        volumes = [b.volume for b in bars]
        
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        first_price = bars[0].close
        last_price = bars[-1].close
        change = ((last_price - first_price) / first_price) * 100
        
        total_volume = sum(volumes)
        avg_volume = total_volume / len(volumes)
        
        first_time = datetime.utcfromtimestamp(bars[0].timestamp / 1000)
        last_time = datetime.utcfromtimestamp(bars[-1].timestamp / 1000)
        
        logger.info(f"Total bars: {len(bars)}")
        logger.info(f"Period: {first_time} to {last_time}")
        logger.info(f"")
        logger.info(f"Price Statistics:")
        logger.info(f"  First:   ${first_price:>12,.2f}")
        logger.info(f"  Last:    ${last_price:>12,.2f}")
        logger.info(f"  Change:  {change:>12.2f}%")
        logger.info(f"  Min:     ${min_price:>12,.2f}")
        logger.info(f"  Max:     ${max_price:>12,.2f}")
        logger.info(f"  Average: ${avg_price:>12,.2f}")
        logger.info(f"  Range:   ${max_price - min_price:>12,.2f}")
        logger.info(f"")
        logger.info(f"Volume Statistics:")
        logger.info(f"  Total:   {total_volume:>15,.2f}")
        logger.info(f"  Average: {avg_volume:>15,.2f}")
        logger.info(f"  Max:     {max(volumes):>15,.2f}")
        logger.info(f"  Min:     {min(volumes):>15,.2f}")
        logger.info("")
    
    logger.info(f"=" * 70)
    logger.info("Analysis complete!")
    logger.info(f"=" * 70)


if __name__ == "__main__":
    main()


