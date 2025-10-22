#!/usr/bin/env python3
"""
Script para forzar el uso de la fecha actual en lugar de fechas futuras.
"""
import requests
import json
from datetime import datetime, timezone

API_BASE = "http://localhost:8000"

def forzar_fecha_actual():
    """Forzar recomendación con fecha actual real."""
    print("🎯 Forzando recomendación con fecha actual real...")
    
    # Obtener fecha actual real
    fecha_actual = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"📅 Fecha actual real: {fecha_actual}")
    
    try:
        # Llamar al endpoint con fecha actual explícita
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
            
            # Mostrar información de estrategia si está disponible
            if 'strategy_name' in result:
                print(f"🏆 Estrategia: {result.get('strategy_name', 'N/A')}")
                print(f"📊 Score: {result.get('strategy_score', 'N/A')}")
                print(f"📈 Sharpe: {result.get('sharpe_ratio', 'N/A')}")
                print(f"🎯 Win Rate: {result.get('win_rate', 'N/A')}")
            
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

if __name__ == "__main__":
    print("🔧 FORZAR FECHA ACTUAL")
    print("=" * 50)
    
    success = forzar_fecha_actual()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ RECOMENDACIÓN CON FECHA ACTUAL GENERADA")
        print("🎯 Ahora puedes ver la recomendación actualizada en la interfaz web")
        print("📱 Refresca la página web para ver los cambios")
    else:
        print("❌ NO SE PUDO GENERAR LA RECOMENDACIÓN CON FECHA ACTUAL")
        print("🔧 Revisa los errores arriba para más detalles")
