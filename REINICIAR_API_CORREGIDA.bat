@echo off
title ONE MARKET - Reiniciar API Corregida
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Reiniciar API Corregida           ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 🛑 Deteniendo API anterior...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1

echo ⏳ Esperando 5 segundos...
timeout /t 5 /nobreak >nul

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0

echo 🧹 Limpiando caché de Python...
python -c "import sys; print('Python path:', sys.path)"

echo 🌐 Iniciando API corregida...
echo ℹ️  La API se iniciará en: http://localhost:8000
echo ℹ️  Presiona Ctrl+C para detener la API
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

