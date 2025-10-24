@echo off
title ONE MARKET - Probar UI Simple
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Probar UI Simple                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🔍 Verificando archivos...
if exist "ui\app_simple_test.py" (
    echo ✅ app_simple_test.py encontrado
) else (
    echo ❌ app_simple_test.py NO encontrado
    pause
    exit /b 1
)

echo.
echo 🌐 Iniciando UI de prueba...
echo ℹ️  La UI se abrirá en: http://localhost:8501
echo ℹ️  Presiona Ctrl+C para detener la UI
echo.

streamlit run ui/app_simple_test.py --server.port 8501


