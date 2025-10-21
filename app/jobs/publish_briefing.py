"""Publish briefing job.

This job runs daily to publish trading briefings.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import traceback

from app.service.daily_recommendation import DailyRecommendationService
from app.data import DataStore

logger = logging.getLogger(__name__)


class PublishBriefingJob:
    """Publish briefing job."""
    
    def __init__(self):
        """Initialize job."""
        self.last_run = None
        self.last_success = None
        self.last_error = None
        
        logger.info("PublishBriefingJob initialized")
    
    async def run(self) -> Dict[str, Any]:
        """Run the publish briefing job.
        
        Returns:
            Job execution result
        """
        self.last_run = datetime.now(timezone.utc)
        
        try:
            logger.info("Starting publish briefing job")
            
            # Initialize services
            recommendation_service = DailyRecommendationService()
            data_store = DataStore()
            
            # Get symbols to publish briefings for
            symbols = ["BTC/USDT", "ETH/USDT"]  # TODO: Get from config
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
            results = {}
            
            for symbol in symbols:
                try:
                    logger.info(f"Publishing briefing for {symbol}")
                    
                    # Get today's recommendation
                    recommendations = recommendation_service.get_recommendation_history(
                        symbol, today, today
                    )
                    
                    if recommendations:
                        recommendation = recommendations[0]  # Get latest
                        
                        # Create briefing content
                        briefing = self._create_briefing(symbol, recommendation)
                        
                        # Publish briefing (simplified - just log for now)
                        briefing_published = self._publish_briefing(symbol, briefing)
                        
                        if briefing_published:
                            results[symbol] = {
                                "success": True,
                                "briefing_published": True,
                                "recommendation_direction": recommendation.direction.value,
                                "confidence": recommendation.confidence
                            }
                            logger.info(f"Briefing published for {symbol}")
                        else:
                            results[symbol] = {
                                "success": False,
                                "error": "Failed to publish briefing"
                            }
                            logger.warning(f"Failed to publish briefing for {symbol}")
                    else:
                        results[symbol] = {
                            "success": False,
                            "error": "No recommendation found for briefing"
                        }
                        logger.warning(f"No recommendation found for {symbol} briefing")
                        
                except Exception as e:
                    logger.error(f"Error publishing briefing for {symbol}: {e}")
                    results[symbol] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Check if any briefings were successful
            successful_briefings = sum(1 for r in results.values() if r.get("success", False))
            
            if successful_briefings == 0:
                self.last_error = "No successful briefings published"
                logger.error("Publish briefing job failed: No successful briefings")
                return {
                    "success": False,
                    "error": "No successful briefings published",
                    "results": results
                }
            
            self.last_success = datetime.now(timezone.utc)
            self.last_error = None
            
            logger.info(f"Publish briefing job completed: {successful_briefings}/{len(symbols)} briefings published")
            
            return {
                "success": True,
                "successful_briefings": successful_briefings,
                "total_symbols": len(symbols),
                "results": results
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Publish briefing job failed: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def _create_briefing(self, symbol: str, recommendation) -> Dict[str, Any]:
        """Create briefing content.
        
        Args:
            symbol: Trading symbol
            recommendation: Recommendation object
            
        Returns:
            Briefing content
        """
        briefing = {
            "symbol": symbol,
            "date": recommendation.date,
            "direction": recommendation.direction.value,
            "confidence": recommendation.confidence,
            "rationale": recommendation.rationale,
            "entry_price": recommendation.entry_price,
            "stop_loss": recommendation.stop_loss,
            "take_profit": recommendation.take_profit,
            "risk_amount": recommendation.risk_amount,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        return briefing
    
    def _publish_briefing(self, symbol: str, briefing: Dict[str, Any]) -> bool:
        """Publish briefing.
        
        Args:
            symbol: Trading symbol
            briefing: Briefing content
            
        Returns:
            True if published successfully
        """
        try:
            # For now, just log the briefing
            # In a real implementation, this would send to a notification service
            logger.info(f"Briefing for {symbol}: {briefing['direction']} with confidence {briefing['confidence']}")
            logger.info(f"Rationale: {briefing['rationale']}")
            
            if briefing['entry_price']:
                logger.info(f"Entry: {briefing['entry_price']}, SL: {briefing['stop_loss']}, TP: {briefing['take_profit']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error publishing briefing for {symbol}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get job status.
        
        Returns:
            Job status information
        """
        return {
            "name": "publish_briefing",
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_error": self.last_error,
            "status": "success" if self.last_success and not self.last_error else "error" if self.last_error else "never_run"
        }
