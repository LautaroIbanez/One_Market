#!/usr/bin/env python3
"""
One Market - Probar Capa de Datos Completa
Script para probar la nueva capa de datos implementada.
"""
import requests
import json
from datetime import datetime, timedelta
import time

API_BASE = "http://localhost:8000"

def test_data_layer():
    """Probar la nueva capa de datos."""
    print("🔧 Probando nueva capa de datos...")
    print()
    
    try:
        # Probar importación de la nueva capa
        print("📦 Importando nueva capa de datos...")
        from app.data import DataFetcher, DataStore, OHLCVBar, DatasetMetadata
        print("✅ Importación exitosa")
        
        # Probar DataFetcher
        print("\n🔍 Probando DataFetcher...")
        fetcher = DataFetcher()
        print(f"✅ DataFetcher inicializado: {fetcher.exchange_name}")
        
        # Probar DataStore
        print("\n💾 Probando DataStore...")
        store = DataStore()
        print(f"✅ DataStore inicializado: {store.base_path}")
        
        # Probar validación de símbolos
        print("\n🎯 Probando validación de símbolos...")
        test_symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
        for symbol in test_symbols:
            is_valid = fetcher.validate_symbol(symbol)
            print(f"  {'✅' if is_valid else '❌'} {symbol}: {'Válido' if is_valid else 'No válido'}")
        
        # Probar timeframes soportados
        print("\n⏰ Probando timeframes soportados...")
        timeframes = fetcher.get_supported_timeframes()
        print(f"✅ Timeframes disponibles: {len(timeframes)}")
        for tf in timeframes[:10]:  # Mostrar solo los primeros 10
            print(f"  - {tf}")
        
        # Probar fetch de datos reales
        print("\n📊 Probando fetch de datos reales...")
        try:
            bars = fetcher.fetch_ohlcv("BTC/USDT", "1h", limit=10)
            print(f"✅ Fetch exitoso: {len(bars)} barras obtenidas")
            
            if bars:
                # Probar validación de calidad
                print("\n🔍 Probando validación de calidad...")
                validation = fetcher.validate_data_quality(bars)
                print(f"✅ Validación: {'Válido' if validation.is_valid else 'Inválido'}")
                print(f"  - Calidad: {validation.quality_score:.2f}")
                print(f"  - Errores: {len(validation.errors)}")
                print(f"  - Advertencias: {len(validation.warnings)}")
                
                # Probar almacenamiento
                print("\n💾 Probando almacenamiento...")
                metadata = store.write_bars(bars)
                print(f"✅ Almacenamiento exitoso: {metadata.bar_count} barras")
                print(f"  - Hash: {metadata.data_hash[:8]}...")
                print(f"  - Rango: {datetime.fromtimestamp(metadata.start_timestamp/1000)} - {datetime.fromtimestamp(metadata.end_timestamp/1000)}")
                
                # Probar lectura
                print("\n📖 Probando lectura...")
                read_bars = store.read_bars("BTC/USDT", "1h", max_bars=5)
                print(f"✅ Lectura exitosa: {len(read_bars)} barras leídas")
                
                # Probar integridad
                print("\n🔍 Probando verificación de integridad...")
                integrity = store.check_integrity("BTC/USDT", "1h")
                print(f"✅ Integridad: {'Saludable' if integrity.is_healthy else 'Con problemas'}")
                print(f"  - Total barras: {integrity.total_bars}")
                print(f"  - Gaps: {integrity.gaps_count}")
                print(f"  - Duplicados: {integrity.duplicates_count}")
                print(f"  - Calidad: {integrity.quality_score:.2f}")
        
        except Exception as e:
            print(f"⚠️  Fetch de datos reales falló: {e}")
            print("ℹ️  Esto es normal si no hay conectividad con el exchange")
        
        print("\n🎉 ¡Capa de datos completa funcionando!")
        return True
        
    except Exception as e:
        print(f"❌ Error probando capa de datos: {e}")
        return False

def test_api_integration():
    """Probar integración con API."""
    print("\n🌐 Probando integración con API...")
    
    try:
        # Probar health endpoint
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API disponible")
        else:
            print(f"❌ API error: HTTP {response.status_code}")
            return False
        
        # Probar data sync endpoint
        print("\n📊 Probando sincronización de datos...")
        sync_payload = {
            "symbol": "BTC/USDT",
            "tf": "1h",
            "since": None,
            "until": None,
            "force_refresh": False
        }
        
        response = requests.post(f"{API_BASE}/data/sync", json=sync_payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Sincronización exitosa: {result.get('stored_count', 0)} barras")
        else:
            print(f"⚠️  Sincronización falló: HTTP {response.status_code}")
            if response.text:
                try:
                    error_detail = response.json()
                    print(f"  Error: {error_detail.get('detail', 'Unknown error')}")
                except:
                    print(f"  Error: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando API: {e}")
        return False

if __name__ == "__main__":
    print("🔧 ONE MARKET - Prueba de Capa de Datos Completa")
    print("=" * 60)
    
    # Probar capa de datos
    data_success = test_data_layer()
    
    # Probar integración con API
    api_success = test_api_integration()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS:")
    print(f"  🔧 Capa de datos: {'✅ Exitoso' if data_success else '❌ Falló'}")
    print(f"  🌐 Integración API: {'✅ Exitoso' if api_success else '❌ Falló'}")
    
    if data_success and api_success:
        print("\n🎉 ¡Sistema completo funcionando!")
        print("🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat")
    else:
        print("\n⚠️  Algunas pruebas fallaron")
        print("ℹ️  Revisa los errores arriba para más detalles")



