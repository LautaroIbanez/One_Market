"""Example usage of core quantitative modules.

This example demonstrates how to use the timeframes, calendar, risk, and utils
modules for building trading strategies and managing positions.
"""
from datetime import datetime, time
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np

from app.core.timeframes import (
    Timeframe,
    get_timeframe_ms,
    get_bars_per_day,
    convert_bars_between_timeframes
)
from app.core.calendar import (
    TradingCalendar,
    utc_to_local,
    local_to_utc
)
from app.core.risk import (
    compute_levels,
    calculate_position_size_fixed_risk,
    calculate_position_size_kelly_simple,
    calculate_atr_from_bars,
    calculate_sharpe_ratio,
    calculate_max_drawdown
)
from app.core.utils import (
    ensure_utc,
    prevent_lookahead,
    calculate_pnl,
    calculate_returns,
    format_currency,
    format_percentage,
    safe_divide
)


def example_timeframes():
    """Example: Working with timeframes."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Timeframes")
    print("="*60)
    
    # Using Timeframe enum
    tf = Timeframe.H1
    print(f"\nTimeframe: {tf}")
    print(f"  Milliseconds: {tf.milliseconds:,}")
    print(f"  Hours: {tf.hours}")
    print(f"  Days: {tf.days}")
    
    # Converting between timeframes
    bars_per_day = get_bars_per_day("1h")
    print(f"\nBars per day (1h): {bars_per_day}")
    
    # Converting bars
    daily_bars = 30
    hourly_bars = convert_bars_between_timeframes("1d", "1h", daily_bars)
    print(f"{daily_bars} daily bars = {hourly_bars} hourly bars")
    
    # Navigating timeframe hierarchy
    print(f"\nTimeframe hierarchy:")
    print(f"  M15 → higher: {Timeframe.M15.to_higher_timeframe()}")
    print(f"  H1 → higher: {Timeframe.H1.to_higher_timeframe()}")
    print(f"  H1 → lower: {Timeframe.H1.to_lower_timeframe()}")


def example_calendar():
    """Example: Working with trading calendar."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Trading Calendar")
    print("="*60)
    
    # Create trading calendar with custom windows
    calendar = TradingCalendar(
        window_a_start=time(9, 0),
        window_a_end=time(12, 30),
        window_b_start=time(14, 0),
        window_b_end=time(17, 0),
        forced_close_time=time(16, 45)
    )
    
    # Check current trading status
    now = datetime.now(ZoneInfo("UTC"))
    print(f"\nCurrent time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Local time (UTC-3): {utc_to_local(now).strftime('%Y-%m-%d %H:%M:%S')}")
    
    is_trading = calendar.is_trading_hours(now)
    current_window = calendar.get_current_window(now)
    should_close = calendar.should_force_close(now)
    
    print(f"\nTrading Status:")
    print(f"  Is trading hours: {is_trading}")
    print(f"  Current window: {current_window if current_window else 'Outside trading hours'}")
    print(f"  Should force close: {should_close}")
    
    if not should_close:
        time_until_close = calendar.time_until_forced_close(now)
        hours_until_close = time_until_close.total_seconds() / 3600
        print(f"  Time until forced close: {hours_until_close:.1f} hours")
    
    # Check if valid time to enter trade
    is_valid_entry = calendar.is_valid_entry_time(now, min_time_before_close_minutes=30)
    print(f"  Valid entry time: {is_valid_entry}")


