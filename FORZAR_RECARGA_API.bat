@echo off
title ONE MARKET - Forzar Recarga API
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Forzar Recarga API              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🛑 Deteniendo API completamente...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
echo ✅ API detenida

echo ⏳ Esperando 5 segundos...
timeout /t 5 /nobreak >nul

echo.
echo 🧹 Limpiando todo el caché...
python limpiar_cache_recomendaciones.py
echo ✅ Caché limpiado

echo.
echo 🔧 Verificando archivo corregido...
python -c "
import os
file_path = 'app/service/daily_recommendation.py'
if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'No signals available for analysis' in content:
        print('❌ Archivo contiene código anterior')
    else:
        print('✅ Archivo contiene código corregido')
else:
    print('❌ Archivo no encontrado')
"

echo.
echo 🔄 Forzando recarga de módulos Python...
python -c "
import sys
modules_to_clear = [m for m in sys.modules.keys() if 'app.service.daily_recommendation' in m]
for module in modules_to_clear:
    del sys.modules[module]
print('✅ Módulos limpiados')
"

echo.
echo 🌐 Reiniciando API con recarga forzada...
echo ℹ️  La API se iniciará en: http://localhost:8000
echo ℹ️  Esta ventana permanecerá abierta para monitorear la API
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app

echo.
echo 🎯 API detenida
echo.
echo 🛑 Presiona cualquier tecla para continuar...
pause >nul



