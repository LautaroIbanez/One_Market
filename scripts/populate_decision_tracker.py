"""Script to populate DecisionTracker with backtest results.

This script:
1. Runs backtests on historical data
2. Transforms backtest trades into DailyDecision and DecisionOutcome
3. Saves to decision_history.json and decision_outcomes.json
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.data.store import DataStore
from app.service.decision import DailyDecision, DecisionEngine
from app.service.decision_tracker import DecisionTracker, DecisionOutcome
from app.research.signals import generate_signal, get_strategy_list
from app.research.combine import combine_signals
from app.research.backtest import BacktestEngine, BacktestConfig
from app.core.risk import compute_levels, calculate_atr, calculate_position_size_fixed_risk
from app.service.entry_band import calculate_entry_band
from app.service.tp_sl_engine import calculate_tp_sl, TPSLConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_backtest_trades(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    days_back: int = 90,
    capital: float = 100000.0,
    risk_pct: float = 0.02
) -> pd.DataFrame:
    """Generate backtest trades from historical data.
    
    Returns:
        DataFrame with columns: timestamp, signal, entry_price, sl, tp, exit_price, 
                               pnl, pnl_pct, exit_reason, strategy
    """
    logger.info(f"Loading data for {symbol} {timeframe}")
    
    # Load data
    store = DataStore()
    bars = store.read_bars(symbol, timeframe)
    
    if len(bars) < 100:
        logger.error(f"Insufficient data for {symbol} {timeframe}")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame([bar.to_dict() for bar in bars])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Filter to last N days
    cutoff_ts = int((datetime.utcnow() - timedelta(days=days_back)).timestamp() * 1000)
    df = df[df['timestamp'] >= cutoff_ts].copy()
    
    logger.info(f"Processing {len(df)} bars from {symbol} {timeframe}")
    
    # Generate signals from multiple strategies
    strategies = ['ma_crossover', 'rsi_regime_pullback', 'donchian_breakout_adx']
    strategy_signals = {}
    
    for strategy in strategies:
        try:
            sig = generate_signal(strategy, df)
            strategy_signals[strategy] = sig.signal
        except Exception as e:
            logger.warning(f"Strategy {strategy} failed: {e}")
    
    if not strategy_signals:
        logger.error("No strategies generated signals")
        return pd.DataFrame()
    
    # Combine signals
    returns = df['close'].pct_change()
    combined = combine_signals(
        strategy_signals,
        method='simple_average',
        returns=returns
    )
    
    # Calculate ATR for stops
    df['atr'] = calculate_atr(df['high'], df['low'], df['close'], period=14)
    
    # Simulate trades
    trades = []
    in_position = False
    entry_bar = None
    
    for i in range(1, len(df)):
        current_signal = int(combined.signal.iloc[i])
        current_confidence = float(combined.confidence.iloc[i])
        current_price = df['close'].iloc[i]
        current_atr = df['atr'].iloc[i]
        current_ts = df['timestamp'].iloc[i]
        
        # Entry logic
        if not in_position and current_signal != 0:
            # Calculate entry levels
            try:
                entry_result = calculate_entry_band(
                    df.iloc[:i+1],
                    current_price,
                    current_signal,
                    beta=0.003
                )
                entry_mid = entry_result.entry_price
            except Exception:
                entry_mid = current_price
            
            # Calculate SL/TP
            levels = compute_levels(
                entry_price=entry_mid,
                atr=current_atr,
                side='long' if current_signal > 0 else 'short',
                atr_multiplier_sl=2.0,
                atr_multiplier_tp=3.0
            )
            
            # Position sizing
            pos_size = calculate_position_size_fixed_risk(
                capital=capital,
                risk_pct=risk_pct,
                entry_price=levels.entry_price,
                stop_loss=levels.stop_loss
            )
            
            # Enter position
            in_position = True
            entry_bar = {
                'entry_idx': i,
                'entry_ts': current_ts,
                'signal': current_signal,
                'confidence': current_confidence,
                'entry_price': levels.entry_price,
                'sl': levels.stop_loss,
                'tp': levels.take_profit,
                'atr': current_atr,
                'quantity': pos_size.quantity,
                'risk_amount': pos_size.risk_amount
            }
        
        # Exit logic
        elif in_position and entry_bar is not None:
            exit_price = None
            exit_reason = None
            
            # Check SL
            if entry_bar['signal'] > 0:  # Long
                if df['low'].iloc[i] <= entry_bar['sl']:
                    exit_price = entry_bar['sl']
                    exit_reason = 'SL'
                elif df['high'].iloc[i] >= entry_bar['tp']:
                    exit_price = entry_bar['tp']
                    exit_reason = 'TP'
                elif current_signal <= 0:  # Signal reversal
                    exit_price = current_price
                    exit_reason = 'Signal Reversal'
            else:  # Short
                if df['high'].iloc[i] >= entry_bar['sl']:
                    exit_price = entry_bar['sl']
                    exit_reason = 'SL'
                elif df['low'].iloc[i] <= entry_bar['tp']:
                    exit_price = entry_bar['tp']
                    exit_reason = 'TP'
                elif current_signal >= 0:  # Signal reversal
                    exit_price = current_price
                    exit_reason = 'Signal Reversal'
            
            # Exit position
            if exit_price is not None:
                # Calculate PnL
                if entry_bar['signal'] > 0:
                    pnl = (exit_price - entry_bar['entry_price']) * entry_bar['quantity']
                    pnl_pct = (exit_price / entry_bar['entry_price']) - 1
                else:
                    pnl = (entry_bar['entry_price'] - exit_price) * entry_bar['quantity']
                    pnl_pct = (entry_bar['entry_price'] / exit_price) - 1
                
                trades.append({
                    'entry_ts': entry_bar['entry_ts'],
                    'exit_ts': current_ts,
                    'signal': entry_bar['signal'],
                    'confidence': entry_bar['confidence'],
                    'entry_price': entry_bar['entry_price'],
                    'exit_price': exit_price,
                    'sl': entry_bar['sl'],
                    'tp': entry_bar['tp'],
                    'atr': entry_bar['atr'],
                    'quantity': entry_bar['quantity'],
                    'risk_amount': entry_bar['risk_amount'],
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_reason': exit_reason,
                    'strategy': 'combined'
                })
                
                # Update capital
                capital += pnl
                
                # Reset
                in_position = False
                entry_bar = None
    
    trades_df = pd.DataFrame(trades)
    logger.info(f"Generated {len(trades_df)} trades")
    
    return trades_df


def populate_tracker_from_backtest(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    days_back: int = 90,
    capital: float = 100000.0,
    risk_pct: float = 0.02
) -> None:
    """Populate DecisionTracker from backtest results."""
    
    logger.info(f"Starting backtest for {symbol} {timeframe}")
    
    # Generate backtest trades
    trades_df = generate_backtest_trades(
        symbol=symbol,
        timeframe=timeframe,
        days_back=days_back,
        capital=capital,
        risk_pct=risk_pct
    )
    
    if trades_df.empty:
        logger.error("No trades generated")
        return
    
    # Initialize tracker
    tracker = DecisionTracker()
    
    logger.info(f"Populating tracker with {len(trades_df)} trades")
    
    # Transform trades to decisions and outcomes
    for idx, trade in trades_df.iterrows():
        # Create DailyDecision
        entry_dt = pd.to_datetime(trade['entry_ts'], unit='ms', utc=True)
        
        # Create decision
        decision = DailyDecision(
            decision_date=entry_dt,
            trading_day=entry_dt.strftime('%Y-%m-%d'),
            window='A',  # Assume window A for backtest
            signal=int(trade['signal']),
            signal_strength=float(trade['confidence']),
            signal_source=f"{symbol}_{timeframe}_{trade['strategy']}",
            should_execute=True,
            entry_price=float(trade['entry_price']),
            entry_mid=float(trade['entry_price']),
            entry_band_beta=0.003,
            stop_loss=float(trade['sl']),
            take_profit=float(trade['tp']),
            atr_value=float(trade['atr']),
            position_size=None,  # Will be reconstructed
            window_a_executed=False,
            skip_reason=None,
            market_price=float(trade['entry_price']),
            timestamp_ms=int(trade['entry_ts'])
        )
        
        # Record decision
        decision_id = tracker.record_decision(decision)
        
        # Create outcome
        exit_dt = pd.to_datetime(trade['exit_ts'], unit='ms', utc=True)
        
        tracker.record_outcome(
            decision_id=decision_id,
            outcome_price=float(trade['exit_price']),
            pnl=float(trade['pnl']),
            pnl_pct=float(trade['pnl_pct']),
            was_executed=True,
            execution_price=float(trade['entry_price']),
            exit_price=float(trade['exit_price']),
            exit_reason=trade['exit_reason']
        )
    
    logger.info(f"Successfully populated tracker with {len(trades_df)} decisions and outcomes")
    
    # Print summary
    metrics = tracker.get_performance_metrics(days=days_back)
    logger.info("Performance Metrics:")
    logger.info(f"  Total Decisions: {metrics['total_decisions']}")
    logger.info(f"  Executed: {metrics['executed_decisions']}")
    logger.info(f"  Win Rate: {metrics['win_rate']:.2%}")
    logger.info(f"  Total PnL: ${metrics['total_pnl']:,.2f}")
    logger.info(f"  Avg PnL: ${metrics['avg_pnl']:,.2f}")
    logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate DecisionTracker with backtest data')
    parser.add_argument('--symbol', type=str, default='BTC/USDT', help='Trading symbol')
    parser.add_argument('--timeframe', type=str, default='1h', help='Timeframe')
    parser.add_argument('--days', type=int, default=90, help='Days of history to process')
    parser.add_argument('--capital', type=float, default=100000.0, help='Initial capital')
    parser.add_argument('--risk', type=float, default=0.02, help='Risk per trade (0.02 = 2%)')
    
    args = parser.parse_args()
    
    populate_tracker_from_backtest(
        symbol=args.symbol,
        timeframe=args.timeframe,
        days_back=args.days,
        capital=args.capital,
        risk_pct=args.risk
    )


if __name__ == '__main__':
    main()

