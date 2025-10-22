#!/usr/bin/env python3
"""
Script para forzar una recomendación con la fecha actual.
Esto solucionará el problema de la fecha futura 2025-10-22.
"""
import requests
import json
from datetime import datetime, timezone

API_BASE = "http://localhost:8000"

def forzar_recomendacion_hoy():
    """Forzar una recomendación para la fecha actual."""
    print("🎯 Forzando recomendación para la fecha actual...")
    
    # Obtener fecha actual
    fecha_actual = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"📅 Fecha actual: {fecha_actual}")
    
    try:
        # Llamar al endpoint de recomendación con fecha actual
        response = requests.get(
            f"{API_BASE}/recommendation/daily",
            params={
                "symbol": "BTC/USDT",
                "date": fecha_actual,
                "capital": 10000.0,
                "risk_percentage": 2.0
            },
            timeout=30
        )
        
        print(f"📥 Respuesta: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Recomendación generada exitosamente")
            print(f"📊 Símbolo: {result.get('symbol', 'N/A')}")
            print(f"📅 Fecha: {result.get('date', 'N/A')}")
            print(f"🎯 Dirección: {result.get('direction', 'N/A')}")
            print(f"📈 Confianza: {result.get('confidence', 0)}%")
            print(f"⏰ Timeframe: {result.get('timeframe', 'N/A')}")
            print(f"🔑 Hash Dataset: {result.get('dataset_hash', 'N/A')[:8]}...")
            print(f"🔑 Hash Params: {result.get('params_hash', 'N/A')[:8]}...")
            
            # Verificar si es una recomendación válida
            if result.get('direction') != 'HOLD' and result.get('confidence', 0) > 0:
                print("🎉 ¡Recomendación válida generada!")
                return True
            else:
                print("⚠️ Recomendación en HOLD - puede ser normal si no hay señales claras")
                return True
        else:
            print(f"❌ Error HTTP {response.status_code}")
            try:
                error_detail = response.json()
                print(f"📝 Detalle: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"📝 Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verificar_api_salud():
    """Verificar que la API esté funcionando."""
    print("🌐 Verificando salud de la API...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API saludable")
            return True
        else:
            print(f"❌ API error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando a API: {e}")
        return False

def sincronizar_datos():
    """Sincronizar datos antes de generar recomendación."""
    print("📊 Sincronizando datos...")
    
    try:
        response = requests.post(
            f"{API_BASE}/data/sync",
            json={
                "symbol": "BTC/USDT",
                "tf": "1h",
                "force_refresh": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            bars = result.get('stored_count', 0)
            print(f"✅ Datos sincronizados: {bars} barras")
            return True
        else:
            print(f"❌ Error sincronizando: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sincronizando datos: {e}")
        return False

if __name__ == "__main__":
    print("🔧 FORZAR RECOMENDACIÓN PARA HOY")
    print("=" * 50)
    
    # Verificar API
    if not verificar_api_salud():
        print("\n❌ API no disponible")
        exit(1)
    
    # Sincronizar datos
    if not sincronizar_datos():
        print("\n⚠️ Problema sincronizando datos, continuando...")
    
    # Forzar recomendación
    success = forzar_recomendacion_hoy()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ RECOMENDACIÓN GENERADA EXITOSAMENTE")
        print("🎯 Ahora puedes ver la recomendación actualizada en la interfaz web")
        print("📱 Refresca la página web para ver los cambios")
    else:
        print("❌ NO SE PUDO GENERAR LA RECOMENDACIÓN")
        print("🔧 Revisa los errores arriba para más detalles")
