from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Literal, cast

from src.live.aircraft import Aircraft, fetch_aircraft
from src.live.conflicts import ConflictEvent, get_all_conflicts
from src.live.environmental import EnvironmentalMonitor
from src.live.macro import get_macro_snapshot
from src.live.news import NewsItem, get_all_news
from src.live.quakes import Quake, get_latest_quakes
from src.live.thermal import ThermalCluster, get_global_thermal
from src.live.vessels import get_all_vessels
from src.live.topo import get_ocean_depth

logger = logging.getLogger(__name__)

MEMORY_FILE = "data/cache/swarm_memory.json"

@dataclass
class SwarmAgent:
    id: str
    persona: Literal["Cautious", "Aggressive", "Standard", "Weather-Sensitive", "Economic-Sensitive"]
    health: float  # 0.0 to 1.0 (1.0 = Optimal flow)
    lat: float
    lon: float
    vessel_type: str
    target_ticker: str | None
    anomalies_detected: list[dict[str, Any]] = field(default_factory=list)
    memory_score: float = 0.0  # Cumulative trauma/risk memory

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2)**2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2)
    return radius * 2 * math.asin(math.sqrt(a))

def _load_memory() -> dict[str, float]:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load swarm memory: {e}")
            return {}
    return {}

def _save_memory(memory: dict[str, float]) -> None:
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f)

_GTFI_CACHE: dict[str, Any] = {}
_GTFI_TS: float = 0.0


