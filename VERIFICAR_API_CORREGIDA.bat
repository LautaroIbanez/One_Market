@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🔧 ONE MARKET - Verificar API Corregida           ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 🔧 Verificando que la API funciona con la nueva capa de datos...
echo ℹ️  Este script verifica:
echo    ✅ Importaciones corregidas
echo    ✅ Nueva capa de datos funcionando
echo    ✅ Esquemas de paper trading
echo    ✅ Endpoints de API
echo.

REM Verificar que existe el archivo
if not exist "VERIFICAR_API_CORREGIDA.py" (
    echo ❌ Error: No se encuentra VERIFICAR_API_CORREGIDA.py
    pause
    exit /b 1
)

python VERIFICAR_API_CORREGIDA.py

if errorlevel 1 (
    echo.
    echo ❌ Error en la verificación de API
    echo.
    echo 🆘 Soluciones:
    echo    1. Verifica que pyarrow esté instalado: pip install pyarrow
    echo    2. Verifica que ccxt esté instalado: pip install ccxt
    echo    3. Revisa que no haya errores de sintaxis
    echo.
    pause
) else (
    echo.
    echo ✅ Verificación de API completada
    echo.
    echo 🎯 PRÓXIMO PASO: Ejecutar EJECUTAR_API.bat
    echo ✅ La API está lista para funcionar
    echo.
    pause
)