def example_risk_management():
    """Example: Risk management and position sizing."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Risk Management")
    print("="*60)
    
    # Sample OHLCV data for ATR calculation
    bars = [
        {'high': 51000, 'low': 49500, 'close': 50000},
        {'high': 50800, 'low': 49200, 'close': 50500},
        {'high': 51200, 'low': 49800, 'close': 50800},
        {'high': 51500, 'low': 50000, 'close': 51000},
        {'high': 52000, 'low': 50500, 'close': 51500},
        {'high': 51800, 'low': 50800, 'close': 51200},
        {'high': 52200, 'low': 51000, 'close': 51800},
        {'high': 52500, 'low': 51300, 'close': 52000},
        {'high': 52800, 'low': 51500, 'close': 52300},
        {'high': 53000, 'low': 51800, 'close': 52500},
        {'high': 53200, 'low': 52000, 'close': 52800},
        {'high': 53500, 'low': 52300, 'close': 53000},
        {'high': 53800, 'low': 52500, 'close': 53200},
        {'high': 54000, 'low': 52800, 'close': 53500},
        {'high': 54200, 'low': 53000, 'close': 53800}
    ]
    
    # Calculate ATR
    atr = calculate_atr_from_bars(bars, period=14)
    print(f"\nATR (14): {format_currency(atr, decimals=2)}")
    
    # Compute SL/TP levels for a long position
    entry_price = 53800
    levels = compute_levels(
        entry_price=entry_price,
        atr=atr,
        side="long",
        atr_multiplier_sl=2.0,
        atr_multiplier_tp=3.0,
        min_rr_ratio=1.5
    )
    
    print(f"\nLong Position Setup:")
    print(f"  Entry: {format_currency(levels.entry_price)}")
    print(f"  Stop Loss: {format_currency(levels.stop_loss)} ({format_percentage(levels.stop_loss_pct)})")
    print(f"  Take Profit: {format_currency(levels.take_profit)} ({format_percentage(levels.take_profit_pct)})")
    print(f"  Risk/Reward: {levels.risk_reward_ratio:.2f}")
    print(f"  Risk per unit: {format_currency(levels.risk_amount)}")
    
    # Calculate position size with fixed risk
    capital = 100000
    risk_pct = 0.02  # 2% risk per trade
    
    position = calculate_position_size_fixed_risk(
        capital=capital,
        risk_pct=risk_pct,
        entry_price=levels.entry_price,
        stop_loss=levels.stop_loss,
        leverage=1.0
    )
    
    print(f"\nPosition Sizing (Fixed Risk):")
    print(f"  Capital: {format_currency(capital)}")
    print(f"  Risk: {format_percentage(risk_pct)}")
    print(f"  Position size: {position.quantity:.4f} units")
    print(f"  Notional value: {format_currency(position.notional_value)}")
    print(f"  Risk amount: {format_currency(position.risk_amount)}")
    
    # Calculate position size with Kelly Criterion
    kelly_risk_pct = calculate_position_size_kelly_simple(
        capital=capital,
        win_rate=0.55,
        risk_reward_ratio=levels.risk_reward_ratio,
        kelly_fraction=0.25,  # Quarter Kelly
        max_risk_pct=0.05
    )
    
    print(f"\nPosition Sizing (Kelly Criterion):")
    print(f"  Win rate: 55%")
    print(f"  R/R ratio: {levels.risk_reward_ratio:.2f}")
    print(f"  Kelly fraction: 0.25 (quarter Kelly)")
    print(f"  Recommended risk: {format_percentage(kelly_risk_pct)}")
    
    if kelly_risk_pct > 0:
        kelly_position = calculate_position_size_fixed_risk(
            capital=capital,
            risk_pct=kelly_risk_pct,
            entry_price=levels.entry_price,
            stop_loss=levels.stop_loss
        )
        print(f"  Position size: {kelly_position.quantity:.4f} units")
        print(f"  Notional value: {format_currency(kelly_position.notional_value)}")


def example_performance_metrics():
    """Example: Performance metrics calculation."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Performance Metrics")
    print("="*60)
    
    # Simulate a series of trades
    trades = [
        {'entry': 50000, 'exit': 51000, 'quantity': 1.0, 'side': 'long'},
        {'entry': 51000, 'exit': 50500, 'quantity': 1.0, 'side': 'long'},
        {'entry': 50500, 'exit': 51500, 'quantity': 1.0, 'side': 'long'},
        {'entry': 51500, 'exit': 51200, 'quantity': 1.0, 'side': 'long'},
        {'entry': 51200, 'exit': 52200, 'quantity': 1.0, 'side': 'long'},
        {'entry': 52200, 'exit': 51800, 'quantity': 1.0, 'side': 'long'},
        {'entry': 51800, 'exit': 52800, 'quantity': 1.0, 'side': 'long'},
        {'entry': 52800, 'exit': 53500, 'quantity': 1.0, 'side': 'long'}
    ]
    
    # Calculate PnL for each trade
    pnls = []
    for trade in trades:
        pnl = calculate_pnl(
            entry_price=trade['entry'],
            exit_price=trade['exit'],
            quantity=trade['quantity'],
            side=trade['side']
        )
        pnls.append(pnl)
    
    # Calculate metrics
    total_trades = len(pnls)
    winning_trades = sum(1 for pnl in pnls if pnl > 0)
    losing_trades = sum(1 for pnl in pnls if pnl < 0)
    win_rate = safe_divide(winning_trades, total_trades, default=0)
    
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [abs(pnl) for pnl in pnls if pnl < 0]
    
    avg_win = np.mean(wins) if wins else 0
    avg_loss = np.mean(losses) if losses else 0
    
    total_pnl = sum(pnls)
    
    print(f"\nTrade Statistics:")
    print(f"  Total trades: {total_trades}")
    print(f"  Winning trades: {winning_trades}")
    print(f"  Losing trades: {losing_trades}")
    print(f"  Win rate: {format_percentage(win_rate)}")
    
    print(f"\nPnL Statistics:")
    print(f"  Total PnL: {format_currency(total_pnl)}")
    print(f"  Average win: {format_currency(avg_win)}")
    print(f"  Average loss: {format_currency(avg_loss)}")
    
    if avg_loss > 0:
        profit_factor = avg_win / avg_loss
        print(f"  Profit factor: {profit_factor:.2f}")
    
    # Calculate equity curve
    initial_capital = 100000
    equity_curve = [initial_capital]
    for pnl in pnls:
        equity_curve.append(equity_curve[-1] + pnl)
    
    equity_series = pd.Series(equity_curve)
    
    # Calculate max drawdown
    max_dd, peak_idx, trough_idx = calculate_max_drawdown(equity_series)
    
    print(f"\nDrawdown Analysis:")
    print(f"  Initial capital: {format_currency(initial_capital)}")
    print(f"  Final capital: {format_currency(equity_curve[-1])}")
    print(f"  Total return: {format_percentage((equity_curve[-1] - initial_capital) / initial_capital)}")
    print(f"  Max drawdown: {format_percentage(max_dd)}")
    
    # Calculate returns and Sharpe ratio
    returns = pd.Series(pnls) / initial_capital
    sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.0, periods_per_year=252)
    
    print(f"\nRisk-Adjusted Metrics:")
    print(f"  Sharpe ratio: {sharpe:.2f}")


