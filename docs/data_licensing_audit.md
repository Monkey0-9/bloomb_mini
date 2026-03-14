# Data Licensing Audit — Phase 0.2

> **GATE**: Legal sign-off required before any data ingestion begins.
> **Status**: DRAFT — Pending Review
> **Version**: 0.1.0
> **Date**: 2026-03-12

---

## Data Source Licensing Matrix

### Free-Tier Sources (Phase 1)

| Source | Provider | License Type | Commercial Use? | Redistribution? | Derivative Works? | Expiry | Cost | PII Present? | Phase 1? |
|---|---|---|---|---|---|---|---|---|---|
| Sentinel-1 (SAR, 10m) | ESA/Copernicus | Open (CC BY-SA 3.0 IGO) | **YES** | YES (with attribution) | YES | Perpetual | Free | NO | ✅ |
| Sentinel-2 (Optical, 10m) | ESA/Copernicus | Open (CC BY-SA 3.0 IGO) | **YES** | YES (with attribution) | YES | Perpetual | Free | NO | ✅ |
| Landsat-8/9 (30m optical+thermal) | USGS | Public Domain (no restrictions) | **YES** | YES | YES | Perpetual | Free | NO | ✅ |
| NOAA AIS | US Coast Guard/NOAA | Public Domain | **YES** | YES | YES | Perpetual | Free | Vessel MMSI only (not PII) | ✅ |
| OpenStreetMap Building Footprints | OSM Foundation | ODbL 1.0 | **YES** | YES (ODbL) | YES (ODbL) | Perpetual | Free | NO | ✅ |
| Copernicus DEM (30m) | ESA | Open (free for commercial) | **YES** | YES | YES | Perpetual | Free | NO | ✅ |

### Commercial Sources (Phase 2+ — Subject to Budget)

| Source | Provider | License Type | Commercial Use? | Redistribution? | Derivative Works? | Expiry | Cost | PII Present? | Phase? |
|---|---|---|---|---|---|---|---|---|---|
| PlanetScope (3m daily) | Planet Labs | Commercial API | **YES** (per contract) | **NO** (raw imagery) | YES (derived products) | Annual renewal | ~$1,500–3,000/mo (area-based) | NO | Phase 2 |
| SkySat (0.5m tasking) | Planet Labs | Commercial API | **YES** (per contract) | **NO** | YES | Per-task | ~$10–25/km² | NO | Phase 2 |
| Capella Space (SAR, 0.5m) | Capella Space | Commercial API | **YES** (per contract) | **NO** | YES | Annual renewal | ~$2,000–5,000/mo | NO | Phase 2 |
| Maxar (WorldView, 0.3m) | Maxar Technologies | Commercial EULA | **YES** (per contract) | **NO** | YES (with restrictions) | Annual renewal | ~$5,000–15,000/mo | NO | Phase 3 |
| Spire Maritime AIS | Spire Global | Commercial API | **YES** (per contract) | **NO** | YES | Annual renewal | ~$500–2,000/mo | Vessel MMSI | Phase 2 |
| exactEarth AIS | exactEarth | Commercial API | **YES** (per contract) | **NO** | YES | Annual renewal | ~$1,000–3,000/mo | Vessel MMSI | Phase 2 |

### Market Data Sources

| Source | Provider | License Type | Commercial Use? | Redistribution? | Derivative Works? | Expiry | Cost | PII Present? | Phase? |
|---|---|---|---|---|---|---|---|---|---|
| Yahoo Finance (price data) | Yahoo | Free API (non-commercial ToS) | **NO** | **NO** | Limited | N/A | Free | NO | Dev only |
| Alpha Vantage | Alpha Vantage | Free tier API | **YES** (limited) | **NO** | YES | Perpetual | Free (5 req/min) | NO | Phase 1 dev |
| Polygon.io | Polygon | Commercial API | **YES** | **NO** | YES | Monthly | ~$200/mo (starter) | NO | Phase 2 |
| Bloomberg Terminal | Bloomberg LP | Commercial | **YES** (per contract) | **NO** | YES (derived) | Annual | ~$2,000/mo/seat | NO | Phase 3 |
| FactSet Revere Supply Chain | FactSet | Commercial | **YES** | **NO** | YES | Annual | ~$3,000–5,000/mo | NO | Phase 2 |

---

## Red Flag Analysis

> [!WARNING]
> **Yahoo Finance**: Commercial Use = **NO** per Terms of Service. Automatically excluded from signal pipeline. Acceptable for development/research notebooks only. Must be replaced with Polygon.io or equivalent before any backtesting claims are made.

| Source | Red Flag | Severity | Remediation |
|---|---|---|---|
| Yahoo Finance | Non-commercial ToS | 🔴 HIGH | Use only for dev; replace with licensed data for backtest |
| NOAA AIS | MMSI could theoretically identify vessels/owners | 🟡 LOW | MMSI is not PII under US law; vessel names are public record |
| Planet Labs | Redistribution prohibited | 🟡 LOW | Only derived products (counts, features) leave the pipeline; raw imagery stays in our data lake |
| Maxar | Derivative work restrictions may limit signal sharing | 🟡 MEDIUM | Review contract clause before Phase 3; may need legal opinion |

---

## Phase 1 Approved Sources

For Phase 1 (port throughput signal, Asia-Pacific), the following sources are **cleared for use**:

| Source | Purpose | Commercial Use | Monthly Cost |
|---|---|---|---|
| Sentinel-1 | SAR vessel/container detection | ✅ | $0 |
| Sentinel-2 | Optical container/crane detection | ✅ | $0 |
| Copernicus DEM 30m | Terrain correction for SAR | ✅ | $0 |
| NOAA AIS | Vessel identity matching | ✅ | $0 |
| OpenStreetMap | Port facility footprints | ✅ | $0 |
| Alpha Vantage | Price data for backtesting (dev) | ✅ (limited) | $0 |

**Total Phase 1 data cost: $0/month** (within $2,000/mo budget)

---

## Contract & ToS References

| Source | Reference Document |
|---|---|
| Copernicus Sentinel | [Legal Notice on use of Copernicus data](https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice) |
| USGS Landsat | [Landsat Data Policy](https://www.usgs.gov/landsat-missions/landsat-data-access) |
| NOAA AIS | [NOAA AIS Data Access](https://marinecadastre.gov/ais/) |
| OpenStreetMap | [ODbL License](https://opendatacommons.org/licenses/odbl/) |
| Alpha Vantage | [API Terms of Service](https://www.alphavantage.co/terms_of_service/) |

---

## Sign-off Record

Formal sign-off is required from Legal, Risk, and CTO before any data from a new source is moved from `dev` to `prod`.

| Date | Officer | Role | Result | Comments |
|---|---|---|---|---|
| 2026-03-12 | Praveen P | CTO | **APPROVED** | Initial Phase 1 infra verification. |
| | | Legal | PENDING | |
| | | Risk | PENDING | |

### Schema definition for Sign-off Logs:
```json
{
  "source_id": "string",
  "approval_timestamp": "ISO8601",
  "approved_by": "uid",
  "role": "LEGAL | RISK | CTO",
  "restriction_tags": ["string"],
  "signature_hash": "sha256"
}
```
