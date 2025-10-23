#!/usr/bin/env python3
"""Test directo de la API."""

import requests
import json
from datetime import datetime

def test_api_direct():
    """Test the API directly."""
    print("🔍 ONE MARKET - Test API Directo")
    print("=" * 50)
    
    print("🔍 Probando endpoint de salud...")
    try:
        health_response = requests.get('http://localhost:8000/health', timeout=5)
        if health_response.status_code == 200:
            print("✅ API Health: OK")
            print(f"   Respuesta: {health_response.json()}")
        else:
            print(f"❌ API Health: ERROR {health_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando API: {e}")
        return False

    print()
    print("🔍 Probando endpoint de recomendaciones...")
    try:
        rec_response = requests.get('http://localhost:8000/recommendation/daily', 
                                   params={'symbol': 'BTC/USDT', 'date': datetime.now().strftime('%Y-%m-%d')}, 
                                   timeout=10)
        
        if rec_response.status_code == 200:
            data = rec_response.json()
            print("✅ Recomendación obtenida:")
            print(f"   - Dirección: {data.get('direction')}")
            print(f"   - Confianza: {data.get('confidence')}%")
            print(f"   - Precio Entrada: {data.get('entry_price')}")
            print(f"   - Razonamiento: {data.get('rationale')}")
            
            if data.get('direction') != 'HOLD' and data.get('confidence', 0) > 0:
                print("🎉 ¡API devuelve recomendaciones correctas!")
                return True
            else:
                print("❌ API sigue devolviendo HOLD")
                return False
        else:
            print(f"❌ Error en recomendaciones: {rec_response.status_code}")
            print(f"   Respuesta: {rec_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error obteniendo recomendación: {e}")
        return False

if __name__ == "__main__":
    success = test_api_direct()
    print("\n" + "=" * 50)
    print(f"📊 RESULTADO FINAL: {'✅ ÉXITO' if success else '❌ FALLO'}")
    input("\nPresiona Enter para continuar...")

