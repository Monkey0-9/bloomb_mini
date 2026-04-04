# SatTrade Terminal - Windows Setup Script

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  SATTRADE TERMINAL - INSTITUTIONAL SETUP ENGINE" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan

# 1. Environment
if (-not (Test-Path .env)) {
    Write-Host "[*] .env not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

# 2. Key Generation (Mock for local run, replace with real RS256 in prod)
if (-not (Test-Path jwt.key)) {
    Write-Host "[*] Initializing security context..." -ForegroundColor Green
    # In a real scenario, we'd use OpenSSL or ssh-keygen here
    "Mock RS256 Private Key" | Out-File -FilePath jwt.key
}

# 3. Pull/Build/Run
Write-Host "[*] Orchestrating Docker containers..." -ForegroundColor Green
docker-compose build
docker-compose up -d

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  SERVICES DEPLOYED" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:3000"
Write-Host "  API Hub:  http://localhost:9009"
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
