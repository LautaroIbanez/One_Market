@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🔍 ONE MARKET - Verificacion Simple                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo [1/6] Python...
python --version
if errorlevel 1 (
    echo ❌ Python NO instalado
    pause
    exit /b 1
) else (
    echo ✅ Python OK
)
echo.

echo [2/6] Dependencias...
python -c "import fastapi, streamlit, pandas, numpy, ccxt, pydantic; print('✅ Dependencias OK')" 2>nul
if errorlevel 1 (
    echo ❌ Faltan dependencias
    pause
    exit /b 1
) else (
    echo ✅ Dependencias OK
)
echo.

echo [3/6] Archivos...
if exist "main.py" (
    echo ✅ main.py OK
) else (
    echo ❌ main.py NO encontrado
    pause
    exit /b 1
)

if exist "ui\app_enhanced.py" (
    echo ✅ ui\app_enhanced.py OK
) else (
    echo ❌ ui\app_enhanced.py NO encontrado
    pause
    exit /b 1
)
echo.

echo [4/6] app.data...
python -c "from app.data import DataStore, DataFetcher, Bar; print('✅ app.data OK')" 2>nul
if errorlevel 1 (
    echo ❌ Error en app.data
    python -c "from app.data import DataStore, DataFetcher, Bar"
    pause
    exit /b 1
) else (
    echo ✅ app.data OK
)
echo.

echo [5/6] API...
python -c "from main import app; print('✅ API OK - ' + str(len(app.routes)) + ' endpoints')" 2>nul
if errorlevel 1 (
    echo ❌ Error al importar API
    python -c "from main import app"
    pause
    exit /b 1
) else (
    echo ✅ API OK
)
echo.

echo [6/6] Puertos...
echo.

REM Puerto 8000
netstat -ano | findstr ":8000" >nul
if errorlevel 1 (
    echo ✅ Puerto 8000: LIBRE
) else (
    echo ❌ Puerto 8000: OCUPADO
)

REM Puerto 8501
netstat -ano | findstr ":8501" >nul
if errorlevel 1 (
    echo ✅ Puerto 8501: LIBRE
) else (
    echo ❌ Puerto 8501: OCUPADO
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              ✅ VERIFICACION COMPLETADA                     ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo Si todos son ✅, ejecuta:
echo   1. EJECUTAR_API.bat
echo   2. EJECUTAR_UI.bat
echo.
pause
