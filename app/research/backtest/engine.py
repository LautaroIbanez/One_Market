"""Backtesting engine using vectorbt.

This module provides the main backtesting engine with support for:
- Vectorized backtesting
- One trade per day enforcement
- Trading windows (A/B)
- Forced close at end of day
- OCO TP/SL orders
- Commission and slippage
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
from pydantic import BaseModel, Field
import warnings

warnings.filterwarnings('ignore')

# Import vectorbt (will be installed via requirements)
try:
    import vectorbt as vbt
    VBT_AVAILABLE = True
except ImportError:
    vbt = None
    VBT_AVAILABLE = False
    warnings.warn("vectorbt not installed. Using fallback engine. Install with: pip install vectorbt")

from app.core.calendar import TradingCalendar
from app.core.risk import compute_levels
from app.research.backtest.rules import (
    enforce_one_trade_per_day,
    filter_by_trading_windows,
    apply_forced_close
)


class BacktestConfig(BaseModel):
    """Configuration for backtest."""
    
    initial_capital: float = Field(default=100000.0, description="Initial capital")
    commission: float = Field(default=0.001, description="Commission rate (0.001 = 0.1%)")
    slippage: float = Field(default=0.0005, description="Slippage rate (0.0005 = 0.05%)")
    
    # Position sizing
    risk_per_trade: float = Field(default=0.02, description="Risk per trade (0.02 = 2%)")
    use_atr_stops: bool = Field(default=True, description="Use ATR-based stops")
    atr_multiplier_sl: float = Field(default=2.0, description="ATR multiplier for SL")
    atr_multiplier_tp: float = Field(default=3.0, description="ATR multiplier for TP")
    
    # Trading rules
    one_trade_per_day: bool = Field(default=True, description="Enforce one trade per day")
    use_trading_windows: bool = Field(default=True, description="Use trading windows A/B")
    use_forced_close: bool = Field(default=True, description="Force close at end of day")
    
    # Trading windows (local time, UTC-3)
    window_a_start: str = Field(default="09:00", description="Window A start (HH:MM)")
    window_a_end: str = Field(default="12:30", description="Window A end (HH:MM)")
    window_b_start: str = Field(default="14:00", description="Window B start (HH:MM)")
    window_b_end: str = Field(default="17:00", description="Window B end (HH:MM)")
    forced_close_time: str = Field(default="16:45", description="Forced close time (HH:MM)")


class BacktestResult(BaseModel):
    """Structured backtest results."""
    
    # Performance metrics
    total_return: float = Field(..., description="Total return")
    cagr: float = Field(..., description="Compound Annual Growth Rate")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    calmar_ratio: float = Field(..., description="Calmar ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    
    # Trade statistics
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate: float = Field(..., description="Win rate (0-1)")
    profit_factor: float = Field(..., description="Profit factor")
    avg_trade: float = Field(..., description="Average trade PnL")
    avg_win: float = Field(..., description="Average winning trade")
    avg_loss: float = Field(..., description="Average losing trade")
    
    # Risk metrics
    volatility: float = Field(..., description="Returns volatility")
    downside_deviation: float = Field(..., description="Downside deviation")
    max_consecutive_losses: int = Field(..., description="Max consecutive losses")
    exposure_time: float = Field(..., description="Time in market (0-1)")
    
    # Additional metrics
    expectancy: float = Field(..., description="Expected value per trade")
    recovery_factor: float = Field(..., description="Total return / Max DD")
    mar_ratio: float = Field(..., description="CAGR / Avg DD")
    
    # Metadata
    strategy_name: str = Field(..., description="Strategy name")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(..., description="Initial capital")
    final_capital: float = Field(..., description="Final capital")
    
    # Detailed trades list
    trades: List[Dict] = Field(default_factory=list, description="Detailed list of all trades executed")
    
    class Config:
        arbitrary_types_allowed = True


class BacktestEngine:
    """Main backtesting engine."""
    
    def __init__(self, config: Optional[BacktestConfig] = None):
        """Initialize backtest engine.
        
        Args:
            config: Backtest configuration
        """
        self.config = config or BacktestConfig()
        self.calendar = None
        
        if self.config.use_trading_windows:
            from datetime import time
            self.calendar = TradingCalendar(
                window_a_start=time(*map(int, self.config.window_a_start.split(':'))),
                window_a_end=time(*map(int, self.config.window_a_end.split(':'))),
                window_b_start=time(*map(int, self.config.window_b_start.split(':'))),
                window_b_end=time(*map(int, self.config.window_b_end.split(':'))),
                forced_close_time=time(*map(int, self.config.forced_close_time.split(':')))
            )
    
    def run(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        strategy_name: str = "Strategy",
        verbose: bool = True
    ) -> BacktestResult:
        """Run backtest on signals.
        
        Args:
            df: DataFrame with OHLCV data
            signals: Signal series (1=long, -1=short, 0=flat)
            strategy_name: Name of strategy
            verbose: Print progress
            
        Returns:
            BacktestResult with metrics
        """
        if not VBT_AVAILABLE:
            if verbose:
                print(f"Using fallback engine for {strategy_name}")
            return self._run_fallback_backtest(df, signals, strategy_name, verbose)
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"Running backtest: {strategy_name}")
            print(f"{'='*60}")
        
        # 1. Apply trading rules
        signals = self._apply_rules(df, signals, verbose)
        
        # 2. Calculate TP/SL levels if using ATR
        if self.config.use_atr_stops:
            tp_stops, sl_stops = self._calculate_atr_stops(df, signals)
        else:
            tp_stops = None
            sl_stops = None
        
        # 3. Run vectorbt backtest
        portfolio = self._run_vectorbt(df, signals, tp_stops, sl_stops, verbose)
        
        # 4. Calculate metrics
        result = self._calculate_metrics(portfolio, strategy_name, df, verbose)
        
        if verbose:
            self._print_summary(result)
        
        return result
    
    def _apply_rules(self, df: pd.DataFrame, signals: pd.Series, verbose: bool) -> pd.Series:
        """Apply trading rules to signals.
        
        Args:
            df: DataFrame with OHLCV data
            signals: Raw signals
            verbose: Print info
            
        Returns:
            Filtered signals
        """
        if verbose:
            print(f"\nApplying trading rules...")
            print(f"  Original signals: {(signals != 0).sum()}")
        
        # One trade per day
        if self.config.one_trade_per_day:
            signals = enforce_one_trade_per_day(signals, df['timestamp'])
            if verbose:
                print(f"  After 1/day rule: {(signals != 0).sum()}")
        
        # Trading windows
        if self.config.use_trading_windows and self.calendar:
            signals = filter_by_trading_windows(signals, df['timestamp'], self.calendar)
            if verbose:
                print(f"  After windows filter: {(signals != 0).sum()}")
        
        return signals
    
    def _calculate_atr_stops(
        self,
        df: pd.DataFrame,
        signals: pd.Series
    ) -> Tuple[pd.Series, pd.Series]:
        """Calculate ATR-based TP/SL stops.
        
        Args:
            df: DataFrame with OHLCV data
            signals: Filtered signals
            
        Returns:
            Tuple of (tp_stops, sl_stops) as percentage series
        """
        from app.research.indicators import atr
        
        # Calculate ATR
        atr_val = atr(df['high'], df['low'], df['close'], period=14)
        
        # Calculate stop percentages
        tp_pct = (atr_val * self.config.atr_multiplier_tp) / df['close']
        sl_pct = (atr_val * self.config.atr_multiplier_sl) / df['close']
        
        return tp_pct, sl_pct
    
    def _run_vectorbt(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        tp_stops: Optional[pd.Series],
        sl_stops: Optional[pd.Series],
        verbose: bool
    ):
        """Run vectorbt backtest.
        
        Args:
            df: DataFrame with OHLCV data
            signals: Filtered signals
            tp_stops: Take profit stops (optional)
            sl_stops: Stop loss stops (optional)
            verbose: Print info
            
        Returns:
            vectorbt Portfolio object
        """
        if verbose:
            print(f"\nRunning vectorbt backtest...")
        
        # Separate long and short entries
        long_entries = signals == 1
        short_entries = signals == -1
        
        # Create portfolio
        portfolio = vbt.Portfolio.from_signals(
            close=df['close'],
            entries=long_entries,
            short_entries=short_entries,
            tp_stop=tp_stops if tp_stops is not None else None,
            sl_stop=sl_stops if sl_stops is not None else None,
            fees=self.config.commission,
            slippage=self.config.slippage,
            init_cash=self.config.initial_capital,
            freq='1H'  # Adjust based on data
        )
        
        return portfolio
    
    def _calculate_metrics(
        self,
        portfolio,
        strategy_name: str,
        df: pd.DataFrame,
        verbose: bool
    ) -> BacktestResult:
        """Calculate performance metrics from portfolio.
        
        Args:
            portfolio: vectorbt Portfolio
            strategy_name: Strategy name
            df: Original DataFrame
            verbose: Print info
            
        Returns:
            BacktestResult with all metrics
        """
        if verbose:
            print(f"\nCalculating metrics...")
        
        # Get basic stats
        stats = portfolio.stats()
        
        # Returns
        returns = portfolio.returns()
        total_return = portfolio.total_return()
        
        # Drawdown
        portfolio_value = portfolio.value()
        running_max = portfolio_value.expanding().max()
        drawdown = (portfolio_value - running_max) / running_max
        max_dd = drawdown.min()  # max_drawdown is the minimum value (most negative)
        
        # Trades
        trades = portfolio.trades.records
        num_trades = len(trades)
        
        if num_trades > 0:
            winning_trades = (trades['pnl'] > 0).sum()
            losing_trades = (trades['pnl'] < 0).sum()
            win_rate = winning_trades / num_trades if num_trades > 0 else 0
            
            wins = trades[trades['pnl'] > 0]['pnl']
            losses = trades[trades['pnl'] < 0]['pnl']
            
            avg_win = wins.mean() if len(wins) > 0 else 0
            avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
            avg_trade = trades['pnl'].mean()
            
            profit_factor = abs(wins.sum() / losses.sum()) if len(losses) > 0 and losses.sum() != 0 else 0
            
            # Expectancy
            expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
            
            # Max consecutive losses
            trade_results = (trades['pnl'] < 0).astype(int)
            max_consecutive = 0
            current_consecutive = 0
            for result in trade_results:
                if result:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0
        else:
            winning_trades = 0
            losing_trades = 0
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            avg_trade = 0
            profit_factor = 0
            expectancy = 0
            max_consecutive = 0
        
        # Risk metrics
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        # Downside deviation
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        
        # Sharpe ratio
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() != 0 else 0
        
        # Sortino ratio
        sortino = (returns.mean() / downside_deviation * np.sqrt(252)) if downside_deviation != 0 else 0
        
        # CAGR
        days = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]) / (1000 * 60 * 60 * 24)
        years = days / 365.25
        cagr = ((1 + total_return) ** (1 / years) - 1) if years > 0 else 0
        
        # Calmar ratio
        calmar = cagr / abs(max_dd) if max_dd != 0 else 0
        
        # Recovery factor
        recovery_factor = total_return / abs(max_dd) if max_dd != 0 else 0
        
        # MAR ratio (using average drawdown)
        avg_dd = abs(drawdown.mean())
        mar_ratio = cagr / avg_dd if avg_dd != 0 else 0
        
        # Exposure time
        exposure = portfolio.positions.records.size / len(df) if hasattr(portfolio.positions, 'records') else 0
        
        # Dates
        start_date = pd.to_datetime(df['timestamp'].iloc[0], unit='ms')
        end_date = pd.to_datetime(df['timestamp'].iloc[-1], unit='ms')
        
        # Final capital
        final_capital = portfolio.final_value()
        
        return BacktestResult(
            total_return=float(total_return),
            cagr=float(cagr),
            sharpe_ratio=float(sharpe),
            sortino_ratio=float(sortino),
            calmar_ratio=float(calmar),
            max_drawdown=float(max_dd),
            total_trades=int(num_trades),
            winning_trades=int(winning_trades),
            losing_trades=int(losing_trades),
            win_rate=float(win_rate),
            profit_factor=float(profit_factor),
            avg_trade=float(avg_trade),
            avg_win=float(avg_win),
            avg_loss=float(avg_loss),
            volatility=float(volatility),
            downside_deviation=float(downside_deviation),
            max_consecutive_losses=int(max_consecutive),
            exposure_time=float(exposure),
            expectancy=float(expectancy),
            recovery_factor=float(recovery_factor),
            mar_ratio=float(mar_ratio),
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=float(self.config.initial_capital),
            final_capital=float(final_capital)
        )
    
    def _print_summary(self, result: BacktestResult):
        """Print backtest summary.
        
        Args:
            result: BacktestResult
        """
        print(f"\n{'='*60}")
        print(f"BACKTEST RESULTS: {result.strategy_name}")
        print(f"{'='*60}")
        
        print(f"\n📊 Performance:")
        print(f"  Total Return: {result.total_return:.2%}")
        print(f"  CAGR: {result.cagr:.2%}")
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"  Sortino Ratio: {result.sortino_ratio:.2f}")
        print(f"  Calmar Ratio: {result.calmar_ratio:.2f}")
        print(f"  Max Drawdown: {result.max_drawdown:.2%}")
        
        print(f"\n📈 Trades:")
        print(f"  Total Trades: {result.total_trades}")
        print(f"  Win Rate: {result.win_rate:.2%}")
        print(f"  Profit Factor: {result.profit_factor:.2f}")
        print(f"  Avg Trade: ${result.avg_trade:.2f}")
        print(f"  Avg Win: ${result.avg_win:.2f}")
        print(f"  Avg Loss: ${result.avg_loss:.2f}")
        print(f"  Expectancy: ${result.expectancy:.2f}")
        
        print(f"\n⚠️  Risk:")
        print(f"  Volatility: {result.volatility:.2%}")
        print(f"  Downside Dev: {result.downside_deviation:.2%}")
        print(f"  Max Consecutive Losses: {result.max_consecutive_losses}")
        print(f"  Exposure: {result.exposure_time:.2%}")
        
        print(f"\n💰 Capital:")
        print(f"  Initial: ${result.initial_capital:,.2f}")
        print(f"  Final: ${result.final_capital:,.2f}")
        print(f"  Profit: ${result.final_capital - result.initial_capital:,.2f}")
        
        print(f"\n📅 Period:")
        print(f"  From: {result.start_date.strftime('%Y-%m-%d')}")
        print(f"  To: {result.end_date.strftime('%Y-%m-%d')}")
        print(f"{'='*60}\n")
    
    def _run_fallback_backtest(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        strategy_name: str = "Strategy",
        verbose: bool = True
    ) -> BacktestResult:
        """Run fallback backtest without vectorbt.
        
        Args:
            df: DataFrame with OHLCV data
            signals: Signal series (1=long, -1=short, 0=flat)
            strategy_name: Name of strategy
            verbose: Print progress
            
        Returns:
            BacktestResult with metrics
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Running fallback backtest: {strategy_name}")
            print(f"{'='*60}")
        
        # Simple backtest logic
        trades = []
        capital = self.config.initial_capital
        position = 0
        entry_price = 0
        entry_time = None
        
        for i, (timestamp, row) in enumerate(df.iterrows()):
            signal = signals.iloc[i] if i < len(signals) else 0
            price = row['close']
            
            # Entry logic
            if signal != 0 and position == 0:
                # Calculate position size based on risk
                risk_amount = capital * self.config.risk_per_trade
                position_size = risk_amount / price
                
                position = position_size
                entry_price = price
                entry_time = timestamp
                
                if verbose and i % 100 == 0:
                    print(f"Entry at {price:.2f}, position: {position:.4f}")
            
            # Exit logic
            elif position != 0 and signal == 0:
                # Calculate PnL
                pnl = (price - entry_price) * position
                pnl_pct = pnl / (entry_price * position) if position > 0 else 0
                
                # Apply commission and slippage
                commission = abs(position * price * self.config.commission)
                slippage = abs(position * price * self.config.slippage)
                net_pnl = pnl - commission - slippage
                
                # Calculate holding time
                holding_time = (timestamp - entry_time).total_seconds() / 3600 if isinstance(timestamp, datetime) and isinstance(entry_time, datetime) else 0
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': timestamp,
                    'entry_price': entry_price,
                    'exit_price': price,
                    'quantity': position,
                    'side': 'LONG',  # Simplified for fallback
                    'pnl': net_pnl,
                    'pnl_pct': pnl_pct,
                    'pnl_gross': pnl,
                    'commission': commission,
                    'slippage': slippage,
                    'holding_time_hours': holding_time,
                    'status': 'CLOSED'
                })
                
                capital += net_pnl
                position = 0
                entry_price = 0
                entry_time = None
        
        # Calculate metrics
        if not trades:
            return BacktestResult(
                strategy_name=strategy_name,
                start_date=df.index[0],
                end_date=df.index[-1],
                initial_capital=self.config.initial_capital,
                final_capital=self.config.initial_capital,
                total_return=0.0,
                cagr=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                max_drawdown=0.0,
                volatility=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                expectancy=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0.0,
                avg_loss=0.0,
                trades=trades
            )
        
        # Calculate comprehensive metrics
        from app.utils.metrics_helper import MetricsCalculator
        
        calculator = MetricsCalculator()
        equity_curve = [self.config.initial_capital]
        for trade in trades:
            equity_curve.append(equity_curve[-1] + trade['pnl'])
        
        # Handle empty DataFrame
        if len(df) == 0:
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
        else:
            start_date = df.index[0]
            end_date = df.index[-1]
        
        metrics = calculator.calculate_comprehensive_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=self.config.initial_capital,
            start_date=start_date,
            end_date=end_date
        )
        
        if verbose:
            print(f"Fallback backtest completed: {len(trades)} trades")
            print(f"Final capital: ${capital:.2f}")
        
        return BacktestResult(
            strategy_name=strategy_name,
            start_date=df.index[0],
            end_date=df.index[-1],
            initial_capital=self.config.initial_capital,
            final_capital=capital,
            total_return=metrics['total_return'],
            cagr=metrics['cagr'],
            sharpe_ratio=metrics['sharpe_ratio'],
            sortino_ratio=metrics['sortino_ratio'],
            calmar_ratio=metrics['calmar_ratio'],
            max_drawdown=metrics['max_drawdown'],
            volatility=metrics['volatility'],
            win_rate=metrics['win_rate'],
            profit_factor=metrics['profit_factor'],
            expectancy=metrics['expectancy'],
            total_trades=metrics['total_trades'],
            winning_trades=metrics['winning_trades'],
            losing_trades=metrics['losing_trades'],
            avg_win=metrics['avg_win'],
            avg_loss=metrics['avg_loss'],
            trades=trades
        )

