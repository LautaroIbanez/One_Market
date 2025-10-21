"""Backfill historical data to meet TIMEFRAME_CANDLE_TARGETS.

This script ensures each timeframe has sufficient data for backtesting
by fetching historical data and filling gaps.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.fetch import DataFetcher
from app.data.store import DataStore
from app.config.settings import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataBackfiller:
    """Backfills historical data for all timeframes."""
    
    def __init__(self):
        """Initialize backfiller."""
        self.fetcher = DataFetcher(
            exchange_name=settings.EXCHANGE_NAME,
            api_key=settings.EXCHANGE_API_KEY,
            api_secret=settings.EXCHANGE_API_SECRET,
            testnet=False
        )
        self.store = DataStore()
    
    def get_data_status(self, symbol: str, timeframe: str) -> Dict:
        """Get current data status for a symbol/timeframe."""
        try:
            bars = self.store.read_bars(symbol, timeframe)
            target = settings.TIMEFRAME_CANDLE_TARGETS.get(timeframe, 100)
            
            if not bars:
                return {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'current_bars': 0,
                    'target_bars': target,
                    'percentage': 0.0,
                    'status': 'EMPTY',
                    'oldest_date': None,
                    'newest_date': None
                }
            
            oldest = min(bar.timestamp for bar in bars)
            newest = max(bar.timestamp for bar in bars)
            
            percentage = (len(bars) / target * 100) if target > 0 else 0
            
            if len(bars) < target:
                status = 'INSUFFICIENT'
            else:
                status = 'OK'
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'current_bars': len(bars),
                'target_bars': target,
                'percentage': percentage,
                'status': status,
                'oldest_date': datetime.fromtimestamp(oldest / 1000, tz=timezone.utc),
                'newest_date': datetime.fromtimestamp(newest / 1000, tz=timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error checking status for {symbol} {timeframe}: {e}")
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'current_bars': 0,
                'target_bars': settings.TIMEFRAME_CANDLE_TARGETS.get(timeframe, 100),
                'percentage': 0.0,
                'status': 'ERROR',
                'oldest_date': None,
                'newest_date': None,
                'error': str(e)
            }
    
    def backfill_timeframe(self, symbol: str, timeframe: str, force: bool = False) -> Dict:
        """Backfill data for a specific timeframe."""
        try:
            logger.info(f"Backfilling {symbol} {timeframe}...")
            
            # Get current status
            status = self.get_data_status(symbol, timeframe)
            
            if status['status'] == 'OK' and not force:
                logger.info(f"✅ {symbol} {timeframe} already has sufficient data ({status['current_bars']}/{status['target_bars']})")
                return status
            
            # Calculate how much data to fetch
            target_bars = status['target_bars']
            current_bars = status['current_bars']
            missing_bars = max(0, target_bars - current_bars)
            
            if missing_bars == 0 and not force:
                return status
            
            logger.info(f"📊 {symbol} {timeframe}: {current_bars}/{target_bars} bars ({status['percentage']:.1f}%)")
            logger.info(f"🔄 Fetching {missing_bars} missing bars...")
            
            # Calculate start time
            from app.config.settings import get_timeframe_ms
            timeframe_ms = get_timeframe_ms(timeframe)
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            
            # Fetch data to cover target bars
            bars_to_fetch = target_bars + 50  # Add buffer for gaps
            since_ms = now_ms - (bars_to_fetch * timeframe_ms)
            
            # Fetch incrementally
            bars = self.fetcher.fetch_incremental(
                symbol=symbol,
                timeframe=timeframe,
                since=since_ms,
                until=now_ms,
                market_type="spot"
            )
            
            if not bars:
                logger.warning(f"⚠️ No data fetched for {symbol} {timeframe}")
                return status
            
            # Write to storage
            self.store.write_bars(bars, mode="append")
            
            # Get updated status
            updated_status = self.get_data_status(symbol, timeframe)
            
            logger.info(f"✅ Backfill complete: {updated_status['current_bars']}/{updated_status['target_bars']} bars ({updated_status['percentage']:.1f}%)")
            
            return updated_status
            
        except Exception as e:
            logger.error(f"❌ Error backfilling {symbol} {timeframe}: {e}")
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def backfill_all_timeframes(self, symbol: str, force: bool = False) -> List[Dict]:
        """Backfill all target timeframes for a symbol."""
        results = []
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting backfill for {symbol}")
        logger.info(f"{'='*60}\n")
        
        for timeframe in settings.TARGET_TIMEFRAMES:
            result = self.backfill_timeframe(symbol, timeframe, force)
            results.append(result)
            
            # Log summary
            if result['status'] == 'OK':
                logger.info(f"✅ {timeframe}: {result['current_bars']}/{result['target_bars']} bars")
            elif result['status'] == 'INSUFFICIENT':
                logger.warning(f"⚠️ {timeframe}: {result['current_bars']}/{result['target_bars']} bars ({result['percentage']:.1f}%)")
            else:
                logger.error(f"❌ {timeframe}: {result['status']}")
        
        return results
    
    def generate_backfill_report(self, results: List[Dict]) -> str:
        """Generate a report of backfill results."""
        report_lines = []
        report_lines.append("\n" + "="*60)
        report_lines.append("BACKFILL REPORT")
        report_lines.append("="*60 + "\n")
        
        for result in results:
            symbol = result['symbol']
            timeframe = result['timeframe']
            status = result['status']
            
            if status == 'OK':
                icon = "✅"
            elif status == 'INSUFFICIENT':
                icon = "⚠️"
            else:
                icon = "❌"
            
            report_lines.append(f"{icon} {symbol} {timeframe}:")
            
            if 'current_bars' in result:
                report_lines.append(f"   Bars: {result['current_bars']}/{result['target_bars']} ({result['percentage']:.1f}%)")
            
            report_lines.append(f"   Status: {status}")
            
            if result.get('oldest_date'):
                report_lines.append(f"   Range: {result['oldest_date'].strftime('%Y-%m-%d')} to {result['newest_date'].strftime('%Y-%m-%d')}")
            
            if result.get('error'):
                report_lines.append(f"   Error: {result['error']}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)


def main():
    """Main backfill function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backfill historical data')
    parser.add_argument('--symbol', default='BTC/USDT', help='Trading symbol')
    parser.add_argument('--force', action='store_true', help='Force refetch even if sufficient data exists')
    parser.add_argument('--timeframe', help='Specific timeframe to backfill (optional)')
    
    args = parser.parse_args()
    
    backfiller = DataBackfiller()
    
    if args.timeframe:
        # Backfill specific timeframe
        result = backfiller.backfill_timeframe(args.symbol, args.timeframe, args.force)
        report = backfiller.generate_backfill_report([result])
    else:
        # Backfill all timeframes
        results = backfiller.backfill_all_timeframes(args.symbol, args.force)
        report = backfiller.generate_backfill_report(results)
    
    print(report)
    
    # Save report to file
    report_file = Path(__file__).parent.parent / "logs" / f"backfill_{args.symbol.replace('/', '-')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report, encoding='utf-8')
    
    logger.info(f"Report saved to: {report_file}")


if __name__ == "__main__":
    main()

