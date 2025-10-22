@echo off
title ONE MARKET - Instalando Dependencias
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         📦 ONE MARKET - Instalando Dependencias          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo ℹ️  Instalando todas las dependencias necesarias...
echo.

REM Verificar Python
echo 🔍 Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado. Instala Python desde https://python.org
    pause
    exit /b 1
)
echo ✅ Python encontrado
echo.

REM Actualizar pip
echo 📦 Actualizando pip...
python -m pip install --upgrade pip
echo.

REM Instalar dependencias básicas
echo 📦 Instalando dependencias básicas...
python -m pip install fastapi uvicorn streamlit plotly pandas requests numpy sqlite3
echo.

REM Instalar dependencias específicas
echo 📦 Instalando dependencias específicas...
python -m pip install vectorbt ta-lib yfinance
echo.

REM Verificar instalaciones
echo 🔍 Verificando instalaciones...
echo.
echo Verificando FastAPI...
python -c "import fastapi; print('✅ FastAPI instalado')" 2>nul || echo "❌ FastAPI no instalado"

echo Verificando Uvicorn...
python -c "import uvicorn; print('✅ Uvicorn instalado')" 2>nul || echo "❌ Uvicorn no instalado"

echo Verificando Streamlit...
python -c "import streamlit; print('✅ Streamlit instalado')" 2>nul || echo "❌ Streamlit no instalado"

echo Verificando Pandas...
python -c "import pandas; print('✅ Pandas instalado')" 2>nul || echo "❌ Pandas no instalado"

echo Verificando Plotly...
python -c "import plotly; print('✅ Plotly instalado')" 2>nul || echo "❌ Plotly no instalado"

echo.
echo ✅ Instalación completada
echo.
pause
