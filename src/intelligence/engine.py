"""
Global Intelligence Engine — The Brain of SatTrade.
Discovers signals from global open data with ZERO hardcoded locations.
Unified wrapper around live telemetry modules.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx

from src.intelligence.swarm import run_swarm_simulation
from src.live.aircraft import Aircraft, fetch_aircraft
from src.live.conflicts import ConflictEvent, get_all_conflicts
from src.live.news import get_all_news
from src.live.orbits import SatOrbit, get_all_eo_satellites
from src.live.quakes import Quake, get_latest_quakes
from src.live.thermal import ThermalCluster, get_global_thermal

logger = logging.getLogger(__name__)

@dataclass
class WorldIntelligenceReport:
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    threat_score: float = 0.0
    signals: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""

class GlobalIntelligenceEngine:
    """
    Unified intelligence engine that synthesizes physical telemetry into alpha.
    """
    def __init__(self):
        self._client = httpx.Client(timeout=30)
        self._nominatim_url = "https://nominatim.openstreetmap.org/reverse"

    async def get_global_aircraft(self) -> list[Aircraft]:
        """Fetch all tracked high-interest aircraft."""
        return await asyncio.to_thread(fetch_aircraft)

    async def get_global_thermal(self) -> list[ThermalCluster]:
        """Discover industrial hotspots globally."""
        return await get_global_thermal()

    async def get_global_earthquakes(self) -> list[Quake]:
        """Track significant seismic activity."""
        return await asyncio.to_thread(get_latest_quakes)

    async def get_global_conflicts(self) -> list[ConflictEvent]:
        """Track global conflict and violence events."""
        return await get_all_conflicts()

    async def get_global_satellites(self) -> list[SatOrbit]:
        """Propagate all EO satellite positions."""
        return await asyncio.to_thread(get_all_eo_satellites)

    async def get_world_intelligence_report(self) -> WorldIntelligenceReport:
        """Synthesize a unified global risk/alpha report."""
        # Run all data gathering in parallel
        thermal_task = self.get_global_thermal()
        quakes_task = self.get_global_earthquakes()
        conflicts_task = self.get_global_conflicts()
        swarm_task = run_swarm_simulation()
        news_task = get_all_news()

        thermal, quakes, conflicts, swarm, news = await asyncio.gather(
            thermal_task, quakes_task, conflicts_task, swarm_task, news_task
        )

        # 1. Start with Swarm Intelligence baseline
        gtfi = swarm.get("gtfi_score", 1.0)
        threat = 1.0 - gtfi  # Lower flow = higher threat

        signals = []

        # 2. Extract top predictions from the swarm
        for p in swarm.get("predictions", [])[:5]:
            signals.append({
                "source": "swarm",
                "impact": p["action"],
                "reason": f"{p['prediction']} (Confidence: {p['confidence']}%)",
                "ticker": p.get("ticker")
            })

        # 3. Layer in raw telemetry signals
        for t in thermal:
            if t.anomaly_sigma > 2.0:
                threat += 0.05
                signals.append({
                    "source": "thermal",
                    "impact": "BULLISH",
                    "reason": t.signal_reason,
                    "ticker": t.tickers[0] if t.tickers else None
                })

        for q in quakes:
            if q.mag > 6.0:
                threat += 0.15
                signals.append({"source": "seismic", "impact": "RISK", "reason": f"M{q.mag} quake at {q.place}"})

        for c in conflicts:
            if c.severity == "CRITICAL":
                threat += 0.1
                signals.append({
                    "source": "conflict",
                    "impact": "BEARISH",
                    "reason": f"Conflict in {c.country}: {c.fatalities} fatalities",
                    "ticker": c.financial_tickers[0] if c.financial_tickers else None
                })

        # 4. Integrate News Sentiment
        for n in news[:10]:
            if n.tickers:
                signals.append({
                    "source": "news",
                    "impact": "INFO",
                    "reason": f"Breaking news for {', '.join(n.tickers)}: {n.title}",
                    "ticker": n.tickers[0]
                })

        return WorldIntelligenceReport(
            threat_score=round(min(1.0, threat), 2),
            signals=signals,
            summary=f"Unified Intelligence Engine identified {len(signals)} significant alpha/risk signals. Global Flow Index (GTFI) is at {gtfi:.2f}."
        )

    # Legacy method for compatibility if needed
    async def get_thermal_signals(self) -> list[ThermalCluster]:
        return await self.get_global_thermal()

