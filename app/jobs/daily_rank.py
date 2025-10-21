"""Daily ranking job.

This job runs daily to rank strategies and update rankings.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import traceback

from app.service.strategy_ranking import StrategyRankingService
from app.data import DataStore

logger = logging.getLogger(__name__)


class DailyRankJob:
    """Daily ranking job."""
    
    def __init__(self):
        """Initialize job."""
        self.last_run = None
        self.last_success = None
        self.last_error = None
        
        logger.info("DailyRankJob initialized")
    
    async def run(self) -> Dict[str, Any]:
        """Run the daily ranking job.
        
        Returns:
            Job execution result
        """
        self.last_run = datetime.now(timezone.utc)
        
        try:
            logger.info("Starting daily ranking job")
            
            # Initialize services
            ranking_service = StrategyRankingService()
            data_store = DataStore()
            
            # Get symbols to rank
            symbols = ["BTC/USDT", "ETH/USDT"]  # TODO: Get from config
            
            results = {}
            
            for symbol in symbols:
                try:
                    logger.info(f"Ranking strategies for {symbol}")
                    
                    # Run ranking for symbol
                    ranking_result = await ranking_service.rank_strategies(symbol)
                    
                    if ranking_result:
                        results[symbol] = {
                            "success": True,
                            "rankings_count": len(ranking_result),
                            "top_strategy": ranking_result[0].strategy_name if ranking_result else None
                        }
                        logger.info(f"Ranked {len(ranking_result)} strategies for {symbol}")
                    else:
                        results[symbol] = {
                            "success": False,
                            "error": "No rankings generated"
                        }
                        logger.warning(f"No rankings generated for {symbol}")
                        
                except Exception as e:
                    logger.error(f"Error ranking {symbol}: {e}")
                    results[symbol] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Check if any rankings were successful
            successful_rankings = sum(1 for r in results.values() if r.get("success", False))
            
            if successful_rankings == 0:
                self.last_error = "No successful rankings generated"
                logger.error("Daily ranking job failed: No successful rankings")
                return {
                    "success": False,
                    "error": "No successful rankings generated",
                    "results": results
                }
            
            self.last_success = datetime.now(timezone.utc)
            self.last_error = None
            
            logger.info(f"Daily ranking job completed: {successful_rankings}/{len(symbols)} symbols ranked")
            
            return {
                "success": True,
                "successful_rankings": successful_rankings,
                "total_symbols": len(symbols),
                "results": results
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Daily ranking job failed: {e}")
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
            "name": "daily_rank",
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_error": self.last_error,
            "status": "success" if self.last_success and not self.last_error else "error" if self.last_error else "never_run"
        }
