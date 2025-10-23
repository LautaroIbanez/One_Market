@echo off
title ONE MARKET - Ejecutar Test Recomendaciones
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Ejecutar Test Recomendaciones   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🔬 Ejecutando test de recomendaciones...
echo.

python test_recommendations_final.py

echo.
echo 🎯 Test completado
echo.
echo 🛑 Presiona cualquier tecla para continuar...
pause >nul

