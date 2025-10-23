#!/usr/bin/env python3
"""Script to update database schema."""

import sqlite3
from pathlib import Path
from app.data import DataStore

def update_database_schema():
    """Update database schema to include new columns."""
    
    print("🔧 Actualizando esquema de base de datos...")
    
    try:
        store = DataStore()
        db_path = store.base_path / "recommendations.db"
        
        if db_path.exists():
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Drop old table
                cursor.execute("DROP TABLE IF EXISTS recommendations")
                
                # Create new table with all fields
                cursor.execute("""
                    CREATE TABLE recommendations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        entry_price REAL,
                        entry_band_min REAL,
                        entry_band_max REAL,
                        stop_loss REAL,
                        take_profit REAL,
                        quantity REAL,
                        risk_amount REAL,
                        risk_percentage REAL,
                        rationale TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        strategy_name TEXT,
                        strategy_score REAL,
                        sharpe_ratio REAL,
                        win_rate REAL,
                        max_drawdown REAL,
                        mtf_analysis TEXT,
                        ranking_weights TEXT,
                        dataset_hash TEXT NOT NULL,
                        params_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        UNIQUE(date, symbol, timeframe)
                    )
                """)
                
                conn.commit()
                print("✅ Base de datos actualizada exitosamente")
        else:
            print("ℹ️ No hay base de datos de recomendaciones")
            
    except Exception as e:
        print(f"❌ Error actualizando base de datos: {e}")

if __name__ == "__main__":
    update_database_schema()
