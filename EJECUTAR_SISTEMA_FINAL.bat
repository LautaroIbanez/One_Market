@echo off
title ONE MARKET - Sistema Completo
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Sistema Completo                  ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo ℹ️  Iniciando sistema completo de One Market
echo.

REM Instalar dependencias básicas
echo 📦 Instalando dependencias...
pip install streamlit plotly pandas requests fastapi uvicorn >nul 2>&1

echo ✅ Dependencias instaladas
echo.

REM Iniciar API
echo 🌐 Iniciando API...
start "ONE MARKET API" cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo ⏳ Esperando que la API se inicie...
timeout /t 3 /nobreak >nul

echo ✅ API iniciada en http://localhost:8000
echo.

REM Iniciar UI
echo 🚀 Iniciando UI de Streamlit...
echo ℹ️  La UI se abrirá en: http://localhost:8501
echo.

streamlit run ui/app_complete.py --server.port 8501 --server.headless false

echo.
echo 🎉 Sistema ejecutado exitosamente
echo.
echo 💡 URLs del sistema:
echo    🌐 API: http://localhost:8000
echo    📊 UI:  http://localhost:8501
echo    📚 Docs: http://localhost:8000/docs
echo.
pause
