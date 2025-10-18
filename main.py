"""FastAPI main application for One Market platform.

This is the entry point for the REST API server.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from app.config.settings import settings
from app.data.store import DataStore
from app.data.fetch import DataFetcher
from app.data.schema import FetchRequest

# Service
from app.service import DecisionEngine, MarketAdvisor, PaperTradingDB
from app.service.tp_sl_engine import TPSLConfig

# Research
from app.research.signals import generate_signal, get_strategy_list
from app.research.combine import combine_signals
from app.research.backtest import BacktestEngine, BacktestConfig

# Logging
from app.utils.structured_logging import logger, event_logger

# API models
from pydantic import BaseModel, Field


# FastAPI app
app = FastAPI(
    title="One Market API",
    description="Trading platform API for signal generation, backtesting, and decision making",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class SymbolsResponse(BaseModel):
    """Response for symbols endpoint."""
    symbols: List[str]
    count: int


class SignalRequest(BaseModel):
    """Request for signal generation."""
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(default="1h", description="Timeframe")
    strategy: str = Field(..., description="Strategy name")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Strategy parameters")


class SignalResponse(BaseModel):
    """Response for signal generation."""
    symbol: str
    timeframe: str
    signal: int
    strength: float
    strategy: str
    timestamp: datetime
    market_price: float


class DecisionRequest(BaseModel):
    """Request for daily decision."""
    symbol: str
    timeframe: str = Field(default="1h")
    strategies: Optional[List[str]] = Field(default=None, description="Strategies to use")
    combination_method: str = Field(default="simple_average")
    capital: float = Field(default=100000.0)


class BacktestRequest(BaseModel):
    """Request for backtest."""
    symbol: str
    timeframe: str
    strategy: str
    params: Optional[Dict[str, Any]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float = 100000.0


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "One Market API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "scheduler_enabled": settings.SCHEDULER_ENABLED
    }


@app.get("/symbols", response_model=SymbolsResponse)
async def get_symbols():
    """Get available trading symbols from configuration and stored data."""
    try:
        # Get from configuration
        config_symbols = settings.DEFAULT_SYMBOLS
        
        # Get from stored data
        store = DataStore()
        stored_symbols = [f"{sym}/{tf}" for sym, tf in store.list_stored_symbols()]
        
        # Combine and deduplicate
        all_symbols = list(set(config_symbols + stored_symbols))
        
        return SymbolsResponse(
            symbols=sorted(all_symbols),
            count=len(all_symbols)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching symbols: {str(e)}")


@app.post("/signal", response_model=SignalResponse)
async def generate_trading_signal(request: SignalRequest):
    """Generate trading signal for a symbol using specified strategy."""
    try:
        # Load data
        store = DataStore()
        bars = store.read_bars(request.symbol, request.timeframe)
        
        if len(bars) < 50:
            raise HTTPException(status_code=400, detail="Insufficient data for signal generation")
        
        # Convert to DataFrame
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Generate signal
        signal_output = generate_signal(request.strategy, df, request.params)
        
        # Get current values
        current_signal = int(signal_output.signal.iloc[-1])
        current_strength = float(signal_output.strength.iloc[-1]) if signal_output.strength is not None else 0.0
        current_price = float(df['close'].iloc[-1])
        
        return SignalResponse(
            symbol=request.symbol,
            timeframe=request.timeframe,
            signal=current_signal,
            strength=current_strength,
            strategy=request.strategy,
            timestamp=datetime.now(),
            market_price=current_price
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signal: {str(e)}")


@app.post("/decision")
async def make_daily_decision(request: DecisionRequest):
    """Make daily trading decision with multi-horizon analysis."""
    try:
        # Load data
        store = DataStore()
        bars = store.read_bars(request.symbol, request.timeframe)
        
        if len(bars) < 100:
            raise HTTPException(status_code=400, detail="Insufficient data")
        
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Generate signals from strategies
        if request.strategies:
            strategy_signals = {}
            for strat in request.strategies:
                sig = generate_signal(strat, df)
                strategy_signals[strat] = sig.signal
        else:
            # Use default strategies
            from app.research.signals import ma_crossover, rsi_regime_pullback
            sig1 = ma_crossover(df['close'])
            sig2 = rsi_regime_pullback(df['close'])
            strategy_signals = {'ma_cross': sig1.signal, 'rsi_regime': sig2.signal}
        
        # Combine signals
        returns = df['close'].pct_change()
        combined = combine_signals(
            strategy_signals,
            method=request.combination_method,
            returns=returns if request.combination_method == "sharpe_weighted" else None
        )
        
        # Get advisor recommendation
        advisor = MarketAdvisor(default_risk_pct=settings.DEFAULT_RISK_PCT)
        advice = advisor.get_advice(
            df_intraday=df,
            current_signal=int(combined.signal.iloc[-1]),
            signal_strength=float(combined.confidence.iloc[-1]),
            symbol=request.symbol
        )
        
        # Make decision
        engine = DecisionEngine()
        decision = engine.make_decision(
            df,
            combined.signal,
            signal_strength=combined.confidence,
            signal_source="combined",
            capital=request.capital,
            risk_pct=advice.recommended_risk_pct
        )
        
        return {
            "decision": {
                "signal": decision.signal,
                "should_execute": decision.should_execute,
                "entry_price": decision.entry_price,
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
                "position_size": decision.position_size.quantity if decision.position_size else 0,
                "risk_amount": decision.position_size.risk_amount if decision.position_size else 0,
                "skip_reason": decision.skip_reason,
                "window": decision.window
            },
            "advice": {
                "consensus": advice.consensus_direction,
                "confidence": advice.confidence_score,
                "recommended_risk": advice.recommended_risk_pct,
                "short_term": advice.short_term.model_dump(),
                "medium_term": advice.medium_term.model_dump(),
                "long_term": advice.long_term.model_dump()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error making decision: {str(e)}")


@app.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run backtest on a strategy."""
    try:
        # Load data
        store = DataStore()
        bars = store.read_bars(request.symbol, request.timeframe)
        
        if len(bars) < 100:
            raise HTTPException(status_code=400, detail="Insufficient data for backtest")
        
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Filter by date if provided
        if request.start_date:
            start_ts = int(datetime.fromisoformat(request.start_date).timestamp() * 1000)
            df = df[df['timestamp'] >= start_ts]
        if request.end_date:
            end_ts = int(datetime.fromisoformat(request.end_date).timestamp() * 1000)
            df = df[df['timestamp'] <= end_ts]
        
        # Generate signals
        signal_output = generate_signal(request.strategy, df, request.params)
        
        # Run backtest
        config = BacktestConfig(initial_capital=request.initial_capital)
        engine = BacktestEngine(config)
        
        # Simplified backtest (vectorbt optional)
        returns = df['close'].pct_change()
        strategy_returns = signal_output.signal.shift(1) * returns
        
        total_return = (1 + strategy_returns).prod() - 1
        sharpe = (strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)) if strategy_returns.std() > 0 else 0
        
        equity = request.initial_capital * (1 + strategy_returns).cumprod()
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max
        max_dd = abs(drawdown.min())
        
        num_trades = (signal_output.signal != signal_output.signal.shift(1)).sum()
        
        return {
            "total_return": float(total_return),
            "sharpe_ratio": float(sharpe),
            "max_drawdown": float(max_dd),
            "total_trades": int(num_trades),
            "final_capital": float(equity.iloc[-1]),
            "strategy": request.strategy,
            "period": {
                "start": df['timestamp'].iloc[0],
                "end": df['timestamp'].iloc[-1]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")


@app.get("/metrics/{symbol}")
async def get_metrics(symbol: str, timeframe: str = "1h"):
    """Get performance metrics for a symbol."""
    try:
        db = PaperTradingDB()
        
        # Get recent decisions
        today = datetime.now().strftime('%Y-%m-%d')
        decisions = db.get_decisions_by_day(today)
        
        # Get open trades
        open_trades = db.get_open_trades(symbol)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "decisions_today": len(decisions),
            "open_trades": len(open_trades),
            "last_updated": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")


@app.post("/force-close")
async def force_close_positions():
    """Force close all open positions."""
    try:
        db = PaperTradingDB()
        open_trades = db.get_open_trades()
        
        # Close all open trades
        closed_count = 0
        for trade in open_trades:
            # Get current price (would need to fetch from exchange in production)
            trade.close_trade(
                exit_price=trade.entry_price,  # Simplified
                exit_time=datetime.now(),
                exit_reason="forced_close"
            )
            db.save_trade(trade)
            closed_count += 1
        
        return {
            "status": "success",
            "closed_trades": closed_count,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forcing close: {str(e)}")


@app.get("/strategies")
async def list_strategies():
    """List available trading strategies."""
    return {
        "strategies": get_strategy_list(),
        "count": len(get_strategy_list())
    }


# ============================================================
# STARTUP/SHUTDOWN
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("ONE MARKET API - Starting", version=app.version, host=settings.API_HOST, port=settings.API_PORT)
    
    print("="*60)
    print("ONE MARKET API - Starting")
    print("="*60)
    print(f"API Version: {app.version}")
    print(f"Host: {settings.API_HOST}:{settings.API_PORT}")
    print(f"Scheduler: {'Enabled' if settings.SCHEDULER_ENABLED else 'Disabled'}")
    print("="*60)
    
    # Start scheduler if enabled
    if settings.SCHEDULER_ENABLED:
        from app.jobs import start_scheduler
        start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("ONE MARKET API - Shutting down")
    print("\nONE MARKET API - Shutting down")
    
    if settings.SCHEDULER_ENABLED:
        from app.jobs import stop_scheduler
        stop_scheduler()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        workers=settings.API_WORKERS
    )

