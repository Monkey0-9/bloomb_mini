#!/bin/bash
# SatTrade Terminal - Institutional Setup script

echo "════════════════════════════════════════════════════════"
echo "  SATTRADE TERMINAL - INSTITUTIONAL SETUP ENGINE"
echo "════════════════════════════════════════════════════════"

# 1. Environment and Keys
if [ ! -f .env ]; then
    echo "[!] .env not found. Creating from .env.example..."
    cp .env.example .env
    echo "[*] WARNING: Please populate .env with real API keys."
fi

# 2. Key Generation (JWT RS256)
if [[ -z "$JWT_PRIVATE_KEY" ]]; then
    echo "[*] Generating institutional RS256 keypair..."
    ssh-keygen -t rsa -b 4096 -m PEM -f jwt.key -N ""
    openssl rsa -in jwt.key -pubout -outform PEM -out jwt.key.pub
    echo "[*] Keys generated. Update .env with base64 encoded strings for production."
fi

# 3. Pull/Build Containers
echo "[*] Orchestrating Docker containers..."
docker-compose build
docker-compose up -d

echo "════════════════════════════════════════════════════════"
echo "  SERVICES DEPLOYED"
echo "  Frontend: http://localhost:3000"
echo "  API Hub:  http://localhost:8000"
echo "  Metrics:  http://localhost:8000/metrics"
echo "════════════════════════════════════════════════════════"
