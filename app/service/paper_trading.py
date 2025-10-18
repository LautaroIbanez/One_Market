"""Paper trading database and tracking.

This module provides SQLite-based storage for paper trading:
- Decision history
- Trade execution
- Performance tracking
"""
import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import json

from app.data.schema import DecisionRecord, TradeRecord, PerformanceMetrics
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

