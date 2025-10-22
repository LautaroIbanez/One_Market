@echo off
echo 🚀 ONE MARKET - Ejecutar Sistema Completo
echo ==========================================

REM Instalar dependencias
pip install streamlit plotly pandas requests fastapi uvicorn

echo.
echo 🌐 Iniciando API...
start "API" cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo ⏳ Esperando API...
timeout /t 3 /nobreak >nul

echo 🚀 Iniciando UI...
streamlit run ui/app_complete.py --server.port 8501

echo.
echo ✅ Sistema ejecutado
echo 🌐 API: http://localhost:8000
echo 📊 UI: http://localhost:8501
echo.
pause
