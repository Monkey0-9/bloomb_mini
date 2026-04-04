from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import structlog

log = structlog.get_logger()

# --- CONSTANTS & REGISTRIES ---

# Mapping known large industrial coordinates to parent equities
# Format: "Facility Name": (lat, lon, industry, ticker, threshold_frp)
FACILITY_REGISTRY = {
    "ArcelorMittal Gent": (51.164, 3.820, "Steel", "MT", 150.0),
    "POSCO Gwangyang": (34.935, 127.731, "Steel", "005490.KS", 500.0),
    "Freeport Grasberg": (-4.058, 137.112, "Copper", "FCX", 100.0),
    "Cheniere Sabine Pass": (29.749, -93.879, "LNG", "LNG", 200.0),
    "Sibur Tobolsk": (58.201, 68.257, "Petrochem", "SIBN.ME", 80.0),
    "Tesla Giga Berlin": (52.397, 13.847, "Automotive", "TSLA", 20.0),
    "Reliance Jamnagar": (22.358, 69.868, "Refinery", "RELIANCE.NS", 600.0)
}

FIRMS_CSV_VIIRS_SNPP = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/Global/SUOMI_VIIRS_C2_Global_24h.csv"

# --- DATA CLASSES ---

@dataclass
class ThermalSignal:
    timestamp: datetime
    lat: float
    lon: float
    frp: float
    confidence: str
    facility_match: str | None = None
    ticker: str | None = None
    industry: str | None = None
    impact: str = "NEUTRAL"
    reason: str = ""

# --- CORE LOGIC ---

class ThermalPipeline:
    """
    Institutional Thermal Intelligence Pipeline.
    Detects industrial operational heat via NASA FIRMS telemetry.
    """
    def __init__(self, output_dir: Path = Path("data/processed/thermal")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._history: dict[str, list[float]] = {} # Track FRP history for baseline detection

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2) -> float:
        """Distance in km."""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    async def run_scan(self) -> list[ThermalSignal]:
        """
        Fetches and processes active industrial heat anomalies.
        """
        log.info("THERMAL_SCAN_INITIATED", source="FIRMS_VIIRS")
        signals = []

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(FIRMS_CSV_VIIRS_SNPP, timeout=30.0)
                resp.raise_for_status()

            lines = resp.text.splitlines()
            reader = csv.DictReader(lines)

            for row in reader:
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                frp = float(row['frp'])
                conf = row['confidence']

                # Filter for industrial heat profile (FRP > 5 for small, > 100 for large)
                if frp < 5.0: continue

                signal = self._evaluate_anomaly(lat, lon, frp, conf)
                if signal:
                    signals.append(signal)

            log.info("THERMAL_SCAN_COMPLETE", anomalies_found=len(signals))
            return signals

        except Exception as e:
            log.error("THERMAL_SCAN_FAILED", error=str(e))
            return []

    def _evaluate_anomaly(self, lat: float, lon: float, frp: float, conf: str) -> ThermalSignal | None:
        """
        Cross-references anomaly against facility registry.
        """
        now = datetime.now(UTC)

        # 1. Geo-fence Match
        matched_facility = None
        match_data = None

        for name, data in FACILITY_REGISTRY.items():
            dist = self._haversine(lat, lon, data[0], data[1])
            if dist < 2.5: # 2.5km radius for large industrial complexes
                matched_facility = name
                match_data = data
                break

        if not matched_facility:
            return None # Ignore natural/unmapped fires

        # 2. Operational Impact Analysis
        # If FRP exceeds baseline, it indicates increased industrial activity
        threshold = match_data[4]
        impact = "NEUTRAL"
        reason = "Standard operational heat signature."

        if frp > threshold * 1.5:
            impact = "BULLISH"
            reason = f"Significant heat spike at {matched_facility} (+50% vs baseline). Potential rampup."
        elif frp < threshold * 0.5:
            impact = "BEARISH"
            reason = f"Thermal output drop at {matched_facility}. Potential maintenance/shutdown."

        return ThermalSignal(
            timestamp=now,
            lat=lat,
            lon=lon,
            frp=frp,
            confidence=conf,
            facility_match=matched_facility,
            ticker=match_data[3],
            industry=match_data[2],
            impact=impact,
            reason=reason
        )

    def get_market_signals(self, signals: list[ThermalSignal]) -> list[dict[str, Any]]:
        """Distills thermal data into signal engine format."""
        market_signals = []
        for s in signals:
            if s.impact != "NEUTRAL":
                market_signals.append({
                    "ticker": s.ticker,
                    "type": "thermal_frp",
                    "impact": s.impact,
                    "confidence": 0.9 if s.confidence in ('h', '90', '100') else 0.7,
                    "headline": s.reason,
                    "metadata": {
                        "facility": s.facility_match,
                        "industry": s.industry,
                        "frp_value": s.frp,
                        "timestamp": s.timestamp.isoformat()
                    }
                })
        return market_signals

if __name__ == "__main__":
    import asyncio
    pipeline = ThermalPipeline()

    async def test():
        signals = await pipeline.run_scan()
        m_sigs = pipeline.get_market_signals(signals)
        print(f"Generated {len(m_sigs)} actionable industrial signals.")

    asyncio.run(test())
