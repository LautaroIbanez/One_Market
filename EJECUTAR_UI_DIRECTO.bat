@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         📊 ONE MARKET - UI Directo                        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

REM Verificar que existe el archivo
if not exist "ui\app_enhanced.py" (
    echo ❌ Error: No se encuentra ui\app_enhanced.py
    pause
    exit /b 1
)

echo ⏳ Iniciando UI con Python directo...
echo ℹ️  Presiona Ctrl+C para detener
echo.

set PYTHONPATH=%CD%

echo 🔧 Ejecutando: python -m streamlit run ui/app_enhanced.py
echo.

python -m streamlit run ui/app_enhanced.py

if errorlevel 1 (
    echo.
    echo ❌ Error al iniciar la UI
    echo.
    echo 🆘 Soluciones:
    echo    1. Ejecuta primero: EJECUTAR_API.bat
    echo    2. Verifica que Python esté instalado
    echo    3. Ejecuta: pip install streamlit
    echo.
    pause
) else (
    echo.
    echo ℹ️  La UI se cerró normalmente
    pause
)
