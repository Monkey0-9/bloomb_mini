from abc import ABC, abstractmethod
from typing import Any

import structlog

from src.common.message_bus import bus

log = structlog.get_logger()

class BaseAgent(ABC):
    """Base interface for all specialized agents."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.log = log.bind(agent=name)

    @abstractmethod
    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        """Process a specific task and return a result."""
        pass

    async def run(self) -> None:
        """Main loop for the agent (if running as a service)."""
        self.log.info("agent_started")
        # In a microservice world, this would listen to a queue
        pass

    async def emit_signal(self, topic: str, payload: Any) -> None:
        """Emit a signal to the message bus."""
        self.log.info("agent_emit_signal", topic=topic)
        await bus.publish(topic, {"agent": self.name, "payload": payload})
