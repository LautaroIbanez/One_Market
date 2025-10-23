@echo off
title ONE MARKET - Reiniciar y Probar
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🔄 ONE MARKET - Reiniciar y Probar               ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Detener procesos de Python
echo 🛑 Deteniendo procesos existentes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Limpiar caché
echo 🧹 Limpiando caché...
python actualizar_base_datos.py

REM Iniciar API
echo 🌐 Iniciando API...
start "ONE MARKET API" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo ⏳ Esperando 5 segundos para que la API se inicie...
timeout /t 5 /nobreak >nul

REM Probar recomendación
echo 🔬 Probando recomendación...
python debug_recommendation.py

echo.
echo ✅ Prueba completada
echo.
pause
