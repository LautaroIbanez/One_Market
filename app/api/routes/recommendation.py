"""Recommendation API endpoints for One Market platform.

This module provides endpoints for daily recommendations and
recommendation history.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import logging

from app.service.daily_recommendation import DailyRecommendationService
from app.service.recommendation_contract import Recommendation, RecommendationRequest, RecommendationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendation", tags=["recommendation"])

# Global service instance
recommendation_service = None


def get_recommendation_service() -> DailyRecommendationService:
    """Get or create recommendation service instance."""
    global recommendation_service
    if recommendation_service is None:
        recommendation_service = DailyRecommendationService()
    return recommendation_service


@router.get("/daily", response_model=Recommendation)
async def get_daily_recommendation(
    symbol: str = Query(..., description="Trading symbol"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)"),
    capital: float = Query(10000.0, description="Available capital"),
    risk_percentage: float = Query(2.0, description="Risk percentage per trade")
):
    """Get daily recommendation for symbol/date.
    
    Args:
        symbol: Trading symbol
        date: Date for recommendation (default: today)
        capital: Available capital
        risk_percentage: Risk percentage per trade
        
    Returns:
        Recommendation object or HOLD with reason
    """
    try:
        # Use today's date if not specified
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Validate date format
        try:
            datetime.fromisoformat(date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Get service with custom parameters
        service = DailyRecommendationService(capital=capital, max_risk_pct=risk_percentage)
        
        # Generate recommendation
        recommendation = service.get_daily_recommendation(symbol, date)
        
        logger.info(f"Generated recommendation for {symbol} on {date}: {recommendation.direction}")
        return recommendation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating daily recommendation: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


@router.get("/history", response_model=List[Recommendation])
async def get_recommendation_history(
    symbol: str = Query(..., description="Trading symbol"),
    from_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    to_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format (default: today)")
):
    """Get recommendation history for symbol and date range.
    
    Args:
        symbol: Trading symbol
        from_date: Start date
        to_date: End date (default: today)
        
    Returns:
        List of recommendations
    """
    try:
        # Use today's date if not specified
        if to_date is None:
            to_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Validate date formats
        try:
            datetime.fromisoformat(from_date)
            datetime.fromisoformat(to_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Get service
        service = get_recommendation_service()
        
        # Get history
        recommendations = service.get_recommendation_history(symbol, from_date, to_date)
        
        logger.info(f"Retrieved {len(recommendations)} recommendations for {symbol} from {from_date} to {to_date}")
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendation history: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.post("/generate", response_model=RecommendationResponse)
async def generate_recommendation(request: RecommendationRequest):
    """Generate recommendation with custom parameters.
    
    Args:
        request: Recommendation request parameters
        
    Returns:
        RecommendationResponse with results
    """
    try:
        # Get service with custom parameters
        service = DailyRecommendationService(
            capital=request.capital,
            max_risk_pct=request.risk_percentage
        )
        
        # Generate recommendation
        recommendation = service.get_daily_recommendation(
            request.symbol, 
            request.date,
            request.timeframes
        )
        
        # Calculate data quality metrics
        data_quality = {
            "timeframes_analyzed": len(request.timeframes),
            "capital": request.capital,
            "risk_percentage": request.risk_percentage,
            "confidence": recommendation.confidence
        }
        
        # Calculate analysis time (simplified)
        analysis_time = 0.5  # Placeholder
        
        return RecommendationResponse(
            success=True,
            recommendation=recommendation,
            message=f"Recommendation generated for {request.symbol}",
            data_quality=data_quality,
            analysis_time=analysis_time
        )
        
    except Exception as e:
        logger.error(f"Error generating recommendation: {e}")
        return RecommendationResponse(
            success=False,
            recommendation=None,
            message=f"Recommendation generation failed: {str(e)}",
            data_quality={},
            analysis_time=0.0
        )


@router.get("/stats/{symbol}")
async def get_recommendation_stats(symbol: str):
    """Get recommendation statistics for symbol.
    
    Args:
        symbol: Trading symbol
        
    Returns:
        Statistics about recommendations
    """
    try:
        # Get service
        service = get_recommendation_service()
        
        # Get last 30 days of recommendations
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        
        recommendations = service.get_recommendation_history(symbol, start_date, end_date)
        
        if not recommendations:
            return {
                "symbol": symbol,
                "total_recommendations": 0,
                "long_recommendations": 0,
                "short_recommendations": 0,
                "hold_recommendations": 0,
                "average_confidence": 0.0,
                "date_range": f"{start_date} to {end_date}"
            }
        
        # Calculate statistics
        total = len(recommendations)
        long_count = sum(1 for r in recommendations if r.direction.value == "LONG")
        short_count = sum(1 for r in recommendations if r.direction.value == "SHORT")
        hold_count = sum(1 for r in recommendations if r.direction.value == "HOLD")
        avg_confidence = sum(r.confidence for r in recommendations) / total
        
        return {
            "symbol": symbol,
            "total_recommendations": total,
            "long_recommendations": long_count,
            "short_recommendations": short_count,
            "hold_recommendations": hold_count,
            "average_confidence": round(avg_confidence, 2),
            "date_range": f"{start_date} to {end_date}",
            "latest_recommendation": {
                "date": recommendations[0].date,
                "direction": recommendations[0].direction.value,
                "confidence": recommendations[0].confidence
            } if recommendations else None
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendation stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/health")
async def recommendation_health_check():
    """Health check for recommendation service.
    
    Returns:
        Health status
    """
    try:
        # Test service initialization
        service = get_recommendation_service()
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "service_initialized": True,
            "capital": service.capital,
            "max_risk_pct": service.max_risk_pct
        }
    except Exception as e:
        logger.error(f"Recommendation health check failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