def example_lookahead_prevention():
    """Example: Preventing lookahead bias."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Lookahead Prevention")
    print("="*60)
    
    # Create sample data with signals
    df = pd.DataFrame({
        'timestamp': pd.date_range('2023-10-01', periods=10, freq='1H'),
        'close': [50000, 50100, 50200, 50150, 50300, 50250, 50400, 50500, 50450, 50600],
        'signal': [0, 1, 0, 0, 1, 0, -1, 0, 0, 1]
    })
    
    print("\nOriginal DataFrame (with lookahead bias):")
    print(df[['timestamp', 'close', 'signal']].head())
    
    # Apply lookahead prevention
    df_clean = prevent_lookahead(df, signal_column='signal', shift_periods=1)
    
    print("\nCorrected DataFrame (lookahead prevented):")
    print(df_clean[['timestamp', 'close', 'signal']].head())
    
    print("\nExplanation:")
    print("  Signals are shifted by 1 period to ensure that a signal generated")
    print("  at bar N can only be acted upon at bar N+1.")
    print("  This prevents using future information in backtesting.")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("ONE MARKET - Core Modules Usage Examples")
    print("="*60)
    
    try:
        example_timeframes()
        example_calendar()
        example_risk_management()
        example_performance_metrics()
        example_lookahead_prevention()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

