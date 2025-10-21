#!/usr/bin/env python3
"""
One Market - Simple Data Sync
Sincronización simple de datos para el sistema One Market.
"""
import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"

def sync_data():
    """Sincronizar datos para múltiples símbolos y timeframes."""
    symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]
    timeframes = ["15m", "1h", "4h", "1d"]
    
    print("🔄 Sincronizando datos...")
    print()
    
    total_synced = 0
    
    for symbol in symbols:
        print(f"📊 Sincronizando {symbol}...")
        
        for tf in timeframes:
            try:
                # Formato correcto para DataSyncRequest
                payload = {
                    "symbol": symbol,
                    "tf": tf,
                    "since": None,
                    "until": None,
                    "force_refresh": False
                }
                
                response = requests.post(
                    f"{API_BASE}/data/sync",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    stored_count = result.get('stored_count', 0)
                    total_synced += stored_count
                    print(f"  ✅ {tf}: {stored_count} barras")
                else:
                    print(f"  ❌ {tf}: HTTP {response.status_code}")
                    if response.text:
                        print(f"     Error: {response.text}")
                        
            except Exception as e:
                print(f"  ❌ {tf}: {e}")
        
        print()
    
    print(f"✅ Sincronización completada: {total_synced} barras totales")
    return total_synced

if __name__ == "__main__":
    try:
        # Verificar que la API esté disponible
        health_response = requests.get(f"{API_BASE}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ API no disponible")
            exit(1)
        
        print("✅ API disponible")
        print()
        
        # Sincronizar datos
        total = sync_data()
        
        if total > 0:
            print()
            print("🎉 ¡Datos sincronizados exitosamente!")
            print(f"📊 Total de barras: {total}")
        else:
            print()
            print("⚠️  No se sincronizaron datos nuevos")
            print("ℹ️  Los datos pueden ya estar actualizados")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API")
        print("ℹ️  Ejecuta EJECUTAR_API.bat primero")
    except Exception as e:
        print(f"❌ Error: {e}")
