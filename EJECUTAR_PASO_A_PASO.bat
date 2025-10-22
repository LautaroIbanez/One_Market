@echo off
title ONE MARKET - Ejecución Paso a Paso
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Ejecución Paso a Paso            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo ℹ️  Este script ejecutará el sistema paso a paso
echo.

REM Paso 1: Verificar Python
echo 🔍 PASO 1: Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado. Instala Python desde https://python.org
    pause
    exit /b 1
)
echo ✅ Python encontrado
echo.

REM Paso 2: Instalar dependencias
echo 📦 PASO 2: Instalando dependencias...
echo Instalando FastAPI...
python -m pip install fastapi
echo Instalando Uvicorn...
python -m pip install uvicorn
echo Instalando Streamlit...
python -m pip install streamlit
echo Instalando otras dependencias...
python -m pip install plotly pandas requests
echo ✅ Dependencias instaladas
echo.

REM Paso 3: Verificar instalaciones
echo 🔍 PASO 3: Verificando instalaciones...
python -c "import fastapi; print('✅ FastAPI OK')" 2>nul || echo "❌ FastAPI ERROR"
python -c "import uvicorn; print('✅ Uvicorn OK')" 2>nul || echo "❌ Uvicorn ERROR"
python -c "import streamlit; print('✅ Streamlit OK')" 2>nul || echo "❌ Streamlit ERROR"
echo.

REM Paso 4: Iniciar API
echo 🌐 PASO 4: Iniciando API...
echo Presiona ENTER para iniciar la API...
pause >nul
start "ONE MARKET API" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo ⏳ Esperando que la API se inicie...
timeout /t 5 /nobreak >nul
echo ✅ API iniciada
echo.

REM Paso 5: Iniciar UI
echo 🚀 PASO 5: Iniciando UI...
echo Presiona ENTER para iniciar la UI...
pause >nul
python -m streamlit run ui/app_complete.py --server.port 8501 --server.headless false

echo.
echo 🎉 Sistema ejecutado exitosamente
echo.
pause
