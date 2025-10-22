@echo off
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Ejecutar UI Simple                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📦 Instalando dependencias...
pip install streamlit plotly pandas requests

echo.
echo 🚀 Iniciando UI de Streamlit...
echo ℹ️  La UI se abrirá en: http://localhost:8501
echo ℹ️  Asegúrate de que la API esté corriendo en: http://localhost:8000
echo.

REM Ejecutar Streamlit
streamlit run ui/app_complete.py --server.port 8501

echo.
echo 🎉 UI ejecutada exitosamente
echo.
pause