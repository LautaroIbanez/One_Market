"""Update data job.

This job runs to update market data from exchanges.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import traceback

from app.data import DataFetcher, DataStore
from app.config.settings import settings

logger = logging.getLogger(__name__)


class UpdateDataJob:
    """Update data job."""
    
    def __init__(self):
        """Initialize job."""
        self.last_run = None
        self.last_success = None
        self.last_error = None
        
        logger.info("UpdateDataJob initialized")
    
    async def run(self) -> Dict[str, Any]:
        """Run the update data job.
        
        Returns:
            Job execution result
        """
        self.last_run = datetime.now(timezone.utc)
        
        try:
            logger.info("Starting update data job")
            
            # Initialize services
            fetcher = DataFetcher()
            store = DataStore()
            
            # Get symbols and timeframes to update
            symbols = getattr(settings, 'SYMBOLS', ["BTC/USDT", "ETH/USDT"])
            timeframes = getattr(settings, 'TARGET_TIMEFRAMES', ["15m", "1h", "4h", "1d"])
            
            results = {}
            total_bars_updated = 0
            
            for symbol in symbols:
                results[symbol] = {}
                
                for timeframe in timeframes:
                    try:
                        logger.info(f"Updating {symbol} {timeframe}")
                        
                        # Sync data
                        sync_result = fetcher.sync_symbol_timeframe(symbol, timeframe)
                        
                        if sync_result["success"]:
                            bars_added = sync_result.get("bars_added", 0)
                            total_bars_updated += bars_added
                            
                            results[symbol][timeframe] = {
                                "success": True,
                                "bars_added": bars_added,
                                "message": sync_result.get("message", "")
                            }
                            logger.info(f"Updated {symbol} {timeframe}: {bars_added} bars added")
                        else:
                            results[symbol][timeframe] = {
                                "success": False,
                                "error": sync_result.get("message", "Unknown error")
                            }
                            logger.warning(f"Failed to update {symbol} {timeframe}: {sync_result.get('message')}")
                            
                    except Exception as e:
                        logger.error(f"Error updating {symbol} {timeframe}: {e}")
                        results[symbol][timeframe] = {
                            "success": False,
                            "error": str(e)
                        }
            
            # Check if any updates were successful
            successful_updates = sum(
                1 for symbol_results in results.values() 
                for tf_result in symbol_results.values() 
                if tf_result.get("success", False)
            )
            
            if successful_updates == 0:
                self.last_error = "No successful data updates"
                logger.warning("Update data job completed with no successful updates")
                return {
                    "success": False,
                    "error": "No successful data updates",
                    "results": results,
                    "total_bars_updated": total_bars_updated
                }
            
            self.last_success = datetime.now(timezone.utc)
            self.last_error = None
            
            logger.info(f"Update data job completed: {successful_updates} successful updates, {total_bars_updated} total bars")
            
            return {
                "success": True,
                "successful_updates": successful_updates,
                "total_symbols": len(symbols),
                "total_timeframes": len(timeframes),
                "total_bars_updated": total_bars_updated,
                "results": results
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Update data job failed: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def run_for_symbol(self, symbol: str, timeframes: List[str]) -> Dict[str, Any]:
        """Run update job for a specific symbol and timeframes.
        
        Args:
            symbol: Trading symbol to update
            timeframes: List of timeframes to update
            
        Returns:
            Job execution result for the symbol
        """
        self.last_run = datetime.now(timezone.utc)
        
        try:
            logger.info(f"Starting update data job for {symbol}")
            
            # Initialize services
            fetcher = DataFetcher()
            store = DataStore()
            
            results = {}
            total_bars_updated = 0
            
            for timeframe in timeframes:
                try:
                    logger.info(f"Updating {symbol} {timeframe}")
                    
                    # Sync data
                    sync_result = fetcher.sync_symbol_timeframe(symbol, timeframe)
                    
                    if sync_result["success"]:
                        bars_added = sync_result.get("bars_added", 0)
                        total_bars_updated += bars_added
                        
                        results[timeframe] = {
                            "success": True,
                            "bars_added": bars_added,
                            "message": sync_result.get("message", "")
                        }
                        logger.info(f"Updated {symbol} {timeframe}: {bars_added} bars added")
                    else:
                        results[timeframe] = {
                            "success": False,
                            "error": sync_result.get("message", "Unknown error")
                        }
                        logger.warning(f"Failed to update {symbol} {timeframe}: {sync_result.get('message')}")
                        
                except Exception as e:
                    logger.error(f"Error updating {symbol} {timeframe}: {e}")
                    results[timeframe] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Check if any updates were successful
            successful_updates = sum(
                1 for tf_result in results.values() 
                if tf_result.get("success", False)
            )
            
            if successful_updates == 0:
                self.last_error = f"No successful data updates for {symbol}"
                logger.warning(f"Update data job for {symbol} completed with no successful updates")
                return {
                    "success": False,
                    "error": "No successful data updates",
                    "results": results,
                    "total_bars_updated": total_bars_updated
                }
            
            self.last_success = datetime.now(timezone.utc)
            self.last_error = None
            
            logger.info(f"Update data job for {symbol} completed: {successful_updates} successful updates, {total_bars_updated} total bars")
            
            return {
                "success": True,
                "successful_updates": successful_updates,
                "total_timeframes": len(timeframes),
                "total_bars_updated": total_bars_updated,
                "results": results
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Update data job for {symbol} failed: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get job status.
        
        Returns:
            Job status information
        """
        return {
            "name": "update_data",
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_error": self.last_error,
            "status": "success" if self.last_success and not self.last_error else "error" if self.last_error else "never_run"
        }

