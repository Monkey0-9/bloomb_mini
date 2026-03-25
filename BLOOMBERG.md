# SatTrade: Institutional Bloomberg Engineering Guide

This document outlines the high-performance engineering patterns and tools from Bloomberg's open-source portfolio integrated into SatTrade.

## 🚀 Tier 1: Real-Time Infrastructure (Implemented/Integrated)

### [blazingmq-sdk-python](https://github.com/bloomberg/blazingmq-sdk-python)
- **Role**: Institutional-grade message bus.
- **SatTrade Use**: Replaces the simple WebSocket broadcast loop. AIS, Thermal, and Seismic data are published to topics. If a stream goes down, messages are queued and delivered when the service recovers.
- **Setup**: `pip install blazingmq-sdk-python`.

### [stricli](https://github.com/bloomberg/stricli)
- **Role**: Typed CLI builder for TypeScript.
- **SatTrade Use**: Powers the terminal command bar. Every command (e.g., `RESEARCH`, `NAV`, `SQUAWK`) is properly typed with argument validation.
- **Setup**: `npm install @stricli/core`.

## 🔍 Tier 2: Performance & Observability (Toolkit Ready)

### [memray](https://github.com/bloomberg/memray)
- **Role**: Python memory profiler.
- **SatTrade Use**: Essential for monitoring the memory footprint of large geospatial datasets (FIRMS, NOAA AIS).
- **Procedure**: Run `memray run -o output.bin uvicorn src.api.server:app` to find leaks in real-time ingestion.

### [pystack](https://github.com/bloomberg/pystack)
- **Role**: Python stack debugger.
- **SatTrade Use**: Attach to the FastAPI process to debug hung async tasks without restarting.
- **Procedure**: `pystack remote {PID}` to see exactly where a data fetch is blocked.

## 🧠 Tier 3: Signal Science (Learning & Patterns)

### [bbit-learning-labs](https://github.com/bloomberg/bbit-learning-labs)
- **Role**: Bloomberg's internal finance and ML training materials.
- **SatTrade Use**: Follow the notebooks in this repo to replace the hardcoded "alpha scores" with real IC/ICIR (Information Coefficient) calculations.
- **Action**: Clone locally to study professional signal backtesting patterns.

---

**Mission Status**: SatTrade is now aligned with Bloomberg's high-fidelity engineering standards. 
- **Real-World AIS**: LIVE (NOAA/Kystverket)
- **Hardened Analysis**: LIVE (Analyst/SSE)
- **Institutional News**: LIVE (RSS/NewsAPI-Harden)
- **Zero-Response Fixed**: LIVE (Token Aligned)
- **Zero-404 Stability**: LIVE (Routes Fixed)
