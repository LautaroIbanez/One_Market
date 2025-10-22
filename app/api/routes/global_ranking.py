"""Global ranking API endpoints for One Market platform.

This module provides endpoints for automated strategy ranking and results.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from app.service.global_ranking import GlobalRankingService, GlobalRankingConfig
from app.jobs.global_ranking_job import GlobalRankingJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/global-ranking", tags=["global-ranking"])

# Global instances
ranking_service = None
ranking_job = None


def get_ranking_service() -> GlobalRankingService:
    """Get or create ranking service instance."""
    global ranking_service
    if ranking_service is None:
        ranking_service = GlobalRankingService()
    return ranking_service


def get_ranking_job() -> GlobalRankingJob:
    """Get or create ranking job instance."""
    global ranking_job
    if ranking_job is None:
        ranking_job = GlobalRankingJob()
    return ranking_job


class RankingRequest(BaseModel):
    """Request model for global ranking execution."""
    
    symbol: str = Field(..., description="Trading symbol")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format (default: today)")
    timeframes: Optional[List[str]] = Field(None, description="Timeframes to analyze")
    ranking_weights: Optional[Dict[str, float]] = Field(None, description="Custom ranking weights")


class RankingResponse(BaseModel):
    """Response model for global ranking execution."""
    
    success: bool = Field(..., description="Ranking success status")
    symbol: str = Field(..., description="Trading symbol")
    date: str = Field(..., description="Date processed")
    total_strategies: int = Field(..., description="Total strategies tested")
    valid_strategies: int = Field(..., description="Valid strategies (min trades)")
    execution_time: float = Field(..., description="Execution time in seconds")
    best_strategy: Optional[str] = Field(None, description="Best strategy name")
    best_score: Optional[float] = Field(None, description="Best strategy score")
    rankings: List[Dict[str, Any]] = Field(default_factory=list, description="Strategy rankings")
    consolidated_metrics: Dict[str, float] = Field(default_factory=dict, description="Consolidated metrics")


@router.post("/run", response_model=RankingResponse)
async def run_global_ranking(request: RankingRequest):
    """Run global ranking for a symbol.
    
    Args:
        request: Ranking request parameters
        
    Returns:
        RankingResponse with complete results
    """
    try:
        logger.info(f"Running global ranking for {request.symbol}")
        
        # Get ranking service
        service = get_ranking_service()
        
        # Run global ranking
        result = service.run_global_ranking(
            symbol=request.symbol,
            date=request.date
        )
        
        # Create response
        response = RankingResponse(
            success=True,
            symbol=request.symbol,
            date=request.date or datetime.now().strftime("%Y-%m-%d"),
            total_strategies=result.total_strategies,
            valid_strategies=result.valid_strategies,
            execution_time=result.execution_time,
            best_strategy=result.consolidated_metrics.get('best_strategy'),
            best_score=result.consolidated_metrics.get('best_score'),
            rankings=result.rankings,
            consolidated_metrics=result.consolidated_metrics
        )
        
        logger.info(f"Global ranking completed: {result.valid_strategies} valid strategies")
        return response
        
    except Exception as e:
        logger.error(f"Error in global ranking: {e}")
        raise HTTPException(status_code=500, detail=f"Global ranking failed: {str(e)}")


@router.get("/rankings/{symbol}")
async def get_daily_rankings(
    symbol: str,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)"),
    limit: int = Query(10, description="Number of top strategies to return")
):
    """Get daily rankings for a symbol.
    
    Args:
        symbol: Trading symbol
        date: Date for rankings (default: today)
        limit: Number of top strategies to return
        
    Returns:
        List of strategy rankings
    """
    try:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        service = get_ranking_service()
        rankings = service.get_daily_rankings(symbol, date)
        
        if not rankings:
            raise HTTPException(
                status_code=404,
                detail=f"No rankings found for {symbol} on {date}"
            )
        
        # Return top N strategies
        top_rankings = rankings[:limit]
        
        return {
            "symbol": symbol,
            "date": date,
            "total_strategies": len(rankings),
            "rankings": top_rankings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daily rankings: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting rankings: {str(e)}")


@router.get("/metrics/{symbol}")
async def get_consolidated_metrics(
    symbol: str,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
):
    """Get consolidated metrics for a symbol.
    
    Args:
        symbol: Trading symbol
        date: Date for metrics (default: today)
        
    Returns:
        Consolidated metrics
    """
    try:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        service = get_ranking_service()
        metrics = service.get_consolidated_metrics(symbol, date)
        
        if not metrics:
            raise HTTPException(
                status_code=404,
                detail=f"No metrics found for {symbol} on {date}"
            )
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting consolidated metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")


@router.get("/top-strategies/{symbol}")
async def get_top_strategies(
    symbol: str,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)"),
    limit: int = Query(5, description="Number of top strategies to return")
):
    """Get top strategies for a symbol.
    
    Args:
        symbol: Trading symbol
        date: Date for strategies (default: today)
        limit: Number of top strategies to return
        
    Returns:
        List of top strategies
    """
    try:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        job = get_ranking_job()
        top_strategies = job.get_top_strategies(symbol, date, limit)
        
        if not top_strategies:
            raise HTTPException(
                status_code=404,
                detail=f"No strategies found for {symbol} on {date}"
            )
        
        return {
            "symbol": symbol,
            "date": date,
            "top_strategies": top_strategies
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting top strategies: {str(e)}")


@router.post("/run-daily")
async def run_daily_ranking_job(
    background_tasks: BackgroundTasks,
    symbols: Optional[List[str]] = Query(None, description="Symbols to process (default: BTC/USDT, ETH/USDT, ADA/USDT)")
):
    """Run daily ranking job for multiple symbols.
    
    Args:
        background_tasks: FastAPI background tasks
        symbols: List of symbols to process
        
    Returns:
        Job status
    """
    try:
        if symbols is None:
            symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
        
        logger.info(f"Starting daily ranking job for {len(symbols)} symbols")
        
        # Run job in background
        job = get_ranking_job()
        background_tasks.add_task(job.run_daily_ranking, symbols)
        
        return {
            "status": "started",
            "symbols": symbols,
            "message": "Daily ranking job started in background"
        }
        
    except Exception as e:
        logger.error(f"Error starting daily ranking job: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting job: {str(e)}")


@router.get("/health")
async def ranking_health_check():
    """Health check for global ranking service.
    
    Returns:
        Health status
    """
    try:
        service = get_ranking_service()
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "global-ranking",
            "timeframes": service.config.target_timeframes,
            "ranking_weights": service.config.ranking_weights
        }
    except Exception as e:
        logger.error(f"Global ranking health check failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
