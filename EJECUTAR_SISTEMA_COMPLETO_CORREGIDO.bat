@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Sistema Completo (Corregido)       ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 🎯 Iniciando sistema completo One Market...
echo.

echo [1/4] 🔧 Verificando sistema...
call INICIALIZAR_SISTEMA_COMPLETO.bat
if errorlevel 1 (
    echo ❌ Error en verificación del sistema
    pause
    exit /b 1
)

echo.
echo [2/4] 🌐 Iniciando API...
echo ℹ️  Ejecutando API en segundo plano...
start /B "One Market API" cmd /c "EJECUTAR_API.bat"

echo ⏳ Esperando que la API se inicie...
timeout /t 15 /nobreak >nul

echo ✅ API iniciada

echo.
echo [3/4] 📊 Sincronizando datos (formato corregido)...
echo ℹ️  Sincronizando datos reales con formato correcto...
call SYNC_DATOS_SIMPLE.bat

echo.
echo [4/4] 📊 Iniciando UI Completa...
echo ℹ️  Abriendo interfaz de usuario completa...
start "One Market UI" cmd /c "EJECUTAR_UI_COMPLETA.bat"

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              🎉 SISTEMA COMPLETO OPERATIVO                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📋 SISTEMA INICIADO:
echo    ✅ API FastAPI: http://localhost:8000
echo    ✅ UI Streamlit: http://localhost:8501
echo    ✅ Datos sincronizados (formato corregido)
echo    ✅ Sistema completo operativo
echo.
echo 🎯 FUNCIONALIDADES DISPONIBLES:
echo    📊 Análisis multi-timeframe
echo    🔬 Backtesting avanzado
echo    🧠 Recomendaciones inteligentes
echo    📈 Métricas cuantitativas
echo    🎯 Gestión de riesgo
echo    📋 Historial de trades
echo.
echo ℹ️  Para detener el sistema: DETENER_SERVICIOS.bat
echo.
pause
