"""
Maritime Swarm Intelligence — MiroFish-inspired predictive simulation.
Predicts Global Trade Flow Index (GTFI) by correlating real-time seeds:
1. AIS Data (vessels.py)
2. Seismic Data (quakes.py)
3. News OSINT (news.py)
"""
import logging
import random
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.free_data import vessels, quakes, news

logger = logging.getLogger(__name__)

class AgentPersona(Enum):
    CAUTIOUS = "cautious"      # Extremely sensitive to risk/quakes
    AGGRESSIVE = "aggressive"  # Ignores minor risks to maintain schedule
    STANDARD = "standard"      # Balanced reaction

@dataclass
class MaritimeAgent:
    """A MiroFish-inspired maritime intelligence agent."""
    id: str
    name: str
    type: str         # Tanker, Container, etc.
    persona: AgentPersona
    location: str
    health: float = 1.0  # 0.0 to 1.0
    memory: list[str] = field(default_factory=list)
    risk_stance: float = 0.5

    def observe(self, seeds: dict):
        """Update agent state based on world seeds."""
        impact = 0.0
        
        # 1. Seismic Reactivity
        for q in seeds.get('quakes', []):
            if q.mag > 5.0:
                # Cautious agents are 50% more impacted by seismic activity
                sensitivity = 1.5 if self.persona == AgentPersona.CAUTIOUS else 0.8
                impact += (q.mag * 0.02 * sensitivity)
                self.memory.append(f"Felt M{q.mag} quake at {q.place}")

        # 2. News/Geopolitical Reactivity
        for n in seeds.get('news', []):
            if any(word in n.title.lower() for word in ["blockade", "conflict", "attack"]):
                # Aggressive agents are more impacted by geopolitical tension (insurance/war risk)
                sensitivity = 2.0 if self.persona == AgentPersona.AGGRESSIVE else 1.0
                impact += 0.1 * sensitivity
                self.memory.append(f"Alerted: {n.title[:30]}...")

        self.health = max(0.0, min(1.0, self.health - impact))
        if len(self.memory) > 5:
            self.memory.pop(0)

@dataclass
class SwarmAlert:
    id: str
    location: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    reason: str
    impact_tickers: list[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class TradeFlowSnapshot:
    global_index: float  # 0.0 to 1.0 (1.0 = optimal flow)
    alerts: list[SwarmAlert]
    congestion_map: dict[str, float]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class VesselSwarmEngine:
    """MiroFish-inspired Multi-Agent Coordination Engine."""
    
    def __init__(self):
        self.agents: dict[str, MaritimeAgent] = {}
        self.last_snapshot: TradeFlowSnapshot | None = None

    def _initialize_agents(self, ships: list[dict]):
        """Populate the swarm with persona-injected agents."""
        for s in ships[:50]: # Focus on top 50 major vessels for simulation quality
            ship_id = str(s.get('mmsi') or s.get('id'))
            if ship_id not in self.agents:
                persona = random.choice(list(AgentPersona))
                self.agents[ship_id] = MaritimeAgent(
                    id=ship_id,
                    name=s.get('name', 'Unknown Vessel'),
                    type=s.get('type', 'Cargo'),
                    persona=persona,
                    location=f"{s.get('lat', 0)}, {s.get('lon', 0)}",
                    risk_stance=0.3 if persona == AgentPersona.AGGRESSIVE else 0.7
                )

    async def run_simulation(self) -> TradeFlowSnapshot:
        """Execute one MiroFish simulation cycle."""
        try:
            tasks = [
                vessels.get_port_congestion(),
                quakes.get_latest_quakes(),
                news.query_gdelt("maritime defense shipping"),
                vessels.get_global_ships(limit=100)
            ]
            port_data, quake_data, news_data, ship_data = await asyncio.gather(*tasks)
            
            # 1. Update/Initialize Agents
            self._initialize_agents(ship_data)
            
            # 2. Propagate Seeds to Agents
            seeds = {'quakes': quake_data, 'news': news_data, 'ports': port_data}
            for agent in self.agents.values():
                agent.observe(seeds)
            
            # 3. Aggregate Swarm Intelligence
            if not self.agents:
                avg_health = 1.0
            else:
                avg_health = sum(a.health for a in self.agents.values()) / len(self.agents)
            
            alerts: list[SwarmAlert] = []
            # Surface agents in critical health (MiroFish profiling)
            for a in list(self.agents.values()):
                if a.health < 0.7:
                    alerts.append(SwarmAlert(
                        id=f"agent-{a.id}",
                        location=a.location,
                        risk_level="HIGH" if a.health < 0.4 else "MEDIUM",
                        reason=f"Agent {a.name} ({a.persona.value}) showing stress from regional seeds.",
                        impact_tickers=["AMKBY", "ZIM"]
                    ))

            congestion_map = {}
            for p in port_data[:5]:
                congestion_map[p.get('name', 'Unknown Port')] = p.get('congestion', 0.0)
            
            snapshot = TradeFlowSnapshot(
                global_index=round(avg_health, 2),
                alerts=alerts[:10],
                congestion_map=congestion_map,
                timestamp=datetime.now(timezone.utc)
            )
            self.last_snapshot = snapshot
            return snapshot
            
        except Exception as e:
            logger.error(f"Swarm simulation failed: {e}")
            return TradeFlowSnapshot(
                global_index=1.0, 
                alerts=[], 
                congestion_map={}, 
                timestamp=datetime.now(timezone.utc)
            )

swarm_engine = VesselSwarmEngine()
