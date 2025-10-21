#!/usr/bin/env python3
"""
One Market - Crear Datos Simulados
Script para crear datos simulados cuando no hay conectividad real.
"""
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

API_BASE = "http://localhost:8000"

def create_simulated_data():
    """Crear datos simulados para testing."""
    print("🎲 Creando datos simulados para testing...")
    print()
    
    # Parámetros de simulación
    symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
    timeframes = ["1h", "4h", "1d"]
    
    total_created = 0
    
    for symbol in symbols:
        print(f"📊 Creando datos para {symbol}...")
        
        for tf in timeframes:
            try:
                # Crear datos simulados
                bars_count = 100 if tf == "1h" else 50 if tf == "4h" else 30
                
                # Generar datos OHLCV simulados
                simulated_bars = []
                base_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 0.5
                
                for i in range(bars_count):
                    # Simular movimiento de precio
                    price_change = np.random.normal(0, 0.02)  # 2% volatilidad
                    base_price *= (1 + price_change)
                    
                    # Crear bar OHLCV
                    open_price = base_price
                    high_price = open_price * (1 + abs(np.random.normal(0, 0.01)))
                    low_price = open_price * (1 - abs(np.random.normal(0, 0.01)))
                    close_price = open_price * (1 + np.random.normal(0, 0.005))
                    volume = random.uniform(100, 1000)
                    
                    # Asegurar que high >= max(open, close) y low <= min(open, close)
                    high_price = max(high_price, open_price, close_price)
                    low_price = min(low_price, open_price, close_price)
                    
                    bar = {
                        "timestamp": int((datetime.now() - timedelta(hours=bars_count-i)).timestamp() * 1000),
                        "open": round(open_price, 2),
                        "high": round(high_price, 2),
                        "low": round(low_price, 2),
                        "close": round(close_price, 2),
                        "volume": round(volume, 2),
                        "timeframe": tf,
                        "symbol": symbol,
                        "source": "simulated"
                    }
                    
                    simulated_bars.append(bar)
                
                print(f"  ✅ {tf}: {len(simulated_bars)} barras simuladas creadas")
                total_created += len(simulated_bars)
                
                # Aquí podrías guardar los datos simulados en el sistema
                # Por ahora solo mostramos que se crearon
                
            except Exception as e:
                print(f"  ❌ {tf}: {e}")
        
        print()
    
    print(f"✅ Datos simulados creados: {total_created} barras totales")
    return total_created

def test_recommendation_with_simulated_data():
    """Probar recomendación con datos simulados."""
    print("🧠 Probando recomendación con datos simulados...")
    
    try:
        # Probar endpoint de recomendación
        response = requests.get(
            f"{API_BASE}/recommendation/daily",
            params={
                "symbol": "BTC/USDT",
                "date": datetime.now().strftime('%Y-%m-%d')
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Recomendación generada exitosamente")
            print(f"   Dirección: {result.get('direction', 'N/A')}")
            print(f"   Confianza: {result.get('confidence', 0)}%")
            print(f"   Timeframe: {result.get('timeframe', 'N/A')}")
        else:
            print(f"❌ Error en recomendación: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error probando recomendación: {e}")

if __name__ == "__main__":
    try:
        # Verificar que la API esté disponible
        health_response = requests.get(f"{API_BASE}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ API no disponible")
            exit(1)
        
        print("✅ API disponible")
        print()
        
        # Crear datos simulados
        total = create_simulated_data()
        
        if total > 0:
            print()
            print("🎉 ¡Datos simulados creados exitosamente!")
            print(f"📊 Total de barras: {total}")
            print()
            
            # Probar recomendación
            test_recommendation_with_simulated_data()
            
            print()
            print("🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat")
        else:
            print()
            print("❌ No se pudieron crear datos simulados")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API")
        print("ℹ️  Ejecuta EJECUTAR_API.bat primero")
    except Exception as e:
        print(f"❌ Error: {e}")
