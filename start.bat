@echo off
echo =======================================================
echo SatTrade Global Intelligence Engine - Boot Sequence
echo =======================================================

echo [1/2] Starting Python Backend API (Port 8000)...
start "SatTrade API" cmd /c ".\.venv\Scripts\python -m src.api.server"

echo [2/2] Starting React Frontend (Port 5173)...
cd frontend
start "SatTrade UI" cmd /c "npm run dev"

echo.
echo Both systems have been initiated in separate windows.
echo - Backend API: http://localhost:8000
echo - Frontend UI: http://localhost:5173
echo.
pause
