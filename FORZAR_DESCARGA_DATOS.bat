@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Forzar Descarga de Datos          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

REM Verificar que existe el archivo
if not exist "FORZAR_DESCARGA_DATOS.py" (
    echo ❌ Error: No se encuentra FORZAR_DESCARGA_DATOS.py
    pause
    exit /b 1
)

echo 🚀 Forzando descarga de datos históricos...
echo ℹ️  Descargando últimos 30 días de datos
echo ℹ️  Símbolos: BTC/USDT, ETH/USDT
echo ℹ️  Timeframes: 1h, 4h, 1d
echo.

python FORZAR_DESCARGA_DATOS.py

if errorlevel 1 (
    echo.
    echo ❌ Error en la descarga
    echo.
    echo 🆘 Soluciones:
    echo    1. Verifica la conexión a internet
    echo    2. Revisa que la API esté respondiendo
    echo    3. Prueba con datos simulados
    echo.
    pause
) else (
    echo.
    echo ✅ Descarga completada
    echo.
    echo 🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat
    echo.
    pause
)
