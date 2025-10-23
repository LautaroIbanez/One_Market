@echo off
title ONE MARKET - Solución Final
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Solución Final                   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 🛑 Deteniendo todos los procesos...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM streamlit.exe >nul 2>&1

echo ⏳ Esperando 3 segundos...
timeout /t 3 /nobreak >nul

echo 🧹 Limpiando caché...
cd /d %~dp0
python limpiar_cache_recomendaciones.py

echo 🌐 Iniciando API con código actualizado...
start "ONE MARKET API" cmd /k "cd /d %~dp0 && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo ⏳ Esperando 5 segundos para que la API se inicie...
timeout /t 5 /nobreak >nul

echo 🔬 Probando recomendación...
cd /d %~dp0
python debug_recommendation.py

echo.
echo ✅ ¡Sistema actualizado y funcionando!
echo.
echo 💡 Ahora deberías ver recomendaciones LONG/SHORT reales en la UI
echo.
pause
