#!/usr/bin/env python3
"""Reusable data synchronization script for OHLCV updates.

This script can be called with parameters to update specific symbols/timeframes
and is designed to be used in automated workflows like cron jobs.
"""

import argparse
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import List, Optional
import logging

from app.data.fetch import DataFetcher
from app.data.store import DataStore
from app.data.last_update import record_data_update
from app.config.settings import settings
import sqlite3


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def _invalidate_recommendation_cache(symbol: str, timeframe: str):
    """Invalidate recommendation cache for a specific symbol/timeframe."""
    logger = logging.getLogger(__name__)
    
    try:
        store = DataStore()
        db_path = store.base_path / "recommendations.db"
        
        if db_path.exists():
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Delete recommendations for this symbol
                cursor.execute(
                    "DELETE FROM recommendations WHERE symbol = ?",
                    (symbol,)
                )
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Invalidated {deleted_count} cached recommendations for {symbol}")
        else:
            logger.info("No recommendation database found to invalidate")
            
    except Exception as e:
        logger.error(f"Error invalidating recommendation cache: {e}")


def sync_data(
    symbol: str,
    timeframe: str,
    days_back: int = 7,
    dry_run: bool = False,
    verbose: bool = False
) -> dict:
    """Synchronize data for a specific symbol/timeframe.
    
    Args:
        symbol: Trading symbol (e.g., 'BTC/USDT')
        timeframe: Timeframe (e.g., '1h', '4h', '1d')
        days_back: Number of days to fetch back
        dry_run: If True, don't actually store data
        verbose: Enable verbose logging
        
    Returns:
        Dictionary with sync results
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Current time
        now_utc = datetime.now(ZoneInfo("UTC"))
        current_timestamp = int(now_utc.timestamp() * 1000)
        
        # Calculate since timestamp
        since_timestamp = current_timestamp - (days_back * 24 * 60 * 60 * 1000)
        
        logger.info(f"Syncing {symbol} {timeframe} from {days_back} days ago")
        logger.debug(f"Since: {datetime.fromtimestamp(since_timestamp/1000, tz=ZoneInfo('UTC'))}")
        logger.debug(f"Until: {datetime.fromtimestamp(current_timestamp/1000, tz=ZoneInfo('UTC'))}")
        
        # Initialize fetcher and store
        fetcher = DataFetcher()
        store = DataStore()
        
        # Fetch data
        bars = fetcher.fetch_incremental(
            symbol=symbol,
            timeframe=timeframe,
            since=since_timestamp,
            until=current_timestamp
        )
        
        logger.info(f"Fetched {len(bars)} bars")
        
        result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'bars_fetched': len(bars),
            'bars_stored': 0,
            'latest_timestamp': None,
            'latest_price': None,
            'success': True,
            'error': None
        }
        
        if bars:
            if not dry_run:
                # Store data
                store.write_bars(bars)
                logger.info(f"Stored {len(bars)} bars")
                result['bars_stored'] = len(bars)
            
            # Get latest data info
            latest_bar = bars[-1]
            latest_utc = datetime.fromtimestamp(latest_bar.timestamp / 1000, tz=ZoneInfo("UTC"))
            
            result['latest_timestamp'] = latest_bar.timestamp
            result['latest_price'] = latest_bar.close
            
            # Record the update
            record_data_update(
                symbol=symbol,
                timeframe=timeframe,
                bars_count=len(bars),
                latest_timestamp=latest_bar.timestamp,
                latest_price=latest_bar.close,
                success=True
            )
            
            # Invalidate recommendation cache for this symbol/timeframe
            _invalidate_recommendation_cache(symbol, timeframe)
            
            # Check if data is recent
            time_diff = now_utc - latest_utc
            if time_diff.total_seconds() < 3600:  # Less than 1 hour old
                logger.info(f"Data is recent ({time_diff})")
                result['data_freshness'] = 'recent'
            else:
                logger.warning(f"Data is old ({time_diff})")
                result['data_freshness'] = 'old'
            
            logger.info(f"Latest: {latest_utc} - Price: ${latest_bar.close:,.2f}")
        else:
            # Record failed update
            record_data_update(
                symbol=symbol,
                timeframe=timeframe,
                success=False,
                error="No data fetched"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error syncing {symbol} {timeframe}: {e}")
        
        # Record failed update
        record_data_update(
            symbol=symbol,
            timeframe=timeframe,
            success=False,
            error=str(e)
        )
        
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'bars_fetched': 0,
            'bars_stored': 0,
            'latest_timestamp': None,
            'latest_price': None,
            'success': False,
            'error': str(e)
        }


def sync_multiple(
    symbols: List[str],
    timeframes: List[str],
    days_back: int = 7,
    dry_run: bool = False,
    verbose: bool = False
) -> List[dict]:
    """Synchronize data for multiple symbols/timeframes.
    
    Args:
        symbols: List of trading symbols
        timeframes: List of timeframes
        days_back: Number of days to fetch back
        dry_run: If True, don't actually store data
        verbose: Enable verbose logging
        
    Returns:
        List of sync results
    """
    logger = logging.getLogger(__name__)
    results = []
    
    total_combinations = len(symbols) * len(timeframes)
    logger.info(f"Syncing {total_combinations} symbol/timeframe combinations")
    
    for symbol in symbols:
        for timeframe in timeframes:
            logger.info(f"Processing {symbol} {timeframe}")
            result = sync_data(symbol, timeframe, days_back, dry_run, verbose)
            results.append(result)
            
            if not result['success']:
                logger.error(f"Failed to sync {symbol} {timeframe}: {result['error']}")
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    total_bars = sum(r['bars_stored'] for r in results)
    
    logger.info(f"Sync complete: {successful} successful, {failed} failed")
    logger.info(f"Total bars stored: {total_bars}")
    
    return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Synchronize OHLCV data')
    parser.add_argument('--symbol', '-s', default='BTC/USDT', 
                       help='Trading symbol (default: BTC/USDT)')
    parser.add_argument('--timeframe', '-t', default='1h',
                       help='Timeframe (default: 1h)')
    parser.add_argument('--days', '-d', type=int, default=7,
                       help='Days to fetch back (default: 7)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Don\'t actually store data')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--batch', action='store_true',
                       help='Sync multiple symbols/timeframes')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    if args.batch:
        # Batch mode - sync multiple combinations
        symbols = ['BTC/USDT', 'ETH/USDT']  # Add more as needed
        timeframes = ['1h', '4h', '1d']
        results = sync_multiple(symbols, timeframes, args.days, args.dry_run, args.verbose)
        
        # Exit with error code if any failed
        if any(not r['success'] for r in results):
            sys.exit(1)
    else:
        # Single mode
        result = sync_data(args.symbol, args.timeframe, args.days, args.dry_run, args.verbose)
        
        if not result['success']:
            logger.error(f"Sync failed: {result['error']}")
            sys.exit(1)
        
        logger.info("Sync completed successfully")


if __name__ == "__main__":
    main()
