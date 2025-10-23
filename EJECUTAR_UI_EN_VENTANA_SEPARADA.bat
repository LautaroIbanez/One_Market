@echo off
title ONE MARKET - UI en Ventana Separada
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - UI en Ventana Separada           ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🌐 Iniciando UI en ventana separada...
echo ℹ️  Se abrirá una nueva ventana con la UI
echo ℹ️  Si hay errores, los verás en esa ventana
echo.

start "ONE MARKET UI" cmd /k "cd /d %~dp0 && python -m streamlit run ui/app_simple_test.py --server.port 8501 --server.headless false"

echo.
echo ✅ UI iniciada en ventana separada
echo ℹ️  Revisa la ventana que se abrió para ver si hay errores
echo.
pause

