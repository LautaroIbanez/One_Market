#!/usr/bin/env python3
"""
One Market - Forzar Descarga de Datos
Script para forzar la descarga de datos históricos.
"""
import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"

def force_download_data():
    """Forzar descarga de datos históricos."""
    # Símbolos principales
    symbols = ["BTC/USDT", "ETH/USDT"]
    timeframes = ["1h", "4h", "1d"]
    
    print("🚀 Forzando descarga de datos históricos...")
    print()
    
    total_synced = 0
    
    for symbol in symbols:
        print(f"📊 Descargando {symbol}...")
        
        for tf in timeframes:
            try:
                # Forzar descarga con fechas específicas
                since_date = datetime.now() - timedelta(days=30)  # Últimos 30 días
                until_date = datetime.now()
                
                payload = {
                    "symbol": symbol,
                    "tf": tf,
                    "since": since_date.isoformat(),
                    "until": until_date.isoformat(),
                    "force_refresh": True  # Forzar descarga
                }
                
                print(f"  🔄 {tf}: Descargando desde {since_date.strftime('%Y-%m-%d')} hasta {until_date.strftime('%Y-%m-%d')}")
                
                response = requests.post(
                    f"{API_BASE}/data/sync",
                    json=payload,
                    timeout=60  # Más tiempo para descarga
                )
                
                if response.status_code == 200:
                    result = response.json()
                    stored_count = result.get('stored_count', 0)
                    total_synced += stored_count
                    print(f"  ✅ {tf}: {stored_count} barras descargadas")
                else:
                    print(f"  ❌ {tf}: HTTP {response.status_code}")
                    if response.text:
                        try:
                            error_detail = response.json()
                            print(f"     Error: {error_detail.get('detail', 'Unknown error')}")
                        except:
                            print(f"     Error: {response.text}")
                        
            except Exception as e:
                print(f"  ❌ {tf}: {e}")
        
        print()
    
    print(f"✅ Descarga completada: {total_synced} barras totales")
    return total_synced

def check_existing_data():
    """Verificar datos existentes."""
    print("🔍 Verificando datos existentes...")
    
    try:
        # Verificar metadatos de datos
        response = requests.get(f"{API_BASE}/data/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Estado de datos: {result}")
        else:
            print(f"❌ Error verificando datos: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")

if __name__ == "__main__":
    try:
        # Verificar que la API esté disponible
        health_response = requests.get(f"{API_BASE}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ API no disponible")
            exit(1)
        
        print("✅ API disponible")
        print()
        
        # Verificar datos existentes
        check_existing_data()
        print()
        
        # Forzar descarga
        total = force_download_data()
        
        if total > 0:
            print()
            print("🎉 ¡Datos descargados exitosamente!")
            print(f"📊 Total de barras: {total}")
            print()
            print("🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat")
        else:
            print()
            print("⚠️  No se descargaron datos")
            print("ℹ️  Posibles causas:")
            print("   - Problema de conectividad con el exchange")
            print("   - Límites de API del exchange")
            print("   - Configuración de fechas incorrecta")
            print()
            print("🎯 PRÓXIMO PASO: Verificar conectividad o usar datos simulados")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API")
        print("ℹ️  Ejecuta EJECUTAR_API.bat primero")
    except Exception as e:
        print(f"❌ Error: {e}")
