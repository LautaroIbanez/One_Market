@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🔍 ONE MARKET - Verificación del Sistema           ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo [1/6] 🐍 Verificando Python...
python --version
if errorlevel 1 (
    echo ❌ Python NO instalado
    pause
    exit /b 1
) else (
    echo ✅ Python instalado
)
echo.

echo [2/6] 📦 Verificando dependencias críticas...
python -c "import fastapi, streamlit, pandas, numpy, ccxt, pydantic; print('  ✅ Todas instaladas')" 2>nul
if errorlevel 1 (
    echo ❌ Faltan dependencias
    echo ℹ️  Instalando ahora...
    pip install -r requirements.txt
) else (
    echo ✅ Dependencias OK
)
echo.

echo [3/6] 🗂️  Verificando archivos...
if exist "main.py" (
    echo ✅ main.py encontrado
) else (
    echo ❌ main.py NO encontrado
)

if exist "ui\app_enhanced.py" (
    echo ✅ ui\app_enhanced.py encontrado
) else (
    echo ❌ ui\app_enhanced.py NO encontrado
)
echo.

echo [4/6] 🔧 Verificando app.data...
python -c "from app.data import DataStore, DataFetcher, Bar; print('  ✅ app.data operativo')" 2>nul
if errorlevel 1 (
    echo ❌ Error en app.data
    python -c "from app.data import DataStore, DataFetcher, Bar"
    pause
    exit /b 1
) else (
    echo ✅ app.data OK
)
echo.

echo [5/6] 📡 Verificando API...
python -c "from main import app; print('  ✅ API importable - ' + str(len(app.routes)) + ' endpoints')" 2>nul
if errorlevel 1 (
    echo ❌ Error al importar API
    echo ℹ️  Mostrando error detallado:
    python -c "from main import app"
    pause
    exit /b 1
) else (
    echo ✅ API OK
)
echo.

echo [6/6] 🌐 Verificando puertos...
echo.

REM Verificar puerto 8000
echo 🔍 Verificando puerto 8000 (API)...
netstat -ano | findstr ":8000" >nul 2>&1
if errorlevel 1 (
    echo ✅ Puerto 8000 disponible (API)
) else (
    echo ⚠️  Puerto 8000 ocupado
    echo ℹ️  Ejecuta DETENER_SERVICIOS.bat primero
)

echo.

REM Verificar puerto 8501  
echo 🔍 Verificando puerto 8501 (UI)...
netstat -ano | findstr ":8501" >nul 2>&1
if errorlevel 1 (
    echo ✅ Puerto 8501 disponible (UI)
) else (
    echo ⚠️  Puerto 8501 ocupado
    echo ℹ️  Ejecuta DETENER_SERVICIOS.bat primero
)
echo.

echo ╔════════════════════════════════════════════════════════════╗
echo ║              ✅ VERIFICACIÓN COMPLETADA                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📋 RESULTADO:
echo.
echo Si todos los checks son ✅, puedes ejecutar:
echo   1. EJECUTAR_API.bat
echo   2. EJECUTAR_UI.bat
echo.
echo Si hay errores ❌, lee el mensaje de error arriba.
echo.
pause

