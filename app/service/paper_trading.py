"""Paper trading database and tracking.

This module provides SQLite-based storage for paper trading:
- Decision history
- Trade execution
- Performance tracking
"""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import json

from app.data.paper_trading_schemas import DecisionRecord, TradeRecord, PerformanceMetrics
from app.config.settings import settings


class PaperTradingDB:
    """Paper trading database manager."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize paper trading database.
        
        Args:
            db_path: Path to SQLite database (defaults to storage/paper_trading.db)
        """
        if db_path is None:
            db_path = settings.STORAGE_PATH / "paper_trading.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Decisions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    trading_day TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    signal INTEGER NOT NULL,
                    signal_strength REAL,
                    signal_source TEXT,
                    entry_price REAL,
                    entry_mid REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    position_size REAL,
                    risk_amount REAL,
                    risk_pct REAL,
                    executed BOOLEAN,
                    skip_reason TEXT,
                    window TEXT
                )
            """)
            
            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    decision_id TEXT NOT NULL,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT,
                    duration_hours REAL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    quantity REAL NOT NULL,
                    notional_value REAL NOT NULL,
                    realized_pnl REAL,
                    realized_pnl_pct REAL,
                    exit_reason TEXT,
                    status TEXT DEFAULT 'open',
                    FOREIGN KEY (decision_id) REFERENCES decisions (decision_id)
                )
            """)
            
            # Strategy Rankings table (NEW)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_rankings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    
                    -- Performance metrics
                    total_return REAL,
                    cagr REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    win_rate REAL,
                    profit_factor REAL,
                    expectancy REAL,
                    
                    -- Risk metrics
                    volatility REAL,
                    calmar_ratio REAL,
                    sortino_ratio REAL,
                    
                    -- Trade statistics
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    avg_win REAL,
                    avg_loss REAL,
                    
                    -- Ranking
                    composite_score REAL,
                    rank INTEGER,
                    
                    -- Config
                    capital REAL,
                    risk_pct REAL,
                    lookback_days INTEGER
                )
            """)
            
            # Strategy Performance History table (NEW)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    UNIQUE(date, symbol, timeframe, strategy_name, metric_name)
                )
            """)
            
            # Truth Data table (NEW) - Real vs Simulated comparison
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS truth_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    
                    -- Real performance
                    real_trades INTEGER DEFAULT 0,
                    real_wins INTEGER DEFAULT 0,
                    real_pnl REAL DEFAULT 0,
                    real_win_rate REAL,
                    
                    -- Simulated performance (backtest)
                    sim_trades INTEGER DEFAULT 0,
                    sim_wins INTEGER DEFAULT 0,
                    sim_pnl REAL DEFAULT 0,
                    sim_win_rate REAL,
                    
                    -- Divergence metrics
                    pnl_divergence_pct REAL,
                    win_rate_divergence_pct REAL,
                    
                    -- Alerts
                    alert_triggered BOOLEAN DEFAULT 0,
                    alert_reason TEXT
                )
            """)
            
            # Metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    initial_capital REAL NOT NULL,
                    current_capital REAL NOT NULL,
                    peak_capital REAL NOT NULL,
                    total_return REAL,
                    total_pnl REAL,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    avg_win REAL DEFAULT 0,
                    avg_loss REAL DEFAULT 0,
                    largest_win REAL DEFAULT 0,
                    largest_loss REAL DEFAULT 0,
                    profit_factor REAL DEFAULT 0,
                    max_drawdown REAL DEFAULT 0,
                    current_drawdown REAL DEFAULT 0,
                    sharpe_ratio REAL DEFAULT 0,
                    sortino_ratio REAL DEFAULT 0,
                    last_updated TEXT NOT NULL
                )
            """)
            
            # Create indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_day ON decisions(trading_day)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_symbol ON decisions(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
            
            conn.commit()
    
    def save_decision(self, decision: DecisionRecord):
        """Save decision to database.
        
        Args:
            decision: DecisionRecord to save
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO decisions VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                decision.decision_id,
                decision.timestamp.isoformat(),
                decision.trading_day,
                decision.symbol,
                decision.timeframe,
                decision.signal,
                decision.signal_strength,
                decision.signal_source,
                decision.entry_price,
                decision.entry_mid,
                decision.stop_loss,
                decision.take_profit,
                decision.position_size,
                decision.risk_amount,
                decision.risk_pct,
                decision.executed,
                decision.skip_reason,
                decision.window
            ))
            conn.commit()
    
    def save_trade(self, trade: TradeRecord):
        """Save trade to database.
        
        Args:
            trade: TradeRecord to save
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO trades VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                trade.trade_id,
                trade.decision_id,
                trade.entry_time.isoformat(),
                trade.exit_time.isoformat() if trade.exit_time else None,
                trade.duration_hours,
                trade.symbol,
                trade.side,
                trade.entry_price,
                trade.exit_price,
                trade.stop_loss,
                trade.take_profit,
                trade.quantity,
                trade.notional_value,
                trade.realized_pnl,
                trade.realized_pnl_pct,
                trade.exit_reason,
                trade.status
            ))
            conn.commit()
    
    def get_open_trades(self, symbol: Optional[str] = None) -> List[TradeRecord]:
        """Get all open trades.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of open TradeRecords
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if symbol:
                cursor.execute("SELECT * FROM trades WHERE status = 'open' AND symbol = ?", (symbol,))
            else:
                cursor.execute("SELECT * FROM trades WHERE status = 'open'")
            
            rows = cursor.fetchall()
            
            trades = []
            for row in rows:
                trades.append(TradeRecord(
                    trade_id=row['trade_id'],
                    decision_id=row['decision_id'],
                    entry_time=datetime.fromisoformat(row['entry_time']),
                    exit_time=datetime.fromisoformat(row['exit_time']) if row['exit_time'] else None,
                    duration_hours=row['duration_hours'],
                    symbol=row['symbol'],
                    side=row['side'],
                    entry_price=row['entry_price'],
                    exit_price=row['exit_price'],
                    stop_loss=row['stop_loss'],
                    take_profit=row['take_profit'],
                    quantity=row['quantity'],
                    notional_value=row['notional_value'],
                    realized_pnl=row['realized_pnl'],
                    realized_pnl_pct=row['realized_pnl_pct'],
                    exit_reason=row['exit_reason'],
                    status=row['status']
                ))
            
            return trades
    
    def get_all_trades(self, symbol: Optional[str] = None) -> List[TradeRecord]:
        """Get all trades (open and closed).
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of all TradeRecords
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if symbol:
                cursor.execute("SELECT * FROM trades WHERE symbol = ? ORDER BY entry_time DESC", (symbol,))
            else:
                cursor.execute("SELECT * FROM trades ORDER BY entry_time DESC")
            
            rows = cursor.fetchall()
            
            trades = []
            for row in rows:
                trades.append(TradeRecord(
                    trade_id=row['trade_id'],
                    decision_id=row['decision_id'],
                    entry_time=datetime.fromisoformat(row['entry_time']),
                    exit_time=datetime.fromisoformat(row['exit_time']) if row['exit_time'] else None,
                    duration_hours=row['duration_hours'],
                    symbol=row['symbol'],
                    side=row['side'],
                    entry_price=row['entry_price'],
                    exit_price=row['exit_price'],
                    stop_loss=row['stop_loss'],
                    take_profit=row['take_profit'],
                    quantity=row['quantity'],
                    notional_value=row['notional_value'],
                    realized_pnl=row['realized_pnl'],
                    realized_pnl_pct=row['realized_pnl_pct'],
                    exit_reason=row['exit_reason'],
                    status=row['status']
                ))
            
            return trades
    
    def get_decisions_by_day(self, trading_day: str) -> List[DecisionRecord]:
        """Get all decisions for a trading day.
        
        Args:
            trading_day: Trading day (YYYY-MM-DD)
            
        Returns:
            List of DecisionRecords
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE trading_day = ?", (trading_day,))
            rows = cursor.fetchall()
            
            decisions = []
            for row in rows:
                decisions.append(DecisionRecord(
                    decision_id=row['decision_id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    trading_day=row['trading_day'],
                    symbol=row['symbol'],
                    timeframe=row['timeframe'],
                    signal=row['signal'],
                    signal_strength=row['signal_strength'],
                    signal_source=row['signal_source'],
                    entry_price=row['entry_price'],
                    entry_mid=row['entry_mid'],
                    stop_loss=row['stop_loss'],
                    take_profit=row['take_profit'],
                    position_size=row['position_size'],
                    risk_amount=row['risk_amount'],
                    risk_pct=row['risk_pct'],
                    executed=bool(row['executed']),
                    skip_reason=row['skip_reason'],
                    window=row['window']
                ))
            
            return decisions
    
    # ============================================================
    # Strategy Rankings Methods (NEW)
    # ============================================================
    
    def save_strategy_ranking(
        self,
        result,
        composite_score: float,
        rank: int
    ):
        """Save strategy ranking to database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO strategy_rankings (
                    timestamp, symbol, timeframe, strategy_name,
                    total_return, cagr, sharpe_ratio, max_drawdown, win_rate,
                    profit_factor, expectancy, volatility, calmar_ratio, sortino_ratio,
                    total_trades, winning_trades, losing_trades, avg_win, avg_loss,
                    composite_score, rank, capital, risk_pct, lookback_days
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.timestamp.isoformat(),
                "UNKNOWN",  # Symbol from context
                "UNKNOWN",  # Timeframe from context
                result.strategy_name,
                result.total_return,
                result.cagr,
                result.sharpe_ratio,
                result.max_drawdown,
                result.win_rate,
                result.profit_factor,
                result.expectancy,
                result.volatility,
                result.calmar_ratio,
                result.sortino_ratio,
                result.total_trades,
                result.winning_trades,
                result.losing_trades,
                result.avg_win,
                result.avg_loss,
                composite_score,
                rank,
                result.capital,
                result.risk_pct,
                result.lookback_days
            ))
            conn.commit()
    
    def get_strategy_rankings(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get latest strategy rankings."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM strategy_rankings WHERE 1=1"
            params = []
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if timeframe:
                query += " AND timeframe = ?"
                params.append(timeframe)
            
            query += " ORDER BY timestamp DESC, rank ASC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def save_strategy_performance_metric(
        self,
        date: str,
        symbol: str,
        timeframe: str,
        strategy_name: str,
        metric_name: str,
        metric_value: float
    ):
        """Save daily performance metric for a strategy."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO strategy_performance 
                (date, symbol, timeframe, strategy_name, metric_name, metric_value)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (date, symbol, timeframe, strategy_name, metric_name, metric_value))
            conn.commit()
    
    def get_strategy_performance_history(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        metric_name: str,
        days: int = 30
    ) -> List[Dict]:
        """Get performance history for a strategy."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM strategy_performance
                WHERE strategy_name = ? AND symbol = ? AND timeframe = ? AND metric_name = ?
                ORDER BY date DESC
                LIMIT ?
            """, (strategy_name, symbol, timeframe, metric_name, days))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ============================================================
    # Truth Data Methods (NEW)
    # ============================================================
    
    def save_truth_data(
        self,
        date: str,
        symbol: str,
        timeframe: str,
        strategy_name: str,
        real_metrics: Dict,
        sim_metrics: Dict
    ):
        """Save comparison between real and simulated performance."""
        # Calculate divergence
        pnl_div = None
        if sim_metrics.get('pnl', 0) != 0:
            pnl_div = ((real_metrics.get('pnl', 0) - sim_metrics.get('pnl', 0)) / abs(sim_metrics['pnl'])) * 100
        
        wr_div = None
        if sim_metrics.get('win_rate'):
            wr_div = (real_metrics.get('win_rate', 0) - sim_metrics.get('win_rate', 0)) * 100
        
        # Check for alert triggers
        alert_triggered = False
        alert_reason = None
        
        if pnl_div and abs(pnl_div) > 20:  # 20% divergence threshold
            alert_triggered = True
            alert_reason = f"PnL divergence: {pnl_div:.1f}%"
        elif wr_div and abs(wr_div) > 15:  # 15% win rate divergence
            alert_triggered = True
            alert_reason = f"Win rate divergence: {wr_div:.1f}%"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO truth_data (
                    date, symbol, timeframe, strategy_name,
                    real_trades, real_wins, real_pnl, real_win_rate,
                    sim_trades, sim_wins, sim_pnl, sim_win_rate,
                    pnl_divergence_pct, win_rate_divergence_pct,
                    alert_triggered, alert_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date, symbol, timeframe, strategy_name,
                real_metrics.get('trades', 0),
                real_metrics.get('wins', 0),
                real_metrics.get('pnl', 0),
                real_metrics.get('win_rate', 0),
                sim_metrics.get('trades', 0),
                sim_metrics.get('wins', 0),
                sim_metrics.get('pnl', 0),
                sim_metrics.get('win_rate', 0),
                pnl_div,
                wr_div,
                alert_triggered,
                alert_reason
            ))
            conn.commit()
    
    def get_truth_data_alerts(
        self,
        days: int = 7
    ) -> List[Dict]:
        """Get recent divergence alerts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM truth_data
                WHERE alert_triggered = 1
                ORDER BY date DESC
                LIMIT ?
            """, (days * 10,))  # Approximate
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_strategy_comparison(
        self,
        symbol: str,
        timeframe: str,
        days: int = 30
    ) -> List[Dict]:
        """Get real vs simulated comparison for all strategies."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM truth_data
                WHERE symbol = ? AND timeframe = ?
                ORDER BY date DESC, strategy_name
                LIMIT ?
            """, (symbol, timeframe, days * 5))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

