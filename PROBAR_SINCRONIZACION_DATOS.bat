@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🔧 ONE MARKET - Probar Sincronización de Datos    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

echo 🔧 Probando sincronización de datos con la API corregida...
echo ℹ️  Este script prueba:
echo    ✅ Salud de la API
echo    ✅ Sincronización de múltiples símbolos/timeframes
echo    ✅ Endpoint de recomendaciones
echo    ✅ Diagnóstico de errores HTTP 400
echo.

REM Verificar que existe el archivo
if not exist "PROBAR_SINCRONIZACION_DATOS.py" (
    echo ❌ Error: No se encuentra PROBAR_SINCRONIZACION_DATOS.py
    pause
    exit /b 1
)

python PROBAR_SINCRONIZACION_DATOS.py

if errorlevel 1 (
    echo.
    echo ❌ Error en la prueba de sincronización
    echo.
    echo 🆘 Soluciones:
    echo    1. Verifica que la API esté corriendo
    echo    2. Revisa que pyarrow esté instalado: pip install pyarrow
    echo    3. Verifica la conectividad a internet
    echo    4. Revisa los logs de la API para más detalles
    echo.
    pause
) else (
    echo.
    echo ✅ Prueba de sincronización completada
    echo.
    echo 🎯 PRÓXIMO PASO: Probar la UI
    echo ✅ La sincronización debería funcionar correctamente
    echo.
    pause
)



