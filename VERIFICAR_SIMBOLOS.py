#!/usr/bin/env python3
"""
One Market - Verificar Símbolos Disponibles
Script para verificar qué símbolos están disponibles en el exchange.
"""
import ccxt
import requests

def check_exchange_symbols():
    """Verificar símbolos disponibles en Binance."""
    print("🔍 Verificando símbolos disponibles en Binance...")
    
    try:
        # Crear instancia de Binance
        exchange = ccxt.binance()
        
        # Cargar mercados
        print("📊 Cargando mercados...")
        markets = exchange.load_markets()
        
        # Filtrar símbolos USDT
        usdt_symbols = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')]
        
        print(f"✅ Encontrados {len(usdt_symbols)} símbolos USDT")
        print()
        
        # Mostrar los primeros 20 símbolos
        print("📋 Símbolos USDT disponibles (primeros 20):")
        for i, symbol in enumerate(sorted(usdt_symbols)[:20]):
            print(f"  {i+1:2d}. {symbol}")
        
        if len(usdt_symbols) > 20:
            print(f"  ... y {len(usdt_symbols) - 20} más")
        
        print()
        
        # Verificar símbolos específicos
        test_symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]
        print("🎯 Verificando símbolos específicos:")
        for symbol in test_symbols:
            if symbol in markets:
                print(f"  ✅ {symbol}: Disponible")
            else:
                print(f"  ❌ {symbol}: No disponible")
        
        return usdt_symbols
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def test_api_connection():
    """Probar conexión con la API."""
    print("\n🌐 Probando conexión con API...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API disponible")
            return True
        else:
            print(f"❌ API error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar a la API: {e}")
        return False

if __name__ == "__main__":
    print("🔍 ONE MARKET - Verificación de Símbolos")
    print("=" * 50)
    
    # Verificar API
    if not test_api_connection():
        print("\n⚠️  API no disponible. Ejecuta EJECUTAR_API.bat primero.")
        exit(1)
    
    # Verificar símbolos
    symbols = check_exchange_symbols()
    
    if symbols:
        print(f"\n✅ Verificación completada: {len(symbols)} símbolos disponibles")
        print("\n💡 Recomendación: Usar símbolos con formato '/USDT'")
    else:
        print("\n❌ No se pudieron cargar símbolos del exchange")
