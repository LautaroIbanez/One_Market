@echo off
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Ejecutar Proyecto Completo         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo ℹ️  Este script ejecutará el proyecto completo de One Market
echo ℹ️  Incluye: API, UI enriquecida y verificaciones
echo.

echo 🔍 Verificando estado del sistema...
echo.

REM Verificar si Python está disponible
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado. Instala Python 3.11+
    pause
    exit /b 1
)

REM Verificar si Streamlit está instalado
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Streamlit no encontrado. Instalando...
    pip install streamlit plotly pandas requests
)

echo ✅ Python y dependencias verificadas
echo.

REM Verificar si la API está corriendo
echo 🌐 Verificando API...
powershell -Command "try { Invoke-RestMethod -Uri 'http://localhost:8000/health' -Method Get -TimeoutSec 5 | Out-Null; Write-Host '✅ API funcionando' } catch { Write-Host '❌ API no disponible' }"

echo.
echo 🚀 Iniciando UI de Streamlit...
echo ℹ️  La UI se abrirá en: http://localhost:8501
echo ℹ️  La API está en: http://localhost:8000
echo ℹ️  Documentación API: http://localhost:8000/docs
echo.

REM Ejecutar Streamlit
streamlit run ui/app_complete.py --server.port 8501 --server.headless true

echo.
echo 🎉 Proyecto ejecutado exitosamente
echo.
pause
