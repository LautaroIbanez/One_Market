@echo off
REM Script helper para ejecutar tests de One Market
REM Configura PYTHONPATH y ejecuta pytest

set PYTHONPATH=%CD%
python -m pytest %*

