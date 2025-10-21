@echo off
chcp 65001 >nul
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Inicio del Proyecto 🚀             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Verificar Python
echo [1/5] 🔍 Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Por favor instala Python 3.11+
    pause
    exit /b 1
)
python --version
echo ✅ Python OK
echo.

REM Verificar dependencias críticas
echo [2/5] 📦 Verificando dependencias...
python -c "import fastapi, streamlit, pandas, numpy, ccxt, pydantic" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Faltan dependencias. Instalando...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Error instalando dependencias
        pause
        exit /b 1
    )
) else (
    echo ✅ Dependencias OK
)
echo.

REM Verificar imports de la aplicación
echo [3/5] 🔧 Verificando integridad del sistema...
python -c "from app.data import DataStore, DataFetcher; from main import app; print('✅ Sistema OK')" 2>&1
if errorlevel 1 (
    echo ❌ Error en la aplicación. Revisa los logs arriba.
    pause
    exit /b 1
)
echo.

REM Crear directorios necesarios
echo [4/5] 📁 Creando directorios...
if not exist "storage" mkdir storage
if not exist "logs" mkdir logs
if not exist "artifacts" mkdir artifacts
echo ✅ Directorios creados
echo.

REM Mostrar opciones
echo [5/5] 🎯 Selecciona qué iniciar:
echo.
echo   1. 🌐 API FastAPI (puerto 8000)
echo   2. 📊 UI Streamlit (puerto 8501)
echo   3. 🔄 Ambos (API + UI en ventanas separadas)
echo   4. 🧪 Ejecutar tests
echo   5. ❌ Salir
echo.
set /p opcion="Opción (1-5): "

if "%opcion%"=="1" goto api
if "%opcion%"=="2" goto ui
if "%opcion%"=="3" goto ambos
if "%opcion%"=="4" goto tests
if "%opcion%"=="5" goto salir

:api
echo.
echo 🌐 Iniciando API FastAPI...
echo.
echo ℹ️  La API estará disponible en: http://localhost:8000
echo ℹ️  Documentación interactiva: http://localhost:8000/docs
echo.
echo Presiona Ctrl+C para detener
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
goto fin

:ui
echo.
echo 📊 Iniciando UI Streamlit...
echo.
echo ℹ️  La UI estará disponible en: http://localhost:8501
echo.
echo Presiona Ctrl+C para detener
echo.
set PYTHONPATH=%CD%
streamlit run ui/app_enhanced.py
goto fin

:ambos
echo.
echo 🔄 Iniciando API y UI...
echo.
echo ℹ️  API: http://localhost:8000
echo ℹ️  UI:  http://localhost:8501
echo.
start "One Market API" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 >nul
start "One Market UI" cmd /k "set PYTHONPATH=%CD% && streamlit run ui/app_enhanced.py"
echo.
echo ✅ Servicios iniciados en ventanas separadas
echo.
pause
goto fin

:tests
echo.
echo 🧪 Ejecutando tests...
echo.
python -m pytest tests/ -v --tb=short
echo.
if errorlevel 1 (
    echo ❌ Algunos tests fallaron
) else (
    echo ✅ Todos los tests pasaron
)
pause
goto fin

:salir
echo.
echo 👋 Saliendo...
goto fin

:fin
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                  Gracias por usar ONE MARKET                ║
echo ╚════════════════════════════════════════════════════════════╝

