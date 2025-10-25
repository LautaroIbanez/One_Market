@echo off
title ONE MARKET - UI con Python
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - UI con Python                     ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🔍 Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado
    pause
    exit /b 1
)

echo.
echo 🔍 Verificando Streamlit...
python -c "import streamlit; print('✅ Streamlit disponible')"
if %errorlevel% neq 0 (
    echo ❌ Streamlit no disponible, instalando...
    pip install streamlit plotly pandas requests numpy
)

echo.
echo 🌐 Iniciando UI con Python...
echo ℹ️  La UI se abrirá en: http://localhost:8501
echo ℹ️  Presiona Ctrl+C para detener la UI
echo.

python -m streamlit run ui/app_simple_test.py --server.port 8501 --server.headless false



