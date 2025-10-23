"""Test recommendation endpoint to verify functionality."""

from fastapi import APIRouter
from app.service.daily_recommendation import DailyRecommendationService
from app.service.recommendation_contract import Recommendation

router = APIRouter(prefix="/test", tags=["test"])

@router.get("/recommendation")
async def test_recommendation():
    """Test endpoint that directly returns a working recommendation."""
    
    # Create service instance
    service = DailyRecommendationService()
    
    # Generate recommendation directly
    recommendation = service._get_signal_based_recommendation("BTC/USDT", "2024-01-15", ["1h", "4h", "1d"])
    
    return recommendation
