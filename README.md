# 🛰️ SatTrade Terminal: Institutional-Grade EO-Intel Terminal

SatTrade is a high-fidelity, production-ready trading intelligence terminal that fuses Satellite Earth Observation (EO) data with quantitative financial benchmarks. It provides defensible alpha by cross-referencing global maritime, aviation, and thermal signals against equity and macro drivers.

---

## ✨ Features

- **🌍 3D World Intelligence**: Real-time WebGL globe visualizing global maritime and aviation freight.
- **🛰️ Live Intelligence Seeds**: Production-grade data fusion from 10+ real-time sources:
    - **Thermal**: NASA FIRMS (VIIRS/SNPP) industrial heat monitoring.
    - **Seismic**: USGS real-time earthquake triggering.
    - **Environmental**: OpenAQ & Open-Meteo Air Quality (PM2.5) and Sea State.
    - **Macro**: FRED (St. Louis Fed) financial benchmarks.
- **🕵️ Dark Vessel Intelligence**: Sentinel-1 SAR backscatter cross-referencing to detect and validate vessels with silent transponders (Dark Fleet).
- **📈 TFT Quantile Forecasting**: Temporal Fusion Transformer (TFT) modeling providing P10/P50/P90 price range forecasts on all tracked equities.
- **⌨️ NLP Command Engine**: Bloomberg-style command bar with semantic natural language intent routing.
- **🧬 Weighted Alpha Scoring**: Principled signal fusion (Thermal > Maritime > Aviation) based on historical Information Coefficient (IC).

---

## 🏗️ Project Structure

```text
satellite_trade/
├── src/
│   ├── ingest/              # Data acquisition (Sentinel, Landsat, AIS, OpenSky)
│   ├── preprocess/          # Optical, SAR, and Thermal processing pipelines
│   ├── maritime/            # Dark vessel detection and port congestion logic
│   ├── signals/             # Weighted composite scoring and TFT forecasting
│   └── common/              # Shared schemas, config, and logging
├── frontend/                # React 18 / TypeScript / Tailwind / Framer Motion
│   ├── src/views/           # functional World, Matrix, Chart, and Economics views
│   └── src/lib/             # NLP Command Engine and Store
└── tests/                   # Comprehensive unit and integration test suite
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, FastAPI, PyTorch, Scikit-Learn, Pandas, NumPy, Rasterio.
- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite, Framer Motion, Globe.gl.
- **Data**: Sentinel-1/2, Landsat, AIS, OpenSky, NASA FIRMS, USGS.
- **Infrastructure**: Docker, GitHub Actions (CI/CD), SQLite/Redis.

---

## 🚀 Getting Started

### 📋 Prerequisites

- **Python**: 3.11+
- **Node.js**: 18+ (LTS recommended)
- **C++ Build Tools**: Required for native dependencies (Visual Studio Build Tools for Windows).
- **Docker** (Optional): For containerized deployment.

### ⚙️ Environment Setup

Copy `.env.example` to `.env` and fill in the required keys:

```bash
cp .env.example .env
```

### 🐍 Backend (Python)

1. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch Server**:
   ```bash
   uvicorn src.api.server:app --reload
   ```

### ⚛️ Frontend (React)

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Launch App**:
   ```bash
   npm run dev
   ```

---

## 🧪 Testing & Quality

### Python Tests
```bash
pytest
```

### Frontend Linting
```bash
cd frontend
npm run lint
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
