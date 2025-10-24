@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🔧 ONE MARKET - Probar Backtest Corregido       ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

echo 🔧 Probando que el backtest funciona después de las correcciones...
echo ℹ️  Este script prueba:
echo    ✅ Salud de la API
echo    ✅ Disponibilidad de datos
echo    ✅ Backtest con parámetros corregidos
echo    ✅ Múltiples estrategias (MA Crossover, RSI, EMA)
echo    ✅ Diagnóstico específico del backtest
echo.

REM Verificar que existe el archivo
if not exist "PROBAR_BACKTEST_CORREGIDO.py" (
    echo ❌ Error: No se encuentra PROBAR_BACKTEST_CORREGIDO.py
    pause
    exit /b 1
)

python PROBAR_BACKTEST_CORREGIDO.py

if errorlevel 1 (
    echo.
    echo ❌ Error en la prueba del backtest
    echo.
    echo 🆘 Soluciones:
    echo    1. Verifica que la API esté corriendo
    echo    2. Sincroniza datos primero: PROBAR_SINCRONIZACION_DATOS.bat
    echo    3. Revisa que los datos estén disponibles
    echo    4. Verifica la conectividad a internet
    echo.
    pause
) else (
    echo.
    echo ✅ Prueba del backtest completada
    echo.
    echo 🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat
    echo ✅ El backtest está funcionando correctamente
    echo.
    pause
)




