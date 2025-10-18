@echo off
REM Run One Market Streamlit UI

echo ============================================================
echo ONE MARKET - Starting Streamlit Dashboard
echo ============================================================
echo.

set PYTHONPATH=%CD%

REM Check if API should be used
set /p USE_API="Connect to API? (y/n, default=n): "

if /i "%USE_API%"=="y" (
    echo.
    echo Starting API-connected UI...
    echo Make sure API is running: python main.py
    echo.
    streamlit run ui/app_api_connected.py
) else (
    echo.
    echo Starting standalone UI...
    echo.
    streamlit run ui/app.py
)

