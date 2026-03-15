# Supply Chain Map — SatTrade

## 1. Raw Ingest Layer
- **Source**: Copernicus CDSE (Sentinel-2) / Planet API
- **Tool**: `sentinel.py` (SentinelIngestor)
- **Validation**: SHA-256 Checksum, CDSE OAuth2

## 2. Preprocessing Layer
- **Operations**: Cloud Masking, 6S Atmospheric Correction, Orthorectification
- **Tool**: `optical.py` (OpticalPipeline)
- **Standard**: RMSE < 0.02 vs ESA reference

## 3. Signal Generation Layer
- **Operations**: Computer Vision (YOLOv8), Time-series Analysis
- **Tool**: `ic.py` (ICAnalyzer)
- **Gate**: Peak Spearman IC ≥ 0.03

## 4. Execution Layer
- **Operations**: Backtest Validation, Risk Checking, Alpaca Execution
- **Tool**: `engine.py` (BacktestEngine), `risk/engine.py` (RiskEngine)
- **Gate**: Max Gross 150%, VaR 99%
