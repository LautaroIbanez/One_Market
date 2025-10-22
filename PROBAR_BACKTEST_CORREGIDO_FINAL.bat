@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🔧 ONE MARKET - Probar Backtest Corregido Final ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

echo 🔧 Probando que el backtest funciona después de corregir el hashing...
echo ℹ️  Este script prueba:
echo    ✅ Salud de la API
echo    ✅ Disponibilidad de datos
echo    ✅ Backtest con hashing corregido
echo    ✅ Múltiples estrategias funcionando
echo    ✅ Todos los campos requeridos generados
echo.

REM Verificar que existe el archivo
if not exist "PROBAR_BACKTEST_CORREGIDO_FINAL.py" (
    echo ❌ Error: No se encuentra PROBAR_BACKTEST_CORREGIDO_FINAL.py
    pause
    exit /b 1
)

python PROBAR_BACKTEST_CORREGIDO_FINAL.py

if errorlevel 1 (
    echo.
    echo ❌ Error en la prueba del backtest corregido
    echo.
    echo 🆘 Soluciones:
    echo    1. Verifica que la API esté corriendo
    echo    2. Sincroniza datos primero: PROBAR_SINCRONIZACION_DATOS.bat
    echo    3. Revisa que el hashing esté corregido
    echo    4. Verifica que todos los campos estén generados
    echo.
    pause
) else (
    echo.
    echo ✅ Prueba del backtest corregido completada
    echo.
    echo 🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat
    echo ✅ El backtest está funcionando con hashing corregido
    echo.
    pause
)

