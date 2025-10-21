@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🔍 DIAGNÓSTICO DETALLADO DE PUERTOS                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 🔍 Verificando puerto 8000 (API)...
echo.
echo 📋 Procesos en puerto 8000:
netstat -ano | findstr ":8000"
if errorlevel 1 (
    echo ✅ Puerto 8000 completamente libre
) else (
    echo ⚠️  Puerto 8000 está ocupado
    echo.
    echo 📋 Detalles de procesos:
    for /f "tokens=2,5" %%a in ('netstat -ano ^| findstr ":8000"') do (
        echo   Puerto: %%a - PID: %%b
        tasklist /FI "PID eq %%b" 2>nul | findstr /V "INFO:"
    )
)
echo.

echo 🔍 Verificando puerto 8501 (UI)...
echo.
echo 📋 Procesos en puerto 8501:
netstat -ano | findstr ":8501"
if errorlevel 1 (
    echo ✅ Puerto 8501 completamente libre
) else (
    echo ⚠️  Puerto 8501 está ocupado
    echo.
    echo 📋 Detalles de procesos:
    for /f "tokens=2,5" %%a in ('netstat -ano ^| findstr ":8501"') do (
        echo   Puerto: %%a - PID: %%b
        tasklist /FI "PID eq %%b" 2>nul | findstr /V "INFO:"
    )
)
echo.

echo 🔍 Verificando procesos Python/Streamlit...
echo.
echo 📋 Procesos Python activos:
tasklist | findstr python.exe
if errorlevel 1 (
    echo ✅ No hay procesos Python activos
) else (
    echo ⚠️  Hay procesos Python activos
)

echo.
echo 📋 Procesos Streamlit activos:
tasklist | findstr streamlit.exe
if errorlevel 1 (
    echo ✅ No hay procesos Streamlit activos
) else (
    echo ⚠️  Hay procesos Streamlit activos
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              📊 RESUMEN DEL DIAGNÓSTICO                     ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Verificación final
netstat -ano | findstr ":8000" >nul 2>&1
if errorlevel 1 (
    echo ✅ Puerto 8000: LIBRE
) else (
    echo ❌ Puerto 8000: OCUPADO
)

netstat -ano | findstr ":8501" >nul 2>&1
if errorlevel 1 (
    echo ✅ Puerto 8501: LIBRE
) else (
    echo ❌ Puerto 8501: OCUPADO
)

echo.
echo ℹ️  Si algún puerto está OCUPADO, ejecuta DETENER_SERVICIOS.bat
echo ℹ️  Si todos están LIBRES, puedes ejecutar EJECUTAR_API.bat
echo.
pause
