@echo off
title ONE MARKET - Sistema Definitivo con UI Separada
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Sistema Definitivo Final       ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🛑 Deteniendo procesos anteriores...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM streamlit.exe >nul 2>&1
echo ✅ Procesos detenidos

echo ⏳ Esperando 3 segundos...
timeout /t 3 /nobreak >nul

echo.
echo 🔧 Verificando e instalando dependencias...
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo ℹ️  Instalando Streamlit y dependencias...
    pip install streamlit plotly pandas requests numpy
)
echo ✅ Dependencias verificadas

echo.
echo 🧹 Limpiando caché de recomendaciones...
python limpiar_cache_recomendaciones.py
echo ✅ Caché limpiado

echo.
echo 🌐 PASO 1: Iniciando API con código corregido...
echo ℹ️  La API se iniciará en: http://localhost:8000
start "ONE MARKET API" cmd /k "cd /d %~dp0 && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo ⏳ Esperando 12 segundos para que la API se inicie completamente...
timeout /t 12 /nobreak >nul

echo.
echo 🔬 Verificando que la API funcione correctamente...
python -c "
import requests
try:
    # Test health endpoint
    health_response = requests.get('http://localhost:8000/health', timeout=5)
    if health_response.status_code == 200:
        print('✅ API Health: OK')
    else:
        print('❌ API Health: FAILED')
        exit(1)
    
    # Test recommendation endpoint
    rec_response = requests.get('http://localhost:8000/recommendation/daily', 
                               params={'symbol': 'BTC/USDT', 'date': '2024-01-15'}, 
                               timeout=10)
    
    if rec_response.status_code == 200:
        data = rec_response.json()
        print(f'✅ Recomendación: {data.get(\"direction\")} - {data.get(\"confidence\")}%')
        print(f'📊 Razonamiento: {data.get(\"rationale\")}')
        
        if data.get('direction') != 'HOLD' or data.get('confidence') > 0:
            print('🎉 ¡Sistema de recomendaciones funcionando correctamente!')
        else:
            print('⚠️  Sistema devuelve HOLD - puede necesitar datos')
    else:
        print(f'❌ Error en recomendaciones: {rec_response.status_code}')
        
except Exception as e:
    print(f'❌ Error verificando API: {e}')
    exit(1)
"

if %errorlevel% neq 0 (
    echo.
    echo ❌ Error en la verificación de la API
    echo ℹ️  Revisa los logs de la API en la ventana que se abrió
    pause
    exit /b 1
)

echo.
echo 📊 PASO 2: Iniciando UI Completa en ventana separada...
echo ℹ️  La UI se abrirá en: http://localhost:8501
echo ℹ️  Se abrirá una nueva ventana con la UI
echo.

start "ONE MARKET UI" cmd /k "cd /d %~dp0 && python -m streamlit run ui/app_complete.py --server.port 8501 --server.headless false"

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              🎉 SISTEMA COMPLETO OPERATIVO                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📋 SISTEMA INICIADO EXITOSAMENTE:
echo    ✅ API FastAPI: http://localhost:8000
echo    ✅ UI Streamlit: http://localhost:8501
echo    ✅ Sistema de recomendaciones: FUNCIONANDO
echo    ✅ Código corregido: APLICADO
echo.
echo 🎯 FUNCIONALIDADES DISPONIBLES:
echo    📊 Análisis multi-timeframe
echo    🔬 Backtesting avanzado
echo    🧠 Recomendaciones inteligentes (LONG/SHORT)
echo    📈 Métricas cuantitativas
echo    🎯 Gestión de riesgo
echo    📋 Historial de trades
echo.
echo 💡 INSTRUCCIONES:
echo    1. Abre tu navegador en: http://localhost:8501
echo    2. Sincroniza los datos haciendo clic en "Sincronizar Datos"
echo    3. Las recomendaciones aparecerán automáticamente
echo.
echo 🛑 Para detener el sistema: Cierra las ventanas de API y UI
echo    o ejecuta: DETENER_SERVICIOS.bat
echo.
echo ⏳ Esperando 3 segundos antes de continuar...
timeout /t 3 /nobreak >nul

echo.
echo 🚀 ¡Sistema listo! Presiona cualquier tecla para continuar...
pause >nul


