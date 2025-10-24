@echo off
title ONE MARKET - Ejecutar Test API
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Ejecutar Test API              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🔬 Ejecutando test de API...
echo.

python test_api_direct.py

echo.
echo 🎯 Test completado
echo.
echo 🛑 Presiona cualquier tecla para continuar...
pause >nul


