@echo off
REM Run all One Market demos in sequence

echo ============================================================
echo ONE MARKET - Running All Demos
echo ============================================================

set PYTHONPATH=%CD%

echo.
echo [1/3] Running Epic 2 Demo - Core Modules...
echo ------------------------------------------------------------
python examples/example_core_usage.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR in Epic 2 demo
    exit /b 1
)

echo.
echo [2/3] Running Epic 3 Demo - Research Signals...
echo ------------------------------------------------------------
python examples/example_research_signals.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR in Epic 3 signals demo
    exit /b 1
)

echo.
echo [3/4] Running Epic 3 Demo - Complete Backtest...
echo ------------------------------------------------------------
python examples/example_backtest_complete.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR in Epic 3 backtest demo
    exit /b 1
)

echo.
echo [4/4] Running Epic 4 Demo - Daily Decision...
echo ------------------------------------------------------------
python examples/example_daily_decision.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR in Epic 4 decision demo
    exit /b 1
)

echo.
echo ============================================================
echo ALL 4 DEMOS COMPLETED SUCCESSFULLY!
echo ============================================================
echo.
echo Next steps:
echo   - Review SESSION_SUMMARY.md for complete summary
echo   - Check PROJECT_STATUS.md for roadmap
echo   - Review EPIC3_SUMMARY.md and EPIC4_SUMMARY.md
echo   - Run tests: .\run_tests.bat -v
echo.

