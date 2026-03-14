# Satellite-Based AI Trading System (SatTrade)

Production-grade, fully auditable trading signal system targeting global equities and commodities using satellite Earth Observation (EO) data.

## Hard Constraints (Defaults — Override in `config/constraints.yaml`)

| Parameter | Default | Rationale |
|---|---|---|
| Cloud Compute Budget | $5,000/mo | Modest; covers GPU training + storage |
| Data License Budget | $2,000/mo | Primarily free-tier (Sentinel, Landsat, NOAA AIS) |
| Cloud Provider | AWS `us-east-1` | Best EO data ecosystem, SageMaker, S3 COG support |
| Team | 1 engineer, 1 analyst | Solo/small-team research mode |
| Regulatory Framework | Internal Research Only | No live execution; paper trading only |
| Simulated NAV | $10,000,000 | Paper trading portfolio |

## Project Structure

```
satellite_trade/
├── config/                  # Constraints, environment, secrets references
├── docs/                    # Phase 0 artifacts (Signal Theory, Licensing, Architecture)
├── src/
│   ├── ingest/              # Phase 1: Data acquisition & ETL
│   ├── preprocess/          # Phase 2: Optical, SAR, Thermal pipelines
│   ├── annotate/            # Phase 3: Labeling & annotation quality
│   ├── features/            # Phase 4: Feature extraction & fusion
│   ├── signals/             # Phase 5: Signal modeling
│   ├── backtest/            # Phase 6: Backtesting engine
│   ├── execution/           # Phase 7: Execution simulator & risk engine
│   ├── monitoring/          # Phase 8: Drift detection & dashboards
│   └── common/              # Shared utilities, logging, schemas
├── tests/                   # Unit + integration tests
├── notebooks/               # Research & exploration
├── infrastructure/          # IaC (Terraform/CDK)
└── agents/                  # Sub-agent prompt templates
```

## Phase Timeline

| Phase | Scope | Duration |
|---|---|---|
| Phase 1 | 1 signal (port throughput), 1 region (Asia-Pacific), equities | 16 weeks |
| Phase 2 | Multi-signal, global coverage | +12 weeks |
| Phase 3 | Live paper trading | +8 weeks |

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run quality gates
python -m src.ingest.quality_gates --check
```

## License

Proprietary — Internal Research Only
