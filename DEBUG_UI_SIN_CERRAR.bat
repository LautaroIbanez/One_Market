@echo off
title ONE MARKET - Debug UI Sin Cerrar
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Debug UI Sin Cerrar             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🔍 DIAGNÓSTICO PASO A PASO:
echo.

echo 🔍 PASO 1: Verificando archivo de UI...
if exist "ui\app_complete.py" (
    echo ✅ app_complete.py existe
) else (
    echo ❌ app_complete.py NO existe
    echo.
    echo 🛑 Presiona cualquier tecla para continuar...
    pause >nul
    exit /b 1
)

echo.
echo 🔍 PASO 2: Verificando dependencias específicas...
echo Verificando Streamlit...
python -c "import streamlit; print('✅ Streamlit:', streamlit.__version__)" 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error con Streamlit
    echo.
    echo 🛑 Presiona cualquier tecla para continuar...
    pause >nul
    exit /b 1
)

echo Verificando Requests...
python -c "import requests; print('✅ Requests OK')" 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error con Requests
    echo.
    echo 🛑 Presiona cualquier tecla para continuar...
    pause >nul
    exit /b 1
)

echo Verificando Pandas...
python -c "import pandas; print('✅ Pandas OK')" 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error con Pandas
    echo.
    echo 🛑 Presiona cualquier tecla para continuar...
    pause >nul
    exit /b 1
)

echo Verificando Plotly...
python -c "import plotly; print('✅ Plotly OK')" 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error con Plotly
    echo.
    echo 🛑 Presiona cualquier tecla para continuar...
    pause >nul
    exit /b 1
)

echo.
echo 🔍 PASO 3: Verificando sintaxis del archivo UI...
python -c "import ast; ast.parse(open('ui/app_complete.py', 'r', encoding='utf-8').read()); print('✅ Sintaxis OK')" 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error de sintaxis en UI
    echo.
    echo 🛑 Presiona cualquier tecla para continuar...
    pause >nul
    exit /b 1
)

echo.
echo 🔍 PASO 4: Verificando puerto 8501...
netstat -an | findstr :8501
if %errorlevel% equ 0 (
    echo ⚠️  Puerto 8501 está en uso
    echo.
    echo 🛑 Presiona cualquier tecla para continuar...
    pause >nul
    exit /b 1
) else (
    echo ✅ Puerto 8501 disponible
)

echo.
echo 🔍 PASO 5: Probando ejecutar Streamlit...
echo ℹ️  Esto debería mostrar errores detallados
echo ℹ️  Presiona Ctrl+C si se cuelga
echo.

python -m streamlit run ui/app_complete.py --server.port 8501 --server.headless false

echo.
echo 🎯 Si llegaste aquí, la UI debería haber funcionado
echo.
echo 🛑 Presiona cualquier tecla para continuar...
pause >nul


