@echo off
title ONE MARKET - Reiniciar API Definitivo
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Reiniciar API Definitivo        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🛑 Deteniendo API anterior completamente...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
echo ✅ API anterior detenida

echo ⏳ Esperando 5 segundos para limpiar procesos...
timeout /t 5 /nobreak >nul

echo.
echo 🧹 Limpiando caché de recomendaciones...
python limpiar_cache_recomendaciones.py
echo ✅ Caché limpiado

echo.
echo 🔧 Verificando que el código corregido esté disponible...
python -c "from app.service.daily_recommendation import DailyRecommendationService; print('✅ Código corregido disponible')"

echo.
echo 🌐 Iniciando API con código corregido...
echo ℹ️  La API se iniciará en: http://localhost:8000
echo ℹ️  Esta ventana permanecerá abierta para monitorear la API
echo ℹ️  Presiona Ctrl+C para detener la API
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo.
echo 🎯 API detenida
echo.
echo 🛑 Presiona cualquier tecla para continuar...
pause >nul


