@echo off
title ONE MARKET - Reiniciar API y Probar
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Reiniciar API y Probar          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🛑 Deteniendo API anterior...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
echo ✅ API anterior detenida

echo ⏳ Esperando 5 segundos...
timeout /t 5 /nobreak >nul

echo.
echo 🧹 Limpiando caché de recomendaciones...
python limpiar_cache_recomendaciones.py
echo ✅ Caché limpiado

echo.
echo 🔧 Verificando código corregido...
python -c "
from app.service.daily_recommendation import DailyRecommendationService
service = DailyRecommendationService()
print('✅ Servicio de recomendaciones cargado correctamente')
"

echo.
echo 🌐 Reiniciando API con código corregido...
echo ℹ️  La API se iniciará en: http://localhost:8000
echo ℹ️  Esta ventana permanecerá abierta para monitorear la API
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo.
echo 🎯 Si llegaste aquí, la API se detuvo
echo.
echo 🛑 Presiona cualquier tecla para continuar...
pause >nul

