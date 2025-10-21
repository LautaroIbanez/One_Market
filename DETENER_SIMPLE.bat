@echo off
echo.
echo 🛑 DETENIENDO SERVICIOS ONE MARKET
echo.

echo 🔄 Deteniendo procesos en puerto 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    echo   Deteniendo PID %%a
    taskkill /F /PID %%a
)

echo 🔄 Deteniendo procesos en puerto 8501...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501"') do (
    echo   Deteniendo PID %%a
    taskkill /F /PID %%a
)

echo 🔄 Deteniendo Streamlit...
taskkill /F /IM streamlit.exe

echo 🔄 Deteniendo uvicorn...
taskkill /F /IM uvicorn.exe

echo.
echo ✅ PROCESO COMPLETADO
echo.
pause
