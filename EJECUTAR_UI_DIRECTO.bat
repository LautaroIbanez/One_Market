@echo off
title ONE MARKET - UI Directo
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - UI Directo                        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🔍 Verificando Python y Streamlit...
python --version
python -c "import streamlit; print('Streamlit OK')"

echo.
echo 🌐 Iniciando UI directamente...
echo ℹ️  Si hay errores, los verás aquí
echo ℹ️  La UI se abrirá en: http://localhost:8501
echo.

streamlit run ui/app_simple_test.py --server.port 8501 --server.headless false