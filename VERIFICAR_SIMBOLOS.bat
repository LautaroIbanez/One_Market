@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🔍 ONE MARKET - Verificar Símbolos                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

REM Verificar que existe el archivo
if not exist "VERIFICAR_SIMBOLOS.py" (
    echo ❌ Error: No se encuentra VERIFICAR_SIMBOLOS.py
    pause
    exit /b 1
)

echo 🔍 Verificando símbolos disponibles en el exchange...
echo.

python VERIFICAR_SIMBOLOS.py

if errorlevel 1 (
    echo.
    echo ❌ Error en la verificación
    echo.
    echo 🆘 Soluciones:
    echo    1. Ejecuta primero: EJECUTAR_API.bat
    echo    2. Verifica la conexión a internet
    echo    3. Revisa que ccxt esté instalado
    echo.
    pause
) else (
    echo.
    echo ✅ Verificación completada
    echo.
    echo 🎯 PRÓXIMO PASO: Usar los símbolos correctos en SYNC_DATOS_SIMPLE.bat
    echo.
    pause
)
