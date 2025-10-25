@echo off
title ONE MARKET - Probar UI Mínima
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Probar UI Mínima                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🔍 Creando UI mínima para probar...
echo.

echo import streamlit as st > ui_test_minimo.py
echo. >> ui_test_minimo.py
echo st.title("🚀 One Market - Test Mínimo") >> ui_test_minimo.py
echo st.write("Si ves esto, Streamlit funciona correctamente") >> ui_test_minimo.py
echo st.write("Fecha actual:", st.write("datetime.now()")) >> ui_test_minimo.py

echo ✅ UI mínima creada

echo.
echo 🌐 Ejecutando UI mínima...
echo ℹ️  Si esto funciona, el problema está en app_complete.py
echo ℹ️  Presiona Ctrl+C si se cuelga
echo.

python -m streamlit run ui_test_minimo.py --server.port 8501 --server.headless false

echo.
echo 🎯 Si llegaste aquí, Streamlit funciona correctamente
echo.
pause



