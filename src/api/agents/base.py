from abc import ABC, abstractmethod
from typing import Any, Dict
from datetime import datetime, timezone

class BaseAgent(ABC):
    """Base class for all institutional-grade intelligence agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.status = "INITIALIZING"
        self.last_sync = None

    @abstractmethod
    async def get_state(self) -> Dict[str, Any]:
        """Returns the current state/data from this agent's domain."""
        pass

    @abstractmethod
    async def process_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a specific task dispatched by the orchestrator."""
        pass

    def get_health(self) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "status": self.status,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None
        }
