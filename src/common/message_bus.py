import asyncio
from typing import Any, Callable, Dict, List
import structlog

log = structlog.get_logger()

class MessageBus:
    """
    A simple async message bus for inter-agent communication.
    Can be swapped for NATS/Kafka in Phase 3.
    """
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, topic: str, callback: Callable) -> None:
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
        log.info("bus_subscribed", topic=topic)

    async def publish(self, topic: str, message: Any) -> None:
        log.info("bus_publish", topic=topic)
        if topic in self._subscribers:
            tasks = [asyncio.create_task(cb(message)) for cb in self._subscribers[topic]]
            if tasks:
                await asyncio.gather(*tasks)

# Singleton instance for the monolith (transition step)
bus = MessageBus()
