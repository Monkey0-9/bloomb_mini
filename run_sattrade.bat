@echo off
title SatTrade 24/7 Runtime
echo ============================================================
echo SatTrade 24/7 Continuous Execution Service
echo ============================================================
echo Starting Python Runtime Orchestrator...
echo.

:: Ensure we are in project root
cd /d %~dp0

:: Check for virtualenv
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

:: Run orchestrator
python src\runtime_orchestrator.py

echo.
echo Orchestrator stopped.
pause
