@echo off
title ONE MARKET - Ejecutar Todo Completo
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Ejecutar Todo Completo           ║
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

echo ⏳ Esperando 3 segundos...
timeout /t 3 /nobreak >nul

echo.
echo 🔧 Verificando e instalando dependencias...
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo ℹ️  Instalando Streamlit...
    pip install streamlit plotly pandas requests numpy
)

echo.
echo 🌐 PASO 1: Iniciando API...
echo ℹ️  La API se iniciará en: http://localhost:8000
start "ONE MARKET API" cmd /k "cd /d %~dp0 && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo ⏳ Esperando 10 segundos para que la API se inicie...
timeout /t 10 /nobreak >nul

echo.
echo 🔬 Verificando que la API funcione...
python -c "
import requests
try:
    response = requests.get('http://localhost:8000/health', timeout=5)
    if response.status_code == 200:
        print('✅ API funcionando correctamente')
    else:
        print('❌ API no responde correctamente')
except Exception as e:
    print(f'❌ Error verificando API: {e}')
"

echo.
echo 📊 PASO 2: Iniciando UI...
echo ℹ️  La UI se abrirá en: http://localhost:8501
echo ℹ️  Usando python -m streamlit para evitar problemas de PATH
echo.

python -m streamlit run ui/app_simple_test.py --server.port 8501 --server.headless false

echo.
echo 🎉 Sistema ejecutado
pause

