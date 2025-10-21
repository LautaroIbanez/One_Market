@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         📊 ONE MARKET - Sincronización Simple              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

REM Verificar que existe el archivo
if not exist "SYNC_DATOS_SIMPLE.py" (
    echo ❌ Error: No se encuentra SYNC_DATOS_SIMPLE.py
    pause
    exit /b 1
)

echo 🔄 Sincronizando datos con formato correcto...
echo.

python SYNC_DATOS_SIMPLE.py

if errorlevel 1 (
    echo.
    echo ❌ Error en la sincronización
    echo.
    echo 🆘 Soluciones:
    echo    1. Ejecuta primero: EJECUTAR_API.bat
    echo    2. Verifica que la API esté respondiendo
    echo    3. Revisa la conexión a internet
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
