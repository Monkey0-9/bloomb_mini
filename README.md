# SatTrade Terminal: Institutional-Grade EO-Intel Terminal

SatTrade is a high-fidelity, production-ready trading intelligence terminal that fuses Satellite Earth Observation (EO) data with quantitative financial benchmarks. It provides defensible alpha by cross-referencing global maritime, aviation, and thermal signals against equity and macro drivers.

## 🚀 Key Features & Differentiators

- **3D World Intelligence**: Real-time WebGL globe visualizing global maritime and aviation freight.
- **Dark Vessel Intelligence**: Sentinel-1 SAR backscatter cross-referencing to detect and validate vessels with silent transponders (Dark Fleet).
- **TFT Quantile Forecasting**: Temporal Fusion Transformer (TFT) modeling providing P10/P50/P90 price range forecasts on all tracked equities.
- **NLP Command Engine**: Bloomberg-style command bar with semantic natural language intent routing.
- **Macro Correlation Hub**: Lead-lag Spearman ρ analysis correlating satellite observations with global macro indicators (Inflation, Industrial Production).
- **Weighted Alpha Scoring**: Principled signal fusion (Thermal > Maritime > Aviation) based on historical Information Coefficient (IC).

## 🛠️ Project Structure

```
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

## ⚡ Quick Start

### Backend (Python 3.11+)
```bash
pip install -r requirements.txt
python src/api/server.py
```

### Frontend (Node 18+)
```bash
cd frontend
npm install
npm run dev
```

## 🧪 Verification
The system has been verified for institutional use:
- **Build**: `npm run build` verified.
- **Signals**: Weighted IC-logic verified.
- **Intelligence**: SAR-validated dark vessel detection operational.

## License
Proprietary — Internal Research & Alpha Generation.
