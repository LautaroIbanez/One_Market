@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🔧 ONE MARKET - Probar Capa de Datos Completa      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  IMPORTANTE: La API debe estar corriendo en puerto 8000
echo ℹ️  Si no está corriendo, ejecuta primero: EJECUTAR_API.bat
echo.

REM Verificar que existe el archivo
if not exist "PROBAR_CAPA_DATOS_COMPLETA.py" (
    echo ❌ Error: No se encuentra PROBAR_CAPA_DATOS_COMPLETA.py
    pause
    exit /b 1
)

echo 🔧 Probando nueva capa de datos implementada...
echo ℹ️  Este script prueba:
echo    ✅ Importación de nuevas clases
echo    ✅ DataFetcher con ccxt
echo    ✅ DataStore con Parquet + SQLite
echo    ✅ Validación de datos
echo    ✅ Integración con API
echo.

python PROBAR_CAPA_DATOS_COMPLETA.py

if errorlevel 1 (
    echo.
    echo ❌ Error en la prueba de capa de datos
    echo.
    echo 🆘 Soluciones:
    echo    1. Verifica que la API esté respondiendo
    echo    2. Revisa que pyarrow esté instalado: pip install pyarrow
    echo    3. Revisa que ccxt esté instalado: pip install ccxt
    echo    4. Verifica la conectividad a internet
    echo.
    pause
) else (
    echo.
    echo ✅ Prueba de capa de datos completada
    echo.
    echo 🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_UI_COMPLETA.bat
    echo ✅ El sistema completo está listo
    echo.
    pause
)





