# SatTrade Alpha-Prime v3.0 // Institutional Intelligence Terminal
**Top 1% Global Intelligence & Execution Architecture**

SatTrade Alpha-Prime is a high-frequency multi-agent intelligence system designed to outperform legacy platforms (Bloomberg, Capital IQ) through direct physical-world telemetry fusion.

## 💎 Institutional-Grade Stack
- **Core Engine**: C++20 with Lock-Free HFT Queues and SIMD-optimized neural analysis.
- **Intelligence**: Spearman IC-recalibrated WeightOptimizer with Bayesian pattern discovery.
- **Execution**: Ultra-low latency OMS supporting Equities and Multi-leg Options (Puts/Calls).
- **Frontend**: High-density React Terminal with GPU-accelerated 3D Global Monitoring.

## 🚀 Key Features
### 1. AlphaFusion™ C++ Engine
- Sub-microsecond GTFI (Global Trade Flow Index) recalculation.
- Compiled Black-Scholes pricing with full GREEKS (Delta, Gamma, Vega, Theta).
- Monte Carlo Value-at-Risk (VaR) simulation at 99% confidence.

### 2. Physical-World Telemetry (Zero-Fake)
- **Maritime**: Real-time AIS fusion via ERDDAP/NOAA with dark vessel detection.
- **Thermal**: NASA FIRMS VIIRS/MODIS industrial facility operate-rate discovery.
- **Geopolitical**: ACLED/UCDP/GDELT automated OSINT harvesting with version-fallback robustness.

### 3. MiroFish Multi-Agent Swarm
- Simulation-based intelligence using "Cautious", "Aggressive", and "Standard" agent personas.
- Dynamic sentiment synthesis from global market feeds and RSS streams.

## 🛠️ Deployment Instructions
### Build C++ Core
```bash
cd cpp_core
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

### Start Intelligence Backend
```bash
python -m src.api.server
```

### Start Intelligence UI
```bash
cd frontend
npm install
npm run dev
```

---
*Developed for Institutional-Grade Surgical Operations. (c) 2026 SatTrade Global.*
