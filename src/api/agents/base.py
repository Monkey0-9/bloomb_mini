from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import structlog
from src.common.message_bus import bus

log = structlog.get_logger()

class BaseAgent(ABC):
    """Base interface for all specialized agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.log = log.bind(agent=name)

    @abstractmethod
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a specific task and return a result."""
        pass

    async def run(self):
        """Main loop for the agent (if running as a service)."""
        self.log.info("agent_started")
        # In a microservice world, this would listen to a queue
        pass

    async def emit_signal(self, topic: str, payload: Any):
        """Emit a signal to the message bus."""
        self.log.info("agent_emit_signal", topic=topic)
        await bus.publish(topic, {"agent": self.name, "payload": payload})
