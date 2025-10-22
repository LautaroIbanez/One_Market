#!/usr/bin/env python3
"""
One Market - Probar Sistema Completo
Script para probar que el sistema completo funciona sin errores.
"""
import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"

def test_data_sync():
    """Probar sincronización de datos."""
    print("📊 Probando sincronización de datos...")
    
    test_cases = [
        {"symbol": "BTC/USDT", "tf": "1h"},
        {"symbol": "BTC/USDT", "tf": "4h"},
        {"symbol": "BTC/USDT", "tf": "1d"},
    ]
    
    results = []
    
    for case in test_cases:
        print(f"  🔄 {case['symbol']} {case['tf']}...")
        
        try:
            payload = {
                "symbol": case["symbol"],
                "tf": case["tf"],
                "force_refresh": False
            }
            
            response = requests.post(
                f"{API_BASE}/data/sync",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                bars = result.get('stored_count', 0)
                print(f"    ✅ {bars} barras sincronizadas")
                results.append(True)
            else:
                print(f"    ❌ Error HTTP {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
            results.append(False)
    
    return all(results)

def test_recommendations():
    """Probar recomendaciones."""
    print("\n🧠 Probando recomendaciones...")
    
    try:
        response = requests.get(
            f"{API_BASE}/recommendation/daily?symbol=BTC/USDT&date=2025-10-21",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Recomendación generada")
            print(f"    📊 Símbolo: {result.get('symbol', 'N/A')}")
            print(f"    📈 Dirección: {result.get('direction', 'N/A')}")
            print(f"    🎯 Confianza: {result.get('confidence', 'N/A')}")
            return True
        else:
            print(f"  ❌ Error HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_backtest():
    """Probar backtest."""
    print("\n🔬 Probando backtest...")
    
    try:
        payload = {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "strategy": "MA Crossover",
            "from_date": None,
            "to_date": None,
            "initial_capital": 10000.0,
            "risk_per_trade": 0.02,
            "commission": 0.001,
            "slippage": 0.0005,
            "use_trading_windows": True,
            "force_close": True,
            "one_trade_per_day": True,
            "atr_sl_multiplier": 2.0,
            "atr_tp_multiplier": 3.0,
            "atr_period": 14
        }
        
        response = requests.post(
            f"{API_BASE}/backtest/run",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Backtest ejecutado exitosamente")
            print(f"    📊 Total trades: {result.get('total_trades', 0)}")
            print(f"    📈 Win rate: {result.get('win_rate', 0):.2%}")
            print(f"    💰 P&L: ${result.get('total_pnl', 0):.2f}")
            return True
        else:
            print(f"  ❌ Error HTTP {response.status_code}")
            try:
                error_detail = response.json()
                print(f"    📝 Detalle: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"    📝 Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_api_health():
    """Probar salud de la API."""
    print("🌐 Probando salud de la API...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ API saludable")
            return True
        else:
            print(f"  ❌ API error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Error conectando a API: {e}")
        return False

if __name__ == "__main__":
    print("🔧 ONE MARKET - Probar Sistema Completo")
    print("=" * 60)
    
    # Probar salud de API
    api_healthy = test_api_health()
    
    if not api_healthy:
        print("\n❌ API no está disponible")
        print("ℹ️  Ejecuta primero: EJECUTAR_API.bat")
        exit(1)
    
    # Probar sincronización
    sync_success = test_data_sync()
    
    # Probar recomendaciones
    rec_success = test_recommendations()
    
    # Probar backtest
    backtest_success = test_backtest()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN DEL SISTEMA COMPLETO:")
    print(f"  🌐 API: {'✅ Saludable' if api_healthy else '❌ Error'}")
    print(f"  📊 Sincronización: {'✅ Funcionando' if sync_success else '❌ Error'}")
    print(f"  🧠 Recomendaciones: {'✅ Funcionando' if rec_success else '❌ Error'}")
    print(f"  🔬 Backtest: {'✅ Funcionando' if backtest_success else '❌ Error'}")
    
    if api_healthy and sync_success and rec_success and backtest_success:
        print(f"\n🎉 ¡SISTEMA COMPLETO FUNCIONANDO!")
        print(f"✅ Todos los componentes operativos")
        print("🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat")
        print("✅ El sistema está listo para operar")
    else:
        print(f"\n⚠️  Algunos componentes tienen problemas")
        print("ℹ️  Revisa los errores arriba para más detalles")
        
        if not sync_success:
            print("  ❌ Problema con sincronización de datos")
        if not rec_success:
            print("  ❌ Problema con recomendaciones")
        if not backtest_success:
            print("  ❌ Problema con backtest")

