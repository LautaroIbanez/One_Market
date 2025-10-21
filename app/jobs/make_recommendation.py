"""Make recommendation job.

This job runs daily to generate trading recommendations.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import traceback

from app.service.daily_recommendation import DailyRecommendationService
from app.data import DataStore

logger = logging.getLogger(__name__)


class MakeRecommendationJob:
    """Make recommendation job."""
    
    def __init__(self):
        """Initialize job."""
        self.last_run = None
        self.last_success = None
        self.last_error = None
        
        logger.info("MakeRecommendationJob initialized")
    
    async def run(self) -> Dict[str, Any]:
        """Run the make recommendation job.
        
        Returns:
            Job execution result
        """
        self.last_run = datetime.now(timezone.utc)
        
        try:
            logger.info("Starting make recommendation job")
            
            # Initialize services
            recommendation_service = DailyRecommendationService()
            data_store = DataStore()
            
            # Get symbols to generate recommendations for
            symbols = ["BTC/USDT", "ETH/USDT"]  # TODO: Get from config
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
            results = {}
            
            for symbol in symbols:
                try:
                    logger.info(f"Generating recommendation for {symbol}")
                    
                    # Generate recommendation
                    recommendation = recommendation_service.get_daily_recommendation(symbol, today)
                    
                    if recommendation:
                        results[symbol] = {
                            "success": True,
                            "direction": recommendation.direction.value,
                            "confidence": recommendation.confidence,
                            "rationale": recommendation.rationale,
                            "entry_price": recommendation.entry_price,
                            "stop_loss": recommendation.stop_loss,
                            "take_profit": recommendation.take_profit
                        }
                        logger.info(f"Generated {recommendation.direction.value} recommendation for {symbol} with confidence {recommendation.confidence}")
                    else:
                        results[symbol] = {
                            "success": False,
                            "error": "No recommendation generated"
                        }
                        logger.warning(f"No recommendation generated for {symbol}")
                        
                except Exception as e:
                    logger.error(f"Error generating recommendation for {symbol}: {e}")
                    results[symbol] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Check if any recommendations were successful
            successful_recommendations = sum(1 for r in results.values() if r.get("success", False))
            
            if successful_recommendations == 0:
                self.last_error = "No successful recommendations generated"
                logger.error("Make recommendation job failed: No successful recommendations")
                return {
                    "success": False,
                    "error": "No successful recommendations generated",
                    "results": results
                }
            
            self.last_success = datetime.now(timezone.utc)
            self.last_error = None
            
            logger.info(f"Make recommendation job completed: {successful_recommendations}/{len(symbols)} recommendations generated")
            
            return {
                "success": True,
                "successful_recommendations": successful_recommendations,
                "total_symbols": len(symbols),
                "results": results
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Make recommendation job failed: {e}")
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
            "name": "make_recommendation",
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_error": self.last_error,
            "status": "success" if self.last_success and not self.last_error else "error" if self.last_error else "never_run"
        }
