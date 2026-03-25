"""
Maritime Swarm Intelligence — MiroFish-inspired predictive simulation.
Predicts Global Trade Flow Index (GTFI) by correlating real-time seeds:
1. AIS Data (vessels.py)
2. Seismic Data (quakes.py)
3. News OSINT (news.py)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio

from src.free_data import vessels, quakes, news

logger = logging.getLogger(__name__)

@dataclass
class SwarmAlert:
    id: str
    location: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    reason: str
    impact_tickers: list[str]
    timestamp: datetime = datetime.now(timezone.utc)

@dataclass
class TradeFlowSnapshot:
    global_index: float  # 0.0 to 1.0 (1.0 = optimal flow)
    alerts: list[SwarmAlert]
    congestion_map: dict[str, float]
    timestamp: datetime = datetime.now(timezone.utc)

class VesselSwarmEngine:
    """Simulates maritime trade disruption agents."""
    
    def __init__(self):
        self.last_snapshot: TradeFlowSnapshot | None = None

    async def run_simulation(self) -> TradeFlowSnapshot:
        """Execute one simulation cycle using real-world seeds."""
        try:
            # Gather intelligence seeds
            tasks = [
                vessels.get_port_congestion() if hasattr(vessels, 'get_port_congestion') else asyncio.sleep(0, []),
                quakes.get_latest_quakes(),
                news.query_gdelt("maritime defense shipping"),
                vessels.get_global_ships(limit=100)
            ]
            # Handle the case where vessels.py might not have get_port_congestion yet
            port_data, quake_data, news_data, ship_data = await asyncio.gather(*tasks)
            
            alerts = []
            congestion_map = {}
            risk_points = 0
            
            # 1. Seismic Disruption Agent
            for q in quake_data:
                if q.is_near_chokepoint:
                    risk_points += (q.mag * 2)
                    alerts.append(SwarmAlert(
                        id=f"quake-{q.id}",
                        location=q.place,
                        risk_level="HIGH" if q.mag > 6 else "MEDIUM",
                        reason=f"Seismic activity M{q.mag} near maritime chokepoint.",
                        impact_tickers=q.impact_tickers
                    ))

            # 2. News/Geopolitical Agent
            for n in news_data:
                impactful_words = ["attack", "blockade", "strike", "closed", "conflict"]
                if any(word in n.title.lower() for word in impactful_words):
                    risk_points += 5
                    alerts.append(SwarmAlert(
                        id=f"news-{n.link[-10:]}",
                        location="Global",
                        risk_level="HIGH",
                        reason=f"OSINT alert: {n.title}",
                        impact_tickers=["ZIM", "AMKBY"]
                    ))

            # 3. Port Congestion Agent (Mocked/Inferred based on MiroFish seeds)
            base_flow = 0.95
            disruption = min(0.6, risk_points / 50.0)
            global_index = round(base_flow - disruption, 2)
            
            snapshot = TradeFlowSnapshot(
                global_index=global_index,
                alerts=alerts[:10],
                congestion_map={"Suez": 0.2, "Panama": 0.4}, # Initial map
                timestamp=datetime.now(timezone.utc)
            )
            self.last_snapshot = snapshot
            return snapshot
            
        except Exception as e:
            logger.error(f"Swarm simulation failed: {e}")
            return TradeFlowSnapshot(global_index=1.0, alerts=[], congestion_map={}, timestamp=datetime.now(timezone.utc))

swarm_engine = VesselSwarmEngine()
