@echo off
title ONE MARKET - Instalar y Ejecutar UI
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Instalar y Ejecutar UI           ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🔧 Instalando Streamlit y dependencias...
echo ℹ️  Esto puede tomar unos minutos...
pip install streamlit plotly pandas requests numpy
echo ✅ Dependencias instaladas

echo.
echo 🔍 Verificando instalación...
python -c "import streamlit; print('✅ Streamlit instalado correctamente')"
if %errorlevel% neq 0 (
    echo ❌ Error instalando Streamlit
    pause
    exit /b 1
)

echo.
echo 🌐 Iniciando UI...
echo ℹ️  La UI se abrirá en: http://localhost:8501
echo ℹ️  Presiona Ctrl+C para detener la UI
echo.

python -m streamlit run ui/app_simple_test.py --server.port 8501 --server.headless false


