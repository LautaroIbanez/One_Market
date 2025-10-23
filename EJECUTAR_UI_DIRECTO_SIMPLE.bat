@echo off
title ONE MARKET - UI Directo Simple
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - UI Directo Simple                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🌐 Ejecutando UI directamente...
echo ℹ️  Si hay errores, los verás aquí
echo ℹ️  La UI se abrirá en: http://localhost:8501
echo.

python -m streamlit run ui/app_complete.py --server.port 8501 --server.headless false

echo.
echo 🎯 Si llegaste aquí, la UI debería haber funcionado
echo.
echo 🛑 Presiona cualquier tecla para continuar...
pause >nul

