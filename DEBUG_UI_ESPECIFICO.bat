@echo off
title ONE MARKET - Debug UI Específico
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Debug UI Específico             ║
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
    pause
    exit /b 1
)

echo.
echo 🔍 PASO 2: Verificando dependencias específicas...
python -c "import streamlit; print('✅ Streamlit:', streamlit.__version__)"
python -c "import requests; print('✅ Requests OK')"
python -c "import pandas; print('✅ Pandas OK')"
python -c "import plotly; print('✅ Plotly OK')"

echo.
echo 🔍 PASO 3: Verificando sintaxis del archivo UI...
python -c "
import ast
try:
    with open('ui/app_complete.py', 'r', encoding='utf-8') as f:
        source = f.read()
    ast.parse(source)
    print('✅ Sintaxis del archivo UI: OK')
except SyntaxError as e:
    print(f'❌ Error de sintaxis en UI: {e}')
    exit(1)
except Exception as e:
    print(f'❌ Error leyendo archivo UI: {e}')
    exit(1)
"

echo.
echo 🔍 PASO 4: Probando importar el archivo UI...
python -c "
try:
    import sys
    sys.path.append('.')
    import ui.app_complete
    print('✅ Archivo UI se puede importar correctamente')
except Exception as e:
    print(f'❌ Error importando UI: {e}')
    exit(1)
"

echo.
echo 🔍 PASO 5: Verificando puerto 8501...
netstat -an | findstr :8501
if %errorlevel% equ 0 (
    echo ⚠️  Puerto 8501 está en uso
) else (
    echo ✅ Puerto 8501 disponible
)

echo.
echo 🔍 PASO 6: Probando ejecutar Streamlit con verbose...
echo ℹ️  Esto debería mostrar errores detallados
echo ℹ️  Presiona Ctrl+C si se cuelga
echo.

python -m streamlit run ui/app_complete.py --server.port 8501 --server.headless false --logger.level debug

echo.
echo 🎯 Si llegaste aquí, la UI debería haber funcionado
echo.
pause



