@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🔧 ONE MARKET - Probar Sistema Completo          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

echo 🔧 Probando que el sistema completo funciona sin errores...
echo ℹ️  Este script prueba:
echo    ✅ Salud de la API
echo    ✅ Sincronización de datos
echo    ✅ Recomendaciones (sin timeframe 15m)
echo    ✅ Backtest (con parámetros corregidos)
echo    ✅ Diagnóstico completo del sistema
echo.

REM Verificar que existe el archivo
if not exist "PROBAR_SISTEMA_COMPLETO.py" (
    echo ❌ Error: No se encuentra PROBAR_SISTEMA_COMPLETO.py
    pause
    exit /b 1
)

python PROBAR_SISTEMA_COMPLETO.py

if errorlevel 1 (
    echo.
    echo ❌ Error en la prueba del sistema
    echo.
    echo 🆘 Soluciones:
    echo    1. Verifica que la API esté corriendo
    echo    2. Revisa que los datos estén sincronizados
    echo    3. Verifica la conectividad a internet
    echo    4. Revisa los logs de la API para más detalles
    echo.
    pause
) else (
    echo.
    echo ✅ Prueba del sistema completada
    echo.
    echo 🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat
    echo ✅ El sistema completo está funcionando
    echo.
    pause
)



