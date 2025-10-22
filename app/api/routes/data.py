"""Data API endpoints for One Market platform.

This module provides REST API endpoints for data synchronization
and management.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging

from app.data import DataFetcher, DataStore, DataSyncRequest, DataSyncResponse, DatasetMetadata

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["data"])

# Global instances (in production, these would be dependency injected)
data_fetcher = None
data_store = None


def get_data_fetcher() -> DataFetcher:
    """Get or create data fetcher instance."""
    global data_fetcher
    if data_fetcher is None:
        data_fetcher = DataFetcher()
    return data_fetcher


def get_data_store() -> DataStore:
    """Get or create data store instance."""
    global data_store
    if data_store is None:
        data_store = DataStore()
    return data_store


@router.post("/sync", response_model=DataSyncResponse)
async def sync_data(request: DataSyncRequest, background_tasks: BackgroundTasks):
    """Synchronize data for a symbol/timeframe.
    
    Args:
        request: Data sync request
        background_tasks: FastAPI background tasks
        
    Returns:
        DataSyncResponse with sync results
    """
    try:
        logger.info(f"Starting data sync for {request.symbol} {request.tf}")
        
        # Get instances
        fetcher = get_data_fetcher()
        store = get_data_store()
        
        # Validate symbol
        if not fetcher.validate_symbol(request.symbol):
            raise HTTPException(
                status_code=400, 
                detail=f"Symbol {request.symbol} not supported by exchange"
            )
        
        # Validate timeframe
        supported_timeframes = fetcher.get_supported_timeframes()
        if request.tf not in supported_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Timeframe {request.tf} not supported. Available: {supported_timeframes}"
            )
        
        # Perform sync
        try:
            # Fetch data from exchange
            bars = fetcher.fetch_ohlcv(
                symbol=request.symbol,
                timeframe=request.tf,
                since=request.since,
                until=request.until
            )
            
            if not bars:
                return DataSyncResponse(
                    message=f"No data available for {request.symbol} {request.tf}",
                    fetched_count=0,
                    stored_count=0
                )
            
            # Store data
            metadata = store.write_bars(bars)
            
            logger.info(f"Successfully synced {request.symbol} {request.tf}: {len(bars)} bars")
            return DataSyncResponse(
                message=f"Successfully synced {len(bars)} bars for {request.symbol} {request.tf}",
                snapshot_meta=metadata,
                fetched_count=len(bars),
                stored_count=len(bars)
            )
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in data sync: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/meta/{symbol}/{timeframe}")
async def get_metadata(symbol: str, timeframe: str) -> Optional[DatasetMetadata]:
    """Get latest metadata for symbol/timeframe.
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe
        
    Returns:
        Latest DatasetMetadata or None
    """
    try:
        store = get_data_store()
        meta = store.snapshot_meta(symbol, timeframe)
        return meta
    except Exception as e:
        logger.error(f"Error getting metadata for {symbol} {timeframe}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting metadata: {str(e)}")


@router.get("/latest/{symbol}/{timeframe}")
async def get_latest_timestamp(symbol: str, timeframe: str) -> Dict[str, Any]:
    """Get latest timestamp for symbol/timeframe.
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe
        
    Returns:
        Dictionary with latest timestamp info
    """
    try:
        store = get_data_store()
        latest_ts = store.latest_ts(symbol, timeframe)
        
        if latest_ts:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "latest_timestamp": latest_ts,
                "latest_datetime": datetime.fromtimestamp(latest_ts / 1000, tz=timezone.utc).isoformat(),
                "has_data": True
            }
        else:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "latest_timestamp": None,
                "latest_datetime": None,
                "has_data": False
            }
    except Exception as e:
        logger.error(f"Error getting latest timestamp for {symbol} {timeframe}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting latest timestamp: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.
    
    Returns:
        Health status with dataset information
    """
    try:
        fetcher = get_data_fetcher()
        store = get_data_store()
        
        # Get exchange info
        exchange_info = fetcher.get_exchange_info()
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "exchange": exchange_info,
            "data_store": {
                "path": str(store.base_path),
                "db_path": str(store.db_path)
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/supported-symbols")
async def get_supported_symbols() -> Dict[str, Any]:
    """Get list of supported symbols.
    
    Returns:
        Dictionary with supported symbols
    """
    try:
        fetcher = get_data_fetcher()
        exchange_info = fetcher.get_exchange_info()
        
        return {
            "exchange": fetcher.exchange_name,
            "total_symbols": exchange_info.get("markets", 0),
            "supported_timeframes": fetcher.get_supported_timeframes()
        }
    except Exception as e:
        logger.error(f"Error getting supported symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting supported symbols: {str(e)}")
