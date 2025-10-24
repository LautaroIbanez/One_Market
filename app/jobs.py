"""APScheduler jobs for automated trading operations.

This module implements scheduled tasks:
- Data updates every 5 minutes
- Window A/B evaluation and watchers
- Forced close at 19:00 (16:45 local + buffer)
- Nightly backtest and metrics refresh
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta, time
import pandas as pd
from typing import Optional, Dict, Any

from app.config.settings import settings
from app.data.store import DataStore
from app.data.fetch import DataFetcher
from app.service import DecisionEngine, MarketAdvisor, PaperTradingDB
from app.service.tp_sl_engine import TPSLConfig
from app.research.signals import ma_crossover, rsi_regime_pullback, trend_following_ema
from app.research.combine import combine_signals
from app.research.backtest import BacktestEngine, BacktestConfig


# Global state
class JobState:
    """Global state for jobs."""
    open_positions: Dict[str, Any] = {}
    last_window_a_check: Optional[datetime] = None
    last_window_b_check: Optional[datetime] = None
    
    @classmethod
    def reset(cls):
        """Reset state."""
        cls.open_positions.clear()
        cls.last_window_a_check = None
        cls.last_window_b_check = None


job_state = JobState()


async def update_data_job():
    """Update OHLCV data for all symbols.
    
    Runs every 5 minutes.
    """
    print(f"\n[{datetime.now()}] Running update_data_job...")
    
    try:
        fetcher = DataFetcher(exchange_name=settings.EXCHANGE_NAME)
        store = DataStore()
        
        for symbol in settings.DEFAULT_SYMBOLS:
            for timeframe in settings.DEFAULT_TIMEFRAMES:
                try:
                    # Fetch latest data
                    last_ts, _ = store.get_stored_range(symbol, timeframe)
                    
                    if last_ts:
                        since = last_ts + 1
                    else:
                        # Fetch last 7 days if no data
                        since = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
                    
                    # Fetch incremental
                    bars = fetcher.fetch_incremental(symbol, timeframe, since)
                    
                    if bars:
                        # Store
                        stats = store.write_bars(bars)
                        print(f"  ✓ {symbol} {timeframe}: {len(bars)} new bars")
                    
                except Exception as e:
                    print(f"  ✗ Error updating {symbol} {timeframe}: {e}")
        
        print(f"[{datetime.now()}] update_data_job completed")
    
    except Exception as e:
        print(f"[{datetime.now()}] Error in update_data_job: {e}")


async def evaluate_window_a_job():
    """Evaluate trading opportunity in Window A.
    
    Runs during Window A (09:00-12:30 local).
    """
    print(f"\n[{datetime.now()}] Running evaluate_window_a_job...")
    
    try:
        engine = DecisionEngine()
        advisor = MarketAdvisor()
        store = DataStore()
        db = PaperTradingDB()
        
        for symbol in settings.DEFAULT_SYMBOLS:
            try:
                # Check if already traded today
                today = datetime.now().strftime('%Y-%m-%d')
                if engine.get_execution_status(today):
                    print(f"  ⏸️  {symbol}: Already executed today")
                    continue
                
                # Load data
                bars = store.read_bars(symbol, "1h")
                if len(bars) < 100:
                    continue
                
                df = pd.DataFrame([bar.to_dict() for bar in bars])
                df = df.sort_values('timestamp').reset_index(drop=True)
                
                # Generate signals
                sig1 = ma_crossover(df['close'])
                sig2 = rsi_regime_pullback(df['close'])
                
                returns = df['close'].pct_change()
                combined = combine_signals(
                    {'ma': sig1.signal, 'rsi': sig2.signal},
                    method='simple_average',
                    returns=returns
                )
                
                # Get advice
                advice = advisor.get_advice(
                    df_intraday=df,
                    current_signal=int(combined.signal.iloc[-1]),
                    signal_strength=float(combined.confidence.iloc[-1]),
                    symbol=symbol
                )
                
                # Make decision
                decision = engine.make_decision(
                    df,
                    combined.signal,
                    signal_strength=combined.confidence,
                    capital=settings.INITIAL_CAPITAL,
                    risk_pct=advice.recommended_risk_pct
                )
                
                if decision.should_execute:
                    print(f"  ✅ {symbol}: EXECUTE {decision.signal} @ ${decision.entry_price}")
                    
                    # Save decision
                    from app.data.schema import DecisionRecord
                    record = DecisionRecord(
                        decision_id=f"DEC_{today}_{symbol.replace('/', '')}",
                        trading_day=today,
                        symbol=symbol,
                        timeframe="1h",
                        signal=decision.signal,
                        signal_strength=decision.signal_strength,
                        signal_source="window_a_auto",
                        entry_price=decision.entry_price,
                        entry_mid=decision.entry_mid,
                        stop_loss=decision.stop_loss,
                        take_profit=decision.take_profit,
                        position_size=decision.position_size.quantity if decision.position_size else 0,
                        risk_amount=decision.position_size.risk_amount if decision.position_size else 0,
                        risk_pct=decision.position_size.risk_pct if decision.position_size else 0,
                        executed=True,
                        window="A"
                    )
                    db.save_decision(record)
                    
                    # Track position
                    job_state.open_positions[symbol] = {
                        'entry_price': decision.entry_price,
                        'stop_loss': decision.stop_loss,
                        'take_profit': decision.take_profit,
                        'signal': decision.signal
                    }
                else:
                    print(f"  ⏸️  {symbol}: Skip - {decision.skip_reason}")
            
            except Exception as e:
                print(f"  ✗ Error evaluating {symbol}: {e}")
        
        job_state.last_window_a_check = datetime.now()
        print(f"[{datetime.now()}] evaluate_window_a_job completed")
    
    except Exception as e:
        print(f"[{datetime.now()}] Error in evaluate_window_a_job: {e}")


async def watch_positions_job():
    """Watch open positions for TP/SL hits.
    
    Runs every minute during trading hours.
    """
    if not job_state.open_positions:
        return
    
    try:
        store = DataStore()
        db = PaperTradingDB()
        
        for symbol, position in list(job_state.open_positions.items()):
            try:
                # Get current price
                bars = store.read_bars(symbol, "1h", limit=1)
                if not bars:
                    continue
                
                current_price = bars[0].close
                
                # Check TP/SL
                hit_tp = False
                hit_sl = False
                
                if position['signal'] == 1:  # Long
                    if current_price >= position['take_profit']:
                        hit_tp = True
                    elif current_price <= position['stop_loss']:
                        hit_sl = True
                elif position['signal'] == -1:  # Short
                    if current_price <= position['take_profit']:
                        hit_tp = True
                    elif current_price >= position['stop_loss']:
                        hit_sl = True
                
                if hit_tp or hit_sl:
                    exit_reason = "take_profit" if hit_tp else "stop_loss"
                    print(f"  🎯 {symbol}: {exit_reason.upper()} hit @ ${current_price}")
                    
                    # Remove from tracking
                    del job_state.open_positions[symbol]
            
            except Exception as e:
                print(f"  ✗ Error watching {symbol}: {e}")
    
    except Exception as e:
        print(f"Error in watch_positions_job: {e}")


async def forced_close_job():
    """Force close all positions at end of day.
    
    Runs at 19:00 UTC (16:00 local, after 16:45 forced close time).
    """
    print(f"\n[{datetime.now()}] Running forced_close_job...")
    
    try:
        db = PaperTradingDB()
        open_trades = db.get_open_trades()
        
        closed_count = 0
        for trade in open_trades:
            trade.close_trade(
                exit_price=trade.entry_price,  # Simplified - would get actual price
                exit_time=datetime.now(),
                exit_reason="forced_close"
            )
            db.save_trade(trade)
            closed_count += 1
        
        # Clear state
        job_state.open_positions.clear()
        
        print(f"  ✅ Forced close: {closed_count} positions closed")
        print(f"[{datetime.now()}] forced_close_job completed")
    
    except Exception as e:
        print(f"[{datetime.now()}] Error in forced_close_job: {e}")


async def nightly_backtest_job():
    """Run nightly backtest and refresh metrics.
    
    Runs at 02:00 UTC (23:00 local previous day).
    """
    print(f"\n[{datetime.now()}] Running nightly_backtest_job...")
    
    try:
        store = DataStore()
        
        for symbol in settings.DEFAULT_SYMBOLS:
            try:
                # Load last 12 months of data
                bars = store.read_bars(symbol, "1d")
                
                if len(bars) < 30:
                    print(f"  ⏸️  {symbol}: Insufficient data")
                    continue
                
                # Take last 365 days
                df = pd.DataFrame([bar.to_dict() for bar in bars])
                df = df.sort_values('timestamp').reset_index(drop=True)
                df = df.tail(365).reset_index(drop=True)
                
                # Generate signals
                sig = ma_crossover(df['close'])
                
                # Simple backtest
                returns = df['close'].pct_change()
                strategy_returns = sig.signal.shift(1) * returns
                
                total_return = (1 + strategy_returns).prod() - 1
                sharpe = (strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)) if strategy_returns.std() > 0 else 0
                
                print(f"  ✓ {symbol}: Return {total_return:.2%}, Sharpe {sharpe:.2f}")
            
            except Exception as e:
                print(f"  ✗ Error backtesting {symbol}: {e}")
        
        print(f"[{datetime.now()}] nightly_backtest_job completed")
    
    except Exception as e:
        print(f"[{datetime.now()}] Error in nightly_backtest_job: {e}")


# ============================================================
# SCHEDULER SETUP
# ============================================================

def create_scheduler() -> AsyncIOScheduler:
    """Create and configure APScheduler.
    
    Returns:
        Configured AsyncIOScheduler
    """
    scheduler = AsyncIOScheduler()
    
    if not settings.SCHEDULER_ENABLED:
        print("⚠️  Scheduler is disabled in settings")
        return scheduler
    
    # Data updates - Every 5 minutes
    scheduler.add_job(
        update_data_job,
        trigger=IntervalTrigger(minutes=settings.DATA_UPDATE_INTERVAL),
        id="update_data",
        name="Update OHLCV Data",
        replace_existing=True
    )
    
    # Window A evaluation - During window A (09:00-12:30 local = 12:00-15:30 UTC)
    # Run every 15 minutes during window
    for hour in range(12, 16):  # 12:00-15:00 UTC
        for minute in [0, 15, 30, 45]:
            scheduler.add_job(
                evaluate_window_a_job,
                trigger=CronTrigger(hour=hour, minute=minute),
                id=f"window_a_eval_{hour:02d}{minute:02d}",
                name=f"Window A Eval {hour:02d}:{minute:02d}",
                replace_existing=True
            )
    
    # Watch positions - Every minute during trading hours
    scheduler.add_job(
        watch_positions_job,
        trigger=IntervalTrigger(minutes=1),
        id="watch_positions",
        name="Watch Positions TP/SL",
        replace_existing=True
    )
    
    # Forced close - 19:00 UTC (16:00 local, buffer after 16:45)
    scheduler.add_job(
        forced_close_job,
        trigger=CronTrigger(hour=19, minute=0),
        id="forced_close",
        name="Forced Close EOD",
        replace_existing=True
    )
    
    # Nightly backtest - 02:00 UTC (23:00 previous day local)
    scheduler.add_job(
        nightly_backtest_job,
        trigger=CronTrigger(hour=2, minute=0),
        id="nightly_backtest",
        name="Nightly Backtest & Metrics",
        replace_existing=True
    )
    
    return scheduler


# Global scheduler instance
scheduler = create_scheduler()


def start_scheduler():
    """Start the scheduler."""
    if settings.SCHEDULER_ENABLED and not scheduler.running:
        scheduler.start()
        print("✅ Scheduler started")
        print(f"   Scheduled jobs: {len(scheduler.get_jobs())}")
        for job in scheduler.get_jobs():
            print(f"   - {job.name} (next run: {job.next_run_time})")
        print("🔄 Daily automation is now active")
    else:
        print("⚠️  Scheduler not started (disabled in settings)")
        print("   Manual execution required for all operations")


def stop_scheduler():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped")

