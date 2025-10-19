@echo off
echo ========================================
echo   One Market Enhanced UI v2.0
echo   Auto Strategy Selection
echo ========================================
echo.
echo Funcionalidades:
echo   - Seleccion automatica de mejor estrategia
echo   - Comparacion de todas las estrategias
echo   - Historial de trades
echo   - Perfiles de riesgo configurables
echo.
echo Abriendo en: http://localhost:8501
echo.
echo Presiona Ctrl+C para detener
echo ========================================
echo.

python -m streamlit run ui/app_enhanced.py

pause

