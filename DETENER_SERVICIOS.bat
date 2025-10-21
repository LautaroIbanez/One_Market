@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🛑 ONE MARKET - Detener Servicios                  ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 🔍 Buscando procesos en puertos 8000 y 8501...
echo.

REM Verificar si hay procesos en puerto 8000
netstat -ano | findstr ":8000" >nul 2>&1
if errorlevel 1 (
    echo ✅ Puerto 8000 libre
) else (
    echo ⚠️  Puerto 8000 ocupado - deteniendo procesos...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
        echo   🔄 Deteniendo PID %%a...
        taskkill /F /PID %%a >nul 2>&1
        if errorlevel 1 (
            echo   ❌ No se pudo detener PID %%a
        ) else (
            echo   ✅ PID %%a detenido
        )
    )
)

echo.

REM Verificar si hay procesos en puerto 8501
netstat -ano | findstr ":8501" >nul 2>&1
if errorlevel 1 (
    echo ✅ Puerto 8501 libre
) else (
    echo ⚠️  Puerto 8501 ocupado - deteniendo procesos...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501"') do (
        echo   🔄 Deteniendo PID %%a...
        taskkill /F /PID %%a >nul 2>&1
        if errorlevel 1 (
            echo   ❌ No se pudo detener PID %%a
        ) else (
            echo   ✅ PID %%a detenido
        )
    )
)

echo.

REM Detener procesos específicos por nombre
echo 🔄 Deteniendo procesos de Streamlit...
taskkill /F /IM streamlit.exe >nul 2>&1
if errorlevel 1 (
    echo ✅ No hay procesos de Streamlit corriendo
) else (
    echo ✅ Procesos de Streamlit detenidos
)

echo 🔄 Deteniendo procesos de uvicorn...
taskkill /F /IM uvicorn.exe >nul 2>&1
if errorlevel 1 (
    echo ✅ No hay procesos de uvicorn corriendo
) else (
    echo ✅ Procesos de uvicorn detenidos
)

echo.
echo 🔍 Verificación final de puertos...
netstat -ano | findstr ":8000" >nul 2>&1
if errorlevel 1 (
    echo ✅ Puerto 8000 liberado
) else (
    echo ⚠️  Puerto 8000 aún ocupado
)

netstat -ano | findstr ":8501" >nul 2>&1
if errorlevel 1 (
    echo ✅ Puerto 8501 liberado
) else (
    echo ⚠️  Puerto 8501 aún ocupado
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              ✅ PROCESO COMPLETADO                         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo ℹ️  Ahora puedes ejecutar:
echo    - EJECUTAR_API.bat
echo    - EJECUTAR_UI.bat
echo.
echo ℹ️  Si los puertos siguen ocupados, reinicia tu computadora.
echo.
pause

