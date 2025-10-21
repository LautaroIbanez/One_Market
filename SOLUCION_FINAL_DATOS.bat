@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🎯 ONE MARKET - Solución Final de Datos           ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

REM Verificar que existe el archivo
if not exist "SOLUCION_FINAL_DATOS.py" (
    echo ❌ Error: No se encuentra SOLUCION_FINAL_DATOS.py
    pause
    exit /b 1
)

echo 🎯 Solución final para datos del sistema...
echo ℹ️  Este script:
echo    ✅ Prueba timeframes disponibles
echo    ✅ Crea datos simulados completos
echo    ✅ Prueba recomendaciones
echo    ✅ Prueba backtesting
echo    ✅ Verifica sistema completo
echo.

python SOLUCION_FINAL_DATOS.py

if errorlevel 1 (
    echo.
    echo ❌ Error en la solución final
    echo.
    echo 🆘 Soluciones:
    echo    1. Verifica que la API esté respondiendo
    echo    2. Revisa que numpy y pandas estén instalados
    echo    3. Ejecuta: pip install numpy pandas requests
    echo.
    pause
) else (
    echo.
    echo ✅ Solución final completada
    echo.
    echo 🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat
    echo ✅ El sistema está listo para usar
    echo.
    pause
)
