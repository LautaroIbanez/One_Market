#!/usr/bin/env python3
"""
Script para probar el sistema de ranking simple.
"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_ranking_simple():
    """Probar el sistema de ranking simple."""
    print("🔧 Probando sistema de ranking simple...")
    
    try:
        # Probar endpoint de salud
        print("🌐 Verificando salud del servicio...")
        response = requests.get(f"{API_BASE}/ranking/health", timeout=10)
        
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Servicio saludable: {health.get('status')}")
            print(f"📊 Mensaje: {health.get('message')}")
        else:
            print(f"❌ Error de salud: HTTP {response.status_code}")
            return False
        
        # Probar ranking para BTC/USDT
        print("\n🎯 Ejecutando ranking para BTC/USDT...")
        payload = {
            "symbol": "BTC/USDT",
            "date": None  # Usar fecha actual
        }
        
        response = requests.post(
            f"{API_BASE}/ranking/run",
            json=payload,
            timeout=30
        )
        
        print(f"📥 Respuesta: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Ranking ejecutado exitosamente")
            print(f"📊 Símbolo: {result.get('symbol')}")
            print(f"📅 Fecha: {result.get('date')}")
            print(f"✅ Éxito: {result.get('success')}")
            print(f"📝 Mensaje: {result.get('message')}")
            
            return True
        else:
            print(f"❌ Error ejecutando ranking: HTTP {response.status_code}")
            try:
                error_detail = response.json()
                print(f"📝 Detalle: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"📝 Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 PROBAR RANKING SIMPLE")
    print("=" * 50)
    
    # Probar ranking simple
    ranking_success = test_ranking_simple()
    
    print("\n" + "=" * 50)
    if ranking_success:
        print("✅ RANKING SIMPLE FUNCIONANDO")
        print("🎯 Endpoint básico implementado")
        print("📊 API endpoints funcionando")
        print("🔧 Base para implementación completa")
    else:
        print("❌ RANKING SIMPLE NO FUNCIONA")
        print("🔧 Revisa los errores arriba para más detalles")
