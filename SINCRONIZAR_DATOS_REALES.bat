@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         📊 ONE MARKET - Sincronización de Datos Reales    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

echo 🔄 Sincronizando datos reales de exchanges...
echo.

REM Símbolos a sincronizar
set SYMBOLS=BTCUSDT ETHUSDT ADAUSDT SOLUSDT BNBUSDT XRPUSDT
set TIMEFRAMES=15m 1h 4h 1d

echo 📊 Símbolos: %SYMBOLS%
echo ⏰ Timeframes: %TIMEFRAMES%
echo.

echo 🚀 Iniciando sincronización...
echo.

REM Crear script Python para sincronización
echo import requests > sync_data.py
echo import json >> sync_data.py
echo from datetime import datetime >> sync_data.py
echo. >> sync_data.py
echo API_BASE = "http://localhost:8000" >> sync_data.py
echo. >> sync_data.py
echo symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"] >> sync_data.py
echo timeframes = ["15m", "1h", "4h", "1d"] >> sync_data.py
echo. >> sync_data.py
echo print("🔄 Sincronizando datos...") >> sync_data.py
echo. >> sync_data.py
echo for symbol in symbols: >> sync_data.py
echo     print(f"📊 Sincronizando {symbol}...") >> sync_data.py
echo     for tf in timeframes: >> sync_data.py
echo         try: >> sync_data.py
echo             response = requests.post(f"{API_BASE}/data/sync", json={"symbol": symbol, "tf": tf, "since": None, "until": None, "force_refresh": False}, timeout=30) >> sync_data.py
echo             if response.status_code == 200: >> sync_data.py
echo                 result = response.json() >> sync_data.py
echo                 print(f"  ✅ {tf}: {result.get('stored_count', 0)} barras") >> sync_data.py
echo             else: >> sync_data.py
echo                 print(f"  ❌ {tf}: HTTP {response.status_code}") >> sync_data.py
echo         except Exception as e: >> sync_data.py
echo             print(f"  ❌ {tf}: {e}") >> sync_data.py
echo. >> sync_data.py
echo print("✅ Sincronización completada") >> sync_data.py

REM Ejecutar sincronización
python sync_data.py

REM Limpiar archivo temporal
del sync_data.py

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              ✅ SINCRONIZACIÓN COMPLETADA                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📋 DATOS DISPONIBLES:
echo    ✅ Datos históricos
echo    ✅ Múltiples timeframes
echo    ✅ Múltiples símbolos
echo    ✅ Datos actualizados
echo.
echo 🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat
echo.
pause
