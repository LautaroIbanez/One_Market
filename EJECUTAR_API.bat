@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🌐 ONE MARKET - Iniciando API FastAPI              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo ℹ️  La API estará disponible en: http://localhost:8000
echo ℹ️  Documentación interactiva: http://localhost:8000/docs
echo.

REM Verificar que existe main.py
if not exist "main.py" (
    echo ❌ Error: No se encuentra main.py
    echo.
    pause
    exit /b 1
)

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado
    echo.
    pause
    exit /b 1
)

echo ⏳ Iniciando servidor...
echo.
echo ⚠️  Presiona Ctrl+C para detener
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

REM Si hay error, pausar para ver el mensaje
if errorlevel 1 (
    echo.
    echo ❌ Error al iniciar la API
    echo ℹ️  Revisa el mensaje de error arriba
    echo.
    pause
)

