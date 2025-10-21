@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         📊 ONE MARKET - Sincronización Corregida          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

REM Verificar que existe el archivo
if not exist "SYNC_DATOS_CORREGIDO.py" (
    echo ❌ Error: No se encuentra SYNC_DATOS_CORREGIDO.py
    pause
    exit /b 1
)

echo 🔄 Sincronizando datos con símbolos corregidos...
echo ℹ️  Usando símbolos más comunes: BTC/USDT, ETH/USDT, ADA/USDT
echo ℹ️  Timeframes: 1h, 4h, 1d (más estables)
echo.

python SYNC_DATOS_CORREGIDO.py

if errorlevel 1 (
    echo.
    echo ❌ Error en la sincronización
    echo.
    echo 🆘 Soluciones:
    echo    1. Ejecuta primero: EJECUTAR_API.bat
    echo    2. Verifica que la API esté respondiendo
    echo    3. Revisa la conexión a internet
    echo    4. Prueba VERIFICAR_SIMBOLOS.bat
    echo.
    pause
) else (
    echo.
    echo ✅ Sincronización completada
    echo.
    echo 🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat
    echo.
    pause
)
