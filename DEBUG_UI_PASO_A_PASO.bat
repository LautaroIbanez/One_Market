@echo off
title ONE MARKET - Debug UI Paso a Paso
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Debug UI Paso a Paso             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🔍 PASO 1: Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python no funciona
    pause
    exit /b 1
)
echo ✅ Python OK

echo.
echo 🔍 PASO 2: Verificando Streamlit...
python -c "import streamlit; print('Streamlit version:', streamlit.__version__)"
if %errorlevel% neq 0 (
    echo ❌ Streamlit no funciona
    pause
    exit /b 1
)
echo ✅ Streamlit OK

echo.
echo 🔍 PASO 3: Verificando archivo de UI...
if exist "ui\app_simple_test.py" (
    echo ✅ app_simple_test.py existe
) else (
    echo ❌ app_simple_test.py NO existe
    pause
    exit /b 1
)

echo.
echo 🔍 PASO 4: Verificando dependencias del archivo UI...
python -c "import streamlit; import requests; import pandas; import plotly; print('✅ Todas las dependencias OK')"
if %errorlevel% neq 0 (
    echo ❌ Faltan dependencias
    pause
    exit /b 1
)

echo.
echo 🔍 PASO 5: Probando ejecutar Streamlit directamente...
echo ℹ️  Esto debería mostrar errores si los hay
echo ℹ️  Presiona Ctrl+C si se cuelga
echo.

python -m streamlit run ui/app_simple_test.py --server.port 8501 --server.headless false

echo.
echo 🎯 Si llegaste aquí, la UI debería haber funcionado
pause
