"""Backtest API endpoints for One Market platform.

This module provides unified backtesting endpoints that use the
same engine as the UI, ensuring consistency.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import logging
import json
import pandas as pd

from app.research.backtest.engine import BacktestEngine, BacktestConfig, BacktestResult
from app.data import DataStore, DataFetcher
from app.research.signals import generate_signal, get_strategy_list
from app.service.recommendation_contract import Recommendation, PlanDirection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backtest", tags=["backtest"])

# Global instances
data_store = None
data_fetcher = None


def get_data_store() -> DataStore:
    """Get or create data store instance."""
    global data_store
    if data_store is None:
        from app.data import DataStore
        data_store = DataStore()
    return data_store


def get_data_fetcher() -> DataFetcher:
    """Get or create data fetcher instance."""
    global data_fetcher
    if data_fetcher is None:
        from app.data import DataFetcher
        data_fetcher = DataFetcher()
    return data_fetcher


class BacktestRequest(BaseModel):
    """Request model for backtest execution."""
    
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe")
    strategy: str = Field(..., description="Strategy name")
    from_date: Optional[datetime] = Field(None, description="Start date")
    to_date: Optional[datetime] = Field(None, description="End date")
    
    # Backtest configuration
    initial_capital: float = Field(default=10000.0, description="Initial capital")
    risk_per_trade: float = Field(default=0.02, description="Risk per trade (2%)")
    commission: float = Field(default=0.001, description="Commission rate")
    slippage: float = Field(default=0.0005, description="Slippage rate")
    
    # Trading rules
    use_trading_windows: bool = Field(default=True, description="Apply trading windows")
    force_close: bool = Field(default=True, description="Force close positions")
    one_trade_per_day: bool = Field(default=True, description="Limit to 1 trade per day")
    
    # Risk management
    atr_sl_multiplier: float = Field(default=2.0, description="ATR stop loss multiplier")
    atr_tp_multiplier: float = Field(default=3.0, description="ATR take profit multiplier")
    atr_period: int = Field(default=14, description="ATR calculation period")


class BacktestResponse(BaseModel):
    """Response model for backtest execution."""
    
    success: bool = Field(..., description="Backtest success status")
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe")
    strategy: str = Field(..., description="Strategy name")
    
    # Performance metrics
    total_return: float = Field(..., description="Total return")
    cagr: float = Field(..., description="Compound Annual Growth Rate")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    win_rate: float = Field(..., description="Win rate")
    profit_factor: float = Field(..., description="Profit factor")
    expectancy: float = Field(..., description="Expectancy")
    
    # Trade statistics
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    avg_win: float = Field(..., description="Average winning trade")
    avg_loss: float = Field(..., description="Average losing trade")
    
    # Risk metrics
    volatility: float = Field(..., description="Volatility")
    calmar_ratio: float = Field(..., description="Calmar ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    
    # Capital
    initial_capital: float = Field(..., description="Initial capital")
    final_capital: float = Field(..., description="Final capital")
    profit: float = Field(..., description="Total profit")
    
    # Period
    from_date: datetime = Field(..., description="Start date")
    to_date: datetime = Field(..., description="End date")
    
    # Data integrity
    dataset_hash: str = Field(..., description="Dataset hash")
    params_hash: str = Field(..., description="Parameters hash")
    
    # Trades data
    trades: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed trades")
    
    # Metadata
    execution_time: float = Field(..., description="Execution time in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """Run unified backtest using the same engine as UI.
    
    Args:
        request: Backtest request parameters
        
    Returns:
        BacktestResponse with comprehensive results
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Starting backtest for {request.symbol} {request.timeframe} with {request.strategy}")
        
        # Get data store
        store = get_data_store()
        
        # Load data
        df = store.read_bars(
            symbol=request.symbol,
            tf=request.timeframe,
            since=request.from_date,
            until=request.to_date
        )
        
        if not df:
            raise HTTPException(
                status_code=400,
                detail=f"No data found for {request.symbol} {request.timeframe}"
            )
        
        # Convert to DataFrame if needed
        if isinstance(df, list):
            df = pd.DataFrame([bar.to_dict() for bar in df])
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Generate signals
        signal_output = generate_signal(df['close'], request.strategy)
        if signal_output is None or signal_output.signal.empty:
            raise HTTPException(
                status_code=400,
                detail=f"No signals generated for strategy {request.strategy}"
            )
        
        # Create backtest configuration
        config = BacktestConfig(
            initial_capital=request.initial_capital,
            risk_per_trade=request.risk_per_trade,
            commission=request.commission,
            slippage=request.slippage,
            use_trading_windows=request.use_trading_windows,
            force_close=request.force_close,
            one_trade_per_day=request.one_trade_per_day,
            atr_sl_multiplier=request.atr_sl_multiplier,
            atr_tp_multiplier=request.atr_tp_multiplier,
            atr_period=request.atr_period
        )
        
        # Run backtest
        engine = BacktestEngine(config)
        result = engine.run(df, signal_output.signal, request.strategy, verbose=False)
        
        if not result or result.total_trades == 0:
            raise HTTPException(
                status_code=400,
                detail=f"No trades executed for {request.strategy}"
            )
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Create response
        response = BacktestResponse(
            success=True,
            symbol=request.symbol,
            timeframe=request.timeframe,
            strategy=request.strategy,
            
            # Performance metrics
            total_return=result.total_return,
            cagr=result.cagr,
            sharpe_ratio=result.sharpe_ratio,
            max_drawdown=result.max_drawdown,
            win_rate=result.win_rate,
            profit_factor=result.profit_factor,
            expectancy=result.expectancy,
            
            # Trade statistics
            total_trades=result.total_trades,
            winning_trades=result.winning_trades,
            losing_trades=result.losing_trades,
            avg_win=result.avg_win,
            avg_loss=result.avg_loss,
            
            # Risk metrics
            volatility=result.volatility,
            calmar_ratio=result.calmar_ratio,
            sortino_ratio=result.sortino_ratio,
            
            # Capital
            initial_capital=result.initial_capital,
            final_capital=result.final_capital,
            profit=result.profit,
            
            # Period
            from_date=datetime.fromtimestamp(result.from_timestamp / 1000, tz=timezone.utc),
            to_date=datetime.fromtimestamp(result.to_timestamp / 1000, tz=timezone.utc),
            
            # Data integrity
            dataset_hash=result.dataset_hash,
            params_hash=result.params_hash,
            
            # Trades data
            trades=result.trades,
            
            # Metadata
            execution_time=execution_time,
            created_at=start_time
        )
        
        logger.info(f"Backtest completed: {result.total_trades} trades, Sharpe={result.sharpe_ratio:.2f}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in backtest execution: {e}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.get("/strategies")
async def get_available_strategies():
    """Get list of available strategies.
    
    Returns:
        List of available strategy names
    """
    try:
        strategies = get_strategy_list()
        return {
            "strategies": strategies,
            "count": len(strategies)
        }
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting strategies: {str(e)}")


@router.get("/health")
async def backtest_health_check():
    """Health check for backtest service.
    
    Returns:
        Health status
    """
    try:
        # Test data store connection
        store = get_data_store()
        
        # Test strategy list
        strategies = get_strategy_list()
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "data_store_connected": True,
            "available_strategies": len(strategies),
            "backtest_engine": "unified"
        }
    except Exception as e:
        logger.error(f"Backtest health check failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
