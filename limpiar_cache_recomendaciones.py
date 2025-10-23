#!/usr/bin/env python3
"""Script to clear recommendation cache."""

import sqlite3
from pathlib import Path
from app.data import DataStore

def clear_recommendation_cache():
    """Clear all cached recommendations."""
    
    print("🧹 Limpiando caché de recomendaciones...")
    
    try:
        store = DataStore()
        db_path = store.base_path / "recommendations.db"
        
        if db_path.exists():
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Count existing recommendations
                cursor.execute("SELECT COUNT(*) FROM recommendations")
                count = cursor.fetchone()[0]
                print(f"📊 Recomendaciones encontradas: {count}")
                
                # Clear all recommendations
                cursor.execute("DELETE FROM recommendations")
                conn.commit()
                
                print(f"✅ Caché limpiado exitosamente")
        else:
            print("ℹ️ No hay base de datos de recomendaciones")
            
    except Exception as e:
        print(f"❌ Error limpiando caché: {e}")

if __name__ == "__main__":
    clear_recommendation_cache()
