"""Global ranking job for automated daily strategy execution and ranking.

This job runs daily to execute all strategies, calculate rankings, and persist results.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from app.service.global_ranking import GlobalRankingService, GlobalRankingConfig
from app.config.settings import settings

logger = logging.getLogger(__name__)


class GlobalRankingJob:
    """Job for automated global strategy ranking."""
    
    def __init__(self, config: Optional[GlobalRankingConfig] = None):
        """Initialize global ranking job.
        
        Args:
            config: Configuration for global ranking
        """
        self.config = config or GlobalRankingConfig()
        self.ranking_service = GlobalRankingService(self.config)
        
        # Default symbols to process
        self.default_symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
        
        logger.info("GlobalRankingJob initialized")
    
    async def run_daily_ranking(
        self, 
        symbols: Optional[List[str]] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run daily ranking for specified symbols.
        
        Args:
            symbols: List of symbols to process (default: default_symbols)
            date: Date for ranking (default: today)
            
        Returns:
            Dictionary with results for each symbol
        """
        if symbols is None:
            symbols = self.default_symbols
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Running daily ranking for {len(symbols)} symbols on {date}")
        
        results = {}
        
        for symbol in symbols:
            try:
                logger.info(f"Processing {symbol}")
                
                # Run global ranking
                ranking_result = self.ranking_service.run_global_ranking(symbol, date)
                
                results[symbol] = {
                    'success': True,
                    'total_strategies': ranking_result.total_strategies,
                    'valid_strategies': ranking_result.valid_strategies,
                    'execution_time': ranking_result.execution_time,
                    'best_strategy': ranking_result.consolidated_metrics.get('best_strategy'),
                    'best_score': ranking_result.consolidated_metrics.get('best_score')
                }
                
                logger.info(f"Completed {symbol}: {ranking_result.valid_strategies} valid strategies")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                results[symbol] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Log summary
        successful = sum(1 for r in results.values() if r.get('success', False))
        logger.info(f"Daily ranking completed: {successful}/{len(symbols)} symbols successful")
        
        return results
    
    async def run_ranking_for_symbol(
        self, 
        symbol: str, 
        date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Run ranking for a specific symbol.
        
        Args:
            symbol: Trading symbol
            date: Date for ranking (default: today)
            
        Returns:
            Ranking result or None if failed
        """
        try:
            logger.info(f"Running ranking for {symbol}")
            
            ranking_result = self.ranking_service.run_global_ranking(symbol, date)
            
            return {
                'symbol': symbol,
                'date': date or datetime.now().strftime("%Y-%m-%d"),
                'total_strategies': ranking_result.total_strategies,
                'valid_strategies': ranking_result.valid_strategies,
                'execution_time': ranking_result.execution_time,
                'rankings': ranking_result.rankings,
                'consolidated_metrics': ranking_result.consolidated_metrics
            }
            
        except Exception as e:
            logger.error(f"Error running ranking for {symbol}: {e}")
            return None
    
    def get_ranking_summary(
        self, 
        symbol: str, 
        date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get ranking summary for a symbol.
        
        Args:
            symbol: Trading symbol
            date: Date for ranking (default: today)
            
        Returns:
            Ranking summary or None if not found
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Get daily rankings
            rankings = self.ranking_service.get_daily_rankings(symbol, date)
            if not rankings:
                return None
            
            # Get consolidated metrics
            metrics = self.ranking_service.get_consolidated_metrics(symbol, date)
            
            return {
                'symbol': symbol,
                'date': date,
                'total_strategies': len(rankings),
                'rankings': rankings[:10],  # Top 10
                'consolidated_metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting ranking summary for {symbol}: {e}")
            return None
    
    def get_top_strategies(
        self, 
        symbol: str, 
        date: Optional[str] = None,
        limit: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """Get top strategies for a symbol.
        
        Args:
            symbol: Trading symbol
            date: Date for ranking (default: today)
            limit: Number of top strategies to return
            
        Returns:
            List of top strategies or None if not found
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            rankings = self.ranking_service.get_daily_rankings(symbol, date)
            if not rankings:
                return None
            
            return rankings[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top strategies for {symbol}: {e}")
            return None


# Global job instance
global_ranking_job = GlobalRankingJob()


async def run_daily_ranking_job():
    """Run the daily ranking job."""
    logger.info("Starting daily ranking job")
    
    try:
        results = await global_ranking_job.run_daily_ranking()
        
        # Log results
        for symbol, result in results.items():
            if result.get('success'):
                logger.info(f"{symbol}: {result['valid_strategies']} strategies, "
                          f"best: {result['best_strategy']} ({result['best_score']:.3f})")
            else:
                logger.error(f"{symbol}: Failed - {result.get('error', 'Unknown error')}")
        
        logger.info("Daily ranking job completed")
        return results
        
    except Exception as e:
        logger.error(f"Daily ranking job failed: {e}")
        return None


if __name__ == "__main__":
    # Run the job directly
    asyncio.run(run_daily_ranking_job())
