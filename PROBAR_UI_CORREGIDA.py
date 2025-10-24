#!/usr/bin/env python3
"""
One Market - Probar UI Corregida
Script para probar que la UI funciona con los símbolos corregidos.
"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_ui_sync_format():
    """Probar el formato de sincronización que usa la UI."""
    print("🔧 Probando formato de sincronización de la UI...")
    print()
    
    # Símbolos y timeframes como los usa la UI
    test_cases = [
        {"symbol": "BTC/USDT", "tf": "1h"},
        {"symbol": "BTC/USDT", "tf": "4h"},
        {"symbol": "BTC/USDT", "tf": "1d"},
    ]
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"📊 Prueba UI {i}/3: {case['symbol']} {case['tf']}")
        
        try:
            # Payload exacto como lo envía la UI
            payload = {
                "symbol": case["symbol"],
                "tf": case["tf"],
                "force_refresh": False
            }
            
            print(f"  📤 Enviando: {payload}")
            
            # Enviar petición
            response = requests.post(
                f"{API_BASE}/data/sync",
                json=payload,
                timeout=30
            )
            
            print(f"  📥 Respuesta: HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Exitoso: {result.get('stored_count', 0)} barras")
                results.append({
                    "case": case,
                    "success": True,
                    "bars": result.get('stored_count', 0)
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
                    "error": f"HTTP {response.status_code}"
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

def test_recommendation_ui_format():
    """Probar recomendaciones con formato de UI."""
    print("🧠 Probando recomendaciones con formato de UI...")
    
    try:
        # Formato exacto como lo usa la UI
        response = requests.get(
            f"{API_BASE}/recommendation/daily?symbol=BTC/USDT&date=2025-10-21",
            timeout=10
        )
        
        print(f"📥 Respuesta: HTTP {response.status_code}")
        
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
    print("🔧 ONE MARKET - Probar UI Corregida")
    print("=" * 50)
    
    # Probar sincronización con formato de UI
    sync_results = test_ui_sync_format()
    
    # Probar recomendaciones
    rec_success = test_recommendation_ui_format()
    
    # Resumen
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE PRUEBAS UI:")
    
    successful_syncs = sum(1 for r in sync_results if r.get('success', False))
    total_syncs = len(sync_results)
    
    print(f"  📊 Sincronización UI: {successful_syncs}/{total_syncs} exitosos")
    print(f"  🧠 Recomendaciones: {'✅ Funcionando' if rec_success else '❌ Error'}")
    
    if successful_syncs == total_syncs and rec_success:
        print(f"\n🎉 ¡UI CORREGIDA Y FUNCIONANDO!")
        print(f"✅ Todos los formatos de UI funcionan correctamente")
        print("🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat")
        print("✅ La UI debería sincronizar datos sin errores")
    else:
        print(f"\n⚠️  Problemas con formato de UI")
        print("ℹ️  Revisa los errores arriba para más detalles")
        
        # Mostrar errores específicos
        for result in sync_results:
            if not result.get('success', False):
                case = result['case']
                error = result.get('error', 'Unknown')
                print(f"  ❌ {case['symbol']} {case['tf']}: {error}")