async def run_swarm_simulation() -> dict[str, Any]:
    global _GTFI_CACHE, _GTFI_TS

    now = time.time()
    if _GTFI_CACHE and (now - _GTFI_TS) < 60:
        return _GTFI_CACHE

    # Load persistent agent memory
    agent_memory = _load_memory()
    environmental = EnvironmentalMonitor()

    v_task = asyncio.to_thread(get_all_vessels, zones=[8, 9, 10, 1, 2])
    c_task = get_all_conflicts()
    t_task = get_global_thermal(top_n=30)
    n_task = get_all_news()
    q_task = asyncio.to_thread(get_latest_quakes)
    a_task = asyncio.to_thread(fetch_aircraft, ["MILITARY", "CARGO"])
    m_task = get_macro_snapshot()

    results = await asyncio.gather(
        v_task, c_task, t_task, n_task, q_task, a_task, m_task
    )

    vessels_dict = cast(dict[str, Any], results[0])
    conflicts = cast(list[ConflictEvent], results[1])
    thermal = cast(list[ThermalCluster], results[2])
    news = cast(list[NewsItem], results[3])
    quakes = cast(list[Quake], results[4])
    aircraft = cast(list[Aircraft], results[5])
    macro_data = cast(dict[str, Any], results[6])

    vessels = list(vessels_dict.values())

    # 1. Instantiate the swarm with Persona and Persistence
    swarm: list[SwarmAgent] = []
    available_personas = ["Cautious", "Aggressive", "Standard", "Weather-Sensitive", "Economic-Sensitive"]

    for v in vessels:
        if hasattr(v, "mmsi"):
            mmsi = str(getattr(v, "mmsi"))
            v_type_name = str(getattr(v, "vessel_type_name", "Cargo"))
            v_lat = float(getattr(v, "lat", 0.0))
            v_lon = float(getattr(v, "lon", 0.0))
        else:
            mmsi = str(v.get("mmsi", v.get("id", "0")))
            v_type_name = str(v.get("vessel_type", "Cargo"))
            v_lat = float(v.get("lat", 0.0))
            v_lon = float(v.get("lon", 0.0))

        p_index = sum(ord(c) for c in mmsi) % len(available_personas)

        ticker = None
        if "Tanker" in v_type_name:
            ticker = random.choice([
                "XOM", "CVX", "SHEL", "TTE", "BP", "EQNR", "FRO", "EURN", "DHT"
            ])
        elif "Cargo" in v_type_name or "Container" in v_type_name:
            ticker = random.choice([
                "ZIM", "AMKBY", "MATX", "DSX", "SBLK", "GOGL", "NMM", "DAC"
            ])
        elif "Bulk" in v_type_name:
            ticker = random.choice([
                "RIO", "BHP", "VALE", "FCX", "NUE", "MT", "CLF"
            ])

        # Apply persistent memory score (historical trauma)
        historical_trauma = agent_memory.get(mmsi, 0.0)
        initial_health = max(0.2, 1.0 - (historical_trauma * 0.1))

        swarm.append(SwarmAgent(
            id=mmsi,
            persona=cast(Any, available_personas[p_index]),
            health=initial_health,
            lat=v_lat,
            lon=v_lon,
            vessel_type=v_type_name,
            target_ticker=ticker,
            memory_score=historical_trauma
        ))

    # 2. Inject seeds into the parallel environment & evaluate
    for agent in swarm:
        # A. Conflict Impact (Geopolitical News/Violence)
        for c in conflicts:
            dist = _haversine(agent.lat, agent.lon, c.lat, c.lon)
            if dist < 800:
                impact = 0.0
                if agent.persona == "Aggressive":
                    impact = 0.3 * (800 - dist) / 800
                elif agent.persona == "Standard":
                    impact = 0.15 * (800 - dist) / 800
                elif agent.persona == "Cautious":
                    impact = 0.05 * (800 - dist) / 800

                agent.health = max(0.0, agent.health - impact)
                agent.memory_score += impact * 0.1
                agent.anomalies_detected.append({
                    "type": "WAR_ZONE", "dist": dist, "impact": impact
                })

        # B. Seismic Impact (Natural Disasters)
        for q in quakes:
            dist = _haversine(agent.lat, agent.lon, q.lat, q.lon)
            if dist < 1000 and q.mag >= 5.0:
                impact = 0.0
                if agent.persona == "Cautious":
                    impact = (q.mag / 10.0) * (1000 - dist) / 1000
                else:
                    impact = (q.mag / 20.0) * (1000 - dist) / 1000

                agent.health = max(0.0, agent.health - impact)
                agent.memory_score += impact * 0.05
                agent.anomalies_detected.append({
                    "type": "SEISMIC", "dist": dist, "impact": impact
                })

        # C. Thermal/Industrial Impact (Supply/Demand)
        for t in thermal:
            dist = _haversine(agent.lat, agent.lon, t.lat, t.lon)
            if dist < 300:
                if t.anomaly_sigma < -1.0:
                    agent.health = max(0.0, agent.health - 0.05)
                    agent.anomalies_detected.append({
                        "type": "THERMAL_BEARISH", "dist": dist
                    })
                elif t.anomaly_sigma > 1.0:
                    agent.health = min(1.0, agent.health + 0.02)

        # F. Environmental Impact (Open-Meteo Sea State & Air Quality via Public-APIs)
        if agent.vessel_type in ["Tanker", "Cargo", "Container"]:
            sea_state = await environmental.get_sea_state(agent.lat, agent.lon)
            if sea_state["status"] in ["SEVERE", "FOGGY"]:
                # High friction delay predicted
                multiplier = 2.0 if agent.persona == "Weather-Sensitive" else 1.0
                impact = 0.10 * (sea_state["wave_height"] / 4.0) * multiplier
                if sea_state["status"] == "FOGGY":
                    impact += 0.05 * multiplier
                
                agent.health = max(0.0, agent.health - impact)
                agent.anomalies_detected.append({
                    "type": "MARINE_WEATHER", 
                    "status": sea_state["status"],
                    "impact": round(impact, 3)
                })

        # I. Air Quality / Industrial Exhaust (Open-Meteo Air Quality from Public-APIs)
        # Higher PM2.5 in port areas indicates high industrial/trade activity (BULLISH)
        pm25 = await environmental.get_industrial_exhaust(agent.lat, agent.lon)
        if pm25 > 50:
            # High activity (BULLISH)
            agent.health = min(1.0, agent.health + 0.01)
            if pm25 > 150:
                # Extreme pollution might cause health/labor issues (BEARISH)
                agent.health = max(0.0, agent.health - 0.05)
                agent.anomalies_detected.append({
                    "type": "INDUSTRIAL_SMOG_DISRUPTION", 
                    "pm25": pm25,
                    "impact": 0.05
                })
            else:
                agent.anomalies_detected.append({
                    "type": "INDUSTRIAL_ACTIVITY_HIGH", 
                    "pm25": pm25,
                    "impact": -0.01 # Negative health impact is BULLISH in this context
                })

        # H. Ocean Depth / Topo Impact (Open Topo Data from Public-APIs)
        # Specifically for deep-draft vessels like VLCC tankers
        if "Tanker" in agent.vessel_type or "Bulk" in agent.vessel_type:
            topo = await get_ocean_depth(agent.lat, agent.lon)
            if topo["risk_level"] == "HIGH":
                # High grounding risk for VLCCs
                impact = 0.15 if agent.persona == "Cautious" else 0.05
                agent.health = max(0.0, agent.health - impact)
                agent.anomalies_detected.append({
                    "type": "SHALLOW_WATER_RISK", 
                    "depth": topo["depth_meters"],
                    "impact": impact
                })

        # D. Aviation Impact (Military/Cargo activity density)
        local_flights = [f for f in aircraft if _haversine(agent.lat, agent.lon, f.lat, f.lon) < 500]
        if local_flights:
            mil_count = sum(1 for f in local_flights if f.category == "MILITARY")
            if mil_count > 2:
                agent.health = max(0.0, agent.health - 0.1)
                agent.anomalies_detected.append({"type": "AERIAL_MIL_DENSITY", "count": mil_count})

        # E. News/OSINT Impact (Geopolitical/Maritime Alerts)
        relevant_news = [n for n in news if n.category in ["shipping", "geopolitics", "military", "energy"]]
        for n in relevant_news[:20]:
            impact_weight = 0.0
            title_upper = n.title.upper()
            if agent.target_ticker and agent.target_ticker in title_upper:
                impact_weight = 0.15
            elif any(kw in title_upper for kw in ["STRIKE", "ATTACK", "BLOCKADE", "SANCTION", "SUNK"]):
                impact_weight = 0.05

            if impact_weight > 0:
                persona_multiplier = 2.5 if agent.persona == "Aggressive" else 0.8 if agent.persona == "Cautious" else 1.0
                impact = impact_weight * persona_multiplier
                agent.health = max(0.0, agent.health - impact)
                agent.memory_score += impact * 0.2
                if impact > 0.1:
                    agent.anomalies_detected.append({
                        "type": "NEWS_ALERT", "source": n.source, "impact": impact
                    })

    # 2. Social Evolution & Influence Loop (MiroFish Multi-Agent Pattern)
    for i, a1 in enumerate(swarm):
        # Limit proximity checks to optimize performance for large swarms
        for j in range(i + 1, min(i + 50, len(swarm))):
            a2 = swarm[j]
            dist = _haversine(a1.lat, a1.lon, a2.lat, a2.lon)
            if dist < 200: # Social Proximity Threshold (KM)
                # Health contagion: agents influence each other's risk perception
                avg_health = (a1.health + a2.health) / 2.0
                a1.health = a1.health * 0.98 + avg_health * 0.02
                a2.health = a2.health * 0.98 + avg_health * 0.02

                # Memory sharing: traumatic events spread through the swarm
                avg_memory = (a1.memory_score + a2.memory_score) / 2.0
                a1.memory_score = a1.memory_score * 0.99 + avg_memory * 0.01
                a2.memory_score = a2.memory_score * 0.99 + avg_memory * 0.01

    # 3. Dynamic Temporal Memory Decay (MiroFish Engine)
    new_memory = {a.id: min(10.0, a.memory_score * 0.98) for a in swarm if a.memory_score > 0.01}
    _save_memory(new_memory)

    # 3. Calculate Global Trade Flow Index (GTFI)
    gtfi = sum(a.health for a in swarm) / len(swarm) if swarm else 1.0

    # 4. MiroFish Behavioral Divergence Discovery
    predictions: list[dict[str, Any]] = []
    impaired_tickers: dict[str, int] = {}
    for a in swarm:
        if a.health < 0.7 and a.target_ticker:
            impaired_tickers[a.target_ticker] = impaired_tickers.get(a.target_ticker, 0) + 1

    # Calculate Divergence Alpha
    for ticker, count in impaired_tickers.items():
        if count >= 1:
            # Multi-Persona Divergence Check
            active_personas = set(a.persona for a in swarm if a.target_ticker == ticker and a.health < 0.7)
            persona_bonus = len(active_personas) * 5.0 # Higher confidence if all personas agree

            conf = min(99.9, 80.0 + count * 2.5 + persona_bonus)
            predictions.append({
                "ticker": ticker,
                "prediction": (
                    f"MiroFish Divergence: {len(active_personas)} agent "
                    f"personas confirm systemic risk for {ticker}."
                ),
                "confidence": round(conf, 1),
                "action": "BEARISH",
                "divergence_score": round(count / (len(swarm) / 10), 3),
                "source": "MiroFish-Predictive-Core"
            })

    # Regional aggregation of health
    regions: dict[str, float] = {}
    for a in swarm:
        region = f"{round(a.lat/20)*20},{round(a.lon/20)*20}"
        regions[region] = regions.get(region, 0.0) + a.health

    for region, count in regions.items():
        if count >= 2:
            conf = min(99.9, 90.0 + count * 1.2)
            predictions.append({
                "region": region,
                "prediction": f"Maritime flow bottleneck clustering at {region}.",
                "confidence": round(conf, 1),
                "action": "WATCH",
                "impaired_agents": count
            })

    predictions = sorted(predictions, key=lambda x: x["confidence"], reverse=True)

    result = {
        "gtfi_score": round(gtfi, 3),
        "total_agents": len(swarm),
        "impaired_agents": sum(1 for a in swarm if a.health < 0.8),
        "predictions": predictions,
        "personas": {p: sum(1 for a in swarm if a.persona == p) for p in available_personas}
    }

    _GTFI_CACHE = result
    _GTFI_TS = now
    return result
