@echo off
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Ejecutar Todo el Sistema          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo ℹ️  Este script ejecutará la API y la UI de One Market
echo ℹ️  Presiona Ctrl+C para detener todo
echo.

REM Verificar si Python está disponible
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado. Instala Python 3.11+
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo.

REM Instalar dependencias si es necesario
echo 📦 Verificando dependencias...
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Instalando Streamlit y dependencias...
    pip install streamlit plotly pandas requests fastapi uvicorn
)

echo ✅ Dependencias verificadas
echo.

REM Verificar si la API ya está corriendo
echo 🌐 Verificando API...
powershell -Command "try { Invoke-RestMethod -Uri 'http://localhost:8000/health' -Method Get -TimeoutSec 3 | Out-Null; Write-Host '✅ API ya está corriendo' } catch { Write-Host '🔄 API no detectada, se iniciará automáticamente' }"

echo.
echo 🚀 Iniciando sistema completo...
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                     📋 INFORMACIÓN                        ║
echo ║                                                             ║
echo ║  🌐 API: http://localhost:8000                             ║
echo ║  📊 UI:  http://localhost:8501                             ║
echo ║  📚 Docs: http://localhost:8000/docs                       ║
echo ║                                                             ║
echo ║  ⚠️  IMPORTANTE:                                           ║
echo ║  - La fecha del sistema está en 2025-10-22                ║
echo ║  - Las recomendaciones mostrarán esa fecha                 ║
echo ║  - Para cambiar fecha: Configuración de Windows            ║
echo ║                                                             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Función para ejecutar API en background
start "ONE MARKET API" cmd /k "cd /d %~dp0 && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo ⏳ Esperando que la API se inicie...
timeout /t 5 /nobreak >nul

echo ✅ API iniciada
echo.

echo 🚀 Iniciando UI de Streamlit...
echo ℹ️  La UI se abrirá automáticamente en tu navegador
echo.

REM Ejecutar UI
streamlit run ui/app_complete.py --server.port 8501 --server.headless false

echo.
echo 🎉 Sistema ejecutado exitosamente
echo.
echo 💡 Para detener todo:
echo    1. Cierra esta ventana
echo    2. Cierra la ventana de la API
echo.
pause
