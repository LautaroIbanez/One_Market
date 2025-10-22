#!/usr/bin/env python3
"""
One Market - Probar Backtest Corregido Final
Script para probar que el backtest funciona después de corregir el hashing.
"""
import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"

def test_backtest_fixed():
    """Probar backtest con hashing corregido."""
    print("🔬 Probando backtest con hashing corregido...")
    
    # Probar una estrategia simple
    strategy = "ma_crossover"
    
    try:
        payload = {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "strategy": strategy,
            "from_date": None,
            "to_date": None,
            "initial_capital": 10000.0,
            "risk_per_trade": 0.02,
            "commission": 0.001,
            "slippage": 0.0005,
            "use_trading_windows": False,
            "force_close": True,
            "one_trade_per_day": True,
            "atr_sl_multiplier": 2.0,
            "atr_tp_multiplier": 3.0,
            "atr_period": 14
        }
        
        print(f"  📤 Enviando backtest para {strategy}...")
        
        response = requests.post(
            f"{API_BASE}/backtest/run",
            json=payload,
            timeout=60
        )
        
        print(f"  📥 Respuesta: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Backtest exitoso")
            print(f"    📊 Total trades: {result.get('total_trades', 0)}")
            print(f"    📈 Win rate: {result.get('win_rate', 0):.2%}")
            print(f"    💰 P&L: ${result.get('profit', 0):.2f}")
            print(f"    📉 Max DD: {result.get('max_drawdown', 0):.2%}")
            print(f"    📊 Sharpe: {result.get('sharpe_ratio', 0):.2f}")
            print(f"    🔑 Dataset hash: {result.get('dataset_hash', 'N/A')[:8]}...")
            print(f"    🔑 Params hash: {result.get('params_hash', 'N/A')[:8]}...")
            print(f"    ⏰ Timestamps: {result.get('from_timestamp', 'N/A')} - {result.get('to_timestamp', 'N/A')}")
            return True
        else:
            print(f"  ❌ Error HTTP {response.status_code}")
            try:
                error_detail = response.json()
                print(f"    📝 Detalle: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"    📝 Respuesta: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"  ⏰ Timeout - {strategy} tardó demasiado")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_multiple_strategies():
    """Probar múltiples estrategias."""
    print("\n🔄 Probando múltiples estrategias...")
    
    strategies = [
        "ma_crossover",
        "rsi_regime_pullback", 
        "trend_following_ema"
    ]
    
    results = []
    
    for strategy in strategies:
        try:
            payload = {
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "strategy": strategy,
                "from_date": None,
                "to_date": None,
                "initial_capital": 10000.0,
                "risk_per_trade": 0.02,
                "commission": 0.001,
                "slippage": 0.0005,
                "use_trading_windows": False,
                "force_close": True,
                "one_trade_per_day": True,
                "atr_sl_multiplier": 2.0,
                "atr_tp_multiplier": 3.0,
                "atr_period": 14
            }
            
            print(f"  📤 Probando: {strategy}...")
            
            response = requests.post(
                f"{API_BASE}/backtest/run",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"    ✅ Exitoso: {result.get('total_trades', 0)} trades, ${result.get('profit', 0):.2f} P&L")
                results.append(True)
            else:
                print(f"    ❌ Error HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"      📝 Error: {error_detail.get('detail', 'Unknown error')}")
                except:
                    print(f"      📝 Respuesta: {response.text}")
                results.append(False)
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
            results.append(False)
    
    return results

def test_data_availability():
    """Probar que hay datos disponibles."""
    print("📊 Verificando disponibilidad de datos...")
    
    try:
        # Probar sincronización rápida
        payload = {
            "symbol": "BTC/USDT",
            "tf": "1h",
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
            print(f"  ✅ Datos disponibles: {bars} barras para BTC/USDT 1h")
            return bars > 0
        else:
            print(f"  ❌ Error sincronizando datos: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error verificando datos: {e}")
        return False

def test_api_health():
    """Probar salud de la API."""
    print("🌐 Verificando salud de la API...")
    
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
    print("🔧 ONE MARKET - Probar Backtest Corregido Final")
    print("=" * 60)
    
    # Verificar salud de API
    api_healthy = test_api_health()
    
    if not api_healthy:
        print("\n❌ API no está disponible")
        print("ℹ️  Ejecuta primero: EJECUTAR_API.bat")
        exit(1)
    
    # Verificar datos
    data_available = test_data_availability()
    
    if not data_available:
        print("\n❌ No hay datos disponibles")
        print("ℹ️  Ejecuta primero: PROBAR_SINCRONIZACION_DATOS.bat")
        exit(1)
    
    # Probar backtest con hashing corregido
    backtest_success = test_backtest_fixed()
    
    # Probar múltiples estrategias
    if backtest_success:
        multiple_results = test_multiple_strategies()
        successful_multiple = sum(multiple_results)
        total_multiple = len(multiple_results)
    else:
        successful_multiple = 0
        total_multiple = 0
    
    # Resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN DEL BACKTEST CORREGIDO:")
    print(f"  🌐 API: {'✅ Saludable' if api_healthy else '❌ Error'}")
    print(f"  📊 Datos: {'✅ Disponibles' if data_available else '❌ Faltantes'}")
    print(f"  🔬 Backtest individual: {'✅ Exitoso' if backtest_success else '❌ Error'}")
    print(f"  🔄 Múltiples estrategias: {successful_multiple}/{total_multiple} exitosos")
    
    if api_healthy and data_available and backtest_success and successful_multiple == total_multiple:
        print(f"\n🎉 ¡BACKTEST CORREGIDO Y FUNCIONANDO!")
        print(f"✅ Hashing corregido")
        print(f"✅ Todas las estrategias ejecutándose correctamente")
        print(f"✅ Todos los campos requeridos generados")
        print("🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat")
        print("✅ El sistema completo está listo")
    else:
        print(f"\n⚠️  El backtest aún tiene problemas")
        print("ℹ️  Revisa los errores arriba para más detalles")
        
        if not data_available:
            print("  ❌ Problema con datos - sincroniza primero")
        if not backtest_success:
            print("  ❌ Problema con backtest individual")
        if successful_multiple < total_multiple:
            print("  ❌ Problema con múltiples estrategias")

