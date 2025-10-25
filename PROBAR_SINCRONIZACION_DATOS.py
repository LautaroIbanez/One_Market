#!/usr/bin/env python3
"""
One Market - Probar Sincronización de Datos
Script para probar la sincronización de datos con la API corregida.
"""
import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"

def test_data_sync():
    """Probar sincronización de datos."""
    print("🔧 Probando sincronización de datos...")
    print()
    
    # Símbolos y timeframes a probar
    test_cases = [
        {"symbol": "BTC/USDT", "tf": "1h"},
        {"symbol": "BTC/USDT", "tf": "4h"},
        {"symbol": "BTC/USDT", "tf": "1d"},
        {"symbol": "ETH/USDT", "tf": "1h"},
        {"symbol": "ADA/USDT", "tf": "1h"},
    ]
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"📊 Prueba {i}/5: {case['symbol']} {case['tf']}")
        
        try:
            # Preparar payload
            payload = {
                "symbol": case["symbol"],
                "tf": case["tf"],
                "since": None,
                "until": None,
                "force_refresh": False
            }
            
            # Enviar petición
            response = requests.post(
                f"{API_BASE}/data/sync",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Exitoso: {result.get('stored_count', 0)} barras")
                results.append({
                    "case": case,
                    "success": True,
                    "bars": result.get('stored_count', 0),
                    "message": result.get('message', '')
                })
            else:
                print(f"  ❌ Error HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"  📝 Detalle: {error_detail.get('detail', 'Unknown error')}")
                except:
                    print(f"  📝 Respuesta: {response.text}")
                
                results.append({
                    "case": case,
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "detail": response.text
                })
                
        except requests.exceptions.Timeout:
            print(f"  ⏰ Timeout - {case['symbol']} {case['tf']} tardó demasiado")
            results.append({
                "case": case,
                "success": False,
                "error": "Timeout"
            })
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                "case": case,
                "success": False,
                "error": str(e)
            })
        
        print()
    
    return results

def test_api_health():
    """Probar salud de la API."""
    print("🌐 Probando salud de la API...")
    
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

def test_recommendation():
    """Probar endpoint de recomendaciones."""
    print("\n🧠 Probando recomendaciones...")
    
    try:
        response = requests.get(
            f"{API_BASE}/recommendation/daily?symbol=BTC/USDT&date=2025-10-21",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Recomendaciones funcionando")
            print(f"  📊 Símbolo: {result.get('symbol', 'N/A')}")
            print(f"  📈 Dirección: {result.get('direction', 'N/A')}")
            print(f"  🎯 Confianza: {result.get('confidence', 'N/A')}")
            return True
        else:
            print(f"❌ Recomendaciones error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en recomendaciones: {e}")
        return False

if __name__ == "__main__":
    print("🔧 ONE MARKET - Probar Sincronización de Datos")
    print("=" * 60)
    
    # Probar salud de API
    api_healthy = test_api_health()
    
    if not api_healthy:
        print("\n❌ API no está disponible")
        print("ℹ️  Ejecuta primero: EJECUTAR_API.bat")
        exit(1)
    
    # Probar sincronización
    sync_results = test_data_sync()
    
    # Probar recomendaciones
    rec_success = test_recommendation()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS:")
    
    successful_syncs = sum(1 for r in sync_results if r.get('success', False))
    total_syncs = len(sync_results)
    
    print(f"  🌐 API: {'✅ Saludable' if api_healthy else '❌ Error'}")
    print(f"  📊 Sincronización: {successful_syncs}/{total_syncs} exitosos")
    print(f"  🧠 Recomendaciones: {'✅ Funcionando' if rec_success else '❌ Error'}")
    
    if successful_syncs > 0:
        print(f"\n🎉 ¡Sincronización funcionando!")
        print(f"✅ {successful_syncs} timeframes sincronizados exitosamente")
        print("🎯 PRÓXIMO PASO: La UI debería funcionar correctamente")
    else:
        print(f"\n⚠️  Problemas con sincronización")
        print("ℹ️  Revisa los errores arriba para más detalles")
        
        # Mostrar errores específicos
        for result in sync_results:
            if not result.get('success', False):
                case = result['case']
                error = result.get('error', 'Unknown')
                print(f"  ❌ {case['symbol']} {case['tf']}: {error}")





