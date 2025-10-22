@echo off
title ONE MARKET - Sistema Completo
echo 🚀 ONE MARKET - Iniciando Sistema...

REM Instalar lo básico
pip install streamlit requests >nul 2>&1

REM Iniciar API
start "API" uvicorn main:app --port 8000 --reload

REM Esperar un poco
timeout /t 2 /nobreak >nul

REM Iniciar UI
streamlit run ui/app_complete.py --server.port 8501

pause
