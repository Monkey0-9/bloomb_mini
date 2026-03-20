# SatTrade Terminal - Local Run Script (Windows)

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  SATTRADE TERMINAL - LOCAL EXECUTION" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan

# 1. Environment Check
if (-not (Test-Path .env)) {
    Write-Host "[!] .env not found. Please create it first." -ForegroundColor Red
    exit 1
}

# 2. Start Backend (in new terminal)
Write-Host "[*] Launching Backend API server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\satellite_trade; uvicorn src.api.server:app --reload --port 8000"

# 3. Start Frontend (in new terminal)
Write-Host "[*] Launching Frontend Development server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\satellite_trade\frontend; npm run dev"

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  LOCAL INSTANCE INITIALIZING" -ForegroundColor Green
Write-Host "  API: http://localhost:8000"
Write-Host "  Vite: http://localhost:3000 (check Vite output for port)"
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
