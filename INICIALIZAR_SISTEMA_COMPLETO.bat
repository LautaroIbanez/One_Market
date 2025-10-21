@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Inicialización Sistema Completo    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 🔧 Inicializando sistema completo...
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado
    pause
    exit /b 1
) else (
    echo ✅ Python disponible
)

REM Verificar dependencias
echo 📦 Verificando dependencias...
python -c "import fastapi, streamlit, pandas, numpy, ccxt, pydantic, plotly, requests; print('✅ Todas las dependencias disponibles')" 2>nul
if errorlevel 1 (
    echo ❌ Faltan dependencias
    echo ℹ️  Instalando dependencias...
    pip install -r requirements.txt
) else (
    echo ✅ Dependencias OK
)

REM Verificar app.data
echo 🔧 Verificando sistema de datos...
python -c "from app.data import DataStore, DataFetcher, Bar; print('✅ Sistema de datos operativo')" 2>nul
if errorlevel 1 (
    echo ❌ Error en sistema de datos
    python -c "from app.data import DataStore, DataFetcher, Bar"
    pause
    exit /b 1
) else (
    echo ✅ Sistema de datos OK
)

REM Verificar API
echo 📡 Verificando API...
python -c "from main import app; print('✅ API importable - ' + str(len(app.routes)) + ' endpoints')" 2>nul
if errorlevel 1 (
    echo ❌ Error al importar API
    python -c "from main import app"
    pause
    exit /b 1
) else (
    echo ✅ API OK
)

REM Verificar puertos
echo 🌐 Verificando puertos...
netstat -ano | findstr ":8000" >nul 2>&1
if errorlevel 1 (
    echo ✅ Puerto 8000 disponible
) else (
    echo ⚠️  Puerto 8000 ocupado
    echo ℹ️  Ejecuta DETENER_SERVICIOS.bat primero
)

netstat -ano | findstr ":8501" >nul 2>&1
if errorlevel 1 (
    echo ✅ Puerto 8501 disponible
) else (
    echo ⚠️  Puerto 8501 ocupado
    echo ℹ️  Ejecuta DETENER_SERVICIOS.bat primero
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              ✅ SISTEMA COMPLETO LISTO                     ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📋 PRÓXIMOS PASOS:
echo.
echo 1. 🌐 Ejecutar API: EJECUTAR_API.bat
echo 2. 📊 Ejecutar UI Completa: EJECUTAR_UI_COMPLETA.bat
echo.
echo 🎯 FUNCIONALIDADES DISPONIBLES:
echo    ✅ Sistema de datos completo (app.data)
echo    ✅ API FastAPI con 38 endpoints
echo    ✅ UI Streamlit completa
echo    ✅ Análisis multi-timeframe
echo    ✅ Backtesting avanzado
echo    ✅ Recomendaciones inteligentes
echo    ✅ Sistema de métricas
echo.
pause
