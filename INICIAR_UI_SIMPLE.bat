@echo off
title ONE MARKET - UI Simple
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Iniciar UI Simple                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🔍 Verificando archivos de UI...
if exist "ui\app_complete.py" (
    echo ✅ app_complete.py encontrado
) else (
    echo ❌ app_complete.py NO encontrado
    pause
    exit /b 1
)

echo.
echo 🌐 Iniciando UI de Streamlit...
echo ℹ️  La UI se abrirá en: http://localhost:8501
echo ℹ️  Presiona Ctrl+C para detener la UI
echo.

streamlit run ui/app_complete.py --server.port 8501 --server.headless true



