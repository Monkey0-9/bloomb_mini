import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from src.api.agents.maritime import MaritimeAgent
from src.api.agents.signal_alpha import SignalAgent
from src.api.agents.macro import MacroAgent
from src.api.agents.risk import RiskAgent
from src.api.agents.analyst import AnalystAgent
from src.api.agents.fundamentals import FundamentalAgent
from src.api.agents.news import NewsAgent
from src.api.agents.execution import ExecutionAgent
from src.api.agents.flight import FlightAgent
from src.api.agents.satellite import SatelliteAgent

log = logging.getLogger(__name__)

class SignalOrchestrator:
    """Central nervous system of the SatTrade Terminal."""
    
    def __init__(self):
        self.agents = {
            "maritime": MaritimeAgent(),
            "flight": FlightAgent(),
            "signals": SignalAgent(),
            "macro": MacroAgent(),
            "risk": RiskAgent(),
            "analyst": AnalystAgent(),
            "fundamentals": FundamentalAgent(),
            "news": NewsAgent(),
            "execution": ExecutionAgent(),
            "satellite": SatelliteAgent()
        }
        self.status = "ACTIVE"
        self._last_state = {}

    async def get_unified_state(self) -> Dict[str, Any]:
        """Aggregates state from all agents into a single unified context."""
        states = await asyncio.gather(*[agent.get_state() for agent in self.agents.values()])
        return {name: state for name, state in zip(self.agents.keys(), states)}

    async def dispatch_task(self, agent_name: str, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches a specific task to an agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not found"}
        return await agent.process_task(task_type, params)

    def get_system_health(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": [agent.get_health() for agent in self.agents.values()]
        }
