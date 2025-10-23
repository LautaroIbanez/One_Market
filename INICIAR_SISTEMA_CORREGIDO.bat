@echo off
title ONE MARKET - Sistema Corregido
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Sistema Corregido                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 🛑 Deteniendo todos los procesos...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM streamlit.exe >nul 2>&1

echo ⏳ Esperando 3 segundos...
timeout /t 3 /nobreak >nul

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0

echo 🧹 Limpiando caché...
python limpiar_cache_recomendaciones.py

echo 🌐 Iniciando API con código actualizado...
echo ℹ️  La API se iniciará en: http://localhost:8000
start "ONE MARKET API" cmd /k "cd /d %~dp0 && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo ⏳ Esperando 8 segundos para que la API se inicie...
timeout /t 8 /nobreak >nul

echo 🔬 Probando recomendación...
python debug_recommendation.py

echo.
echo ✅ ¡Sistema actualizado y funcionando!
echo.
echo 💡 Ahora deberías ver recomendaciones LONG/SHORT reales en la UI
echo 🌐 API: http://localhost:8000
echo 📊 UI: Ejecuta 'EJECUTAR_UI_COMPLETA.bat' para abrir la interfaz
echo.
pause

