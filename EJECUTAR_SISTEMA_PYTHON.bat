@echo off
title ONE MARKET - Sistema Completo (Python)
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Sistema Completo (Python)        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo ℹ️  Iniciando sistema completo usando Python directamente
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

REM Instalar dependencias si es necesario
echo 📦 Verificando dependencias...
python -c "import fastapi, uvicorn, streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Instalando dependencias faltantes...
    python -m pip install fastapi uvicorn streamlit plotly pandas requests
    echo ✅ Dependencias instaladas
) else (
    echo ✅ Todas las dependencias están instaladas
)
echo.

REM Iniciar API usando Python
echo 🌐 Iniciando API usando Python...
start "ONE MARKET API" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo ⏳ Esperando que la API se inicie...
timeout /t 5 /nobreak >nul

echo ✅ API iniciada en http://localhost:8000
echo.

REM Iniciar UI usando Python
echo 🚀 Iniciando UI usando Python...
echo ℹ️  La UI se abrirá en: http://localhost:8501
echo.

python -m streamlit run ui/app_complete.py --server.port 8501 --server.headless false

echo.
echo 🎉 Sistema ejecutado exitosamente
echo.
echo 💡 URLs del sistema:
echo    🌐 API: http://localhost:8000
echo    📊 UI:  http://localhost:8501
echo    📚 Docs: http://localhost:8000/docs
echo.
pause
