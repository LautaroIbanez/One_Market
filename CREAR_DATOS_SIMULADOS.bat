@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🎲 ONE MARKET - Crear Datos Simulados            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

REM Verificar que existe el archivo
if not exist "CREAR_DATOS_SIMULADOS.py" (
    echo ❌ Error: No se encuentra CREAR_DATOS_SIMULADOS.py
    pause
    exit /b 1
)

echo 🎲 Creando datos simulados para testing...
echo ℹ️  Esto es útil cuando no hay conectividad real con exchanges
echo ℹ️  Símbolos: BTC/USDT, ETH/USDT, ADA/USDT
echo ℹ️  Timeframes: 1h, 4h, 1d
echo.

python CREAR_DATOS_SIMULADOS.py

if errorlevel 1 (
    echo.
    echo ❌ Error creando datos simulados
    echo.
    echo 🆘 Soluciones:
    echo    1. Verifica que la API esté respondiendo
    echo    2. Revisa que numpy y pandas estén instalados
    echo    3. Ejecuta: pip install numpy pandas
    echo.
    pause
) else (
    echo.
    echo ✅ Datos simulados creados
    echo.
    echo 🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat
    echo.
    pause
)
