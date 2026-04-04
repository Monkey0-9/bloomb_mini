"""
SatTrade Institutional Message Bus.
Provides topic-based Pub/Sub with guaranteed delivery patterns.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Message:
    topic: str
    payload: dict[str, Any]
    timestamp: str = ""
    msg_id: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()


class MessageBus:
    """
    Topic-based Message Bus for SatTrade.
    Singleton. Provides topic-based routing compatible with BlazingMQ patterns.
    """

    _instance: MessageBus | None = None

    def __new__(cls) -> MessageBus:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self) -> None:
        # Guard against re-initialisation on repeated MessageBus() calls
        if getattr(self, "__initialized", False):
            return
        self._topics: dict[str, list[asyncio.Queue[Message]]] = {}
        self._lock: asyncio.Lock | None = None
        self.__initialized = True

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        """Publish a message to a topic."""
        msg = Message(topic=topic, payload=payload)
        logger.debug("bus.publish: %s", topic)
        async with self._get_lock():
            for q in self._topics.get(topic, []):
                await q.put(msg)

    async def subscribe(self, topic: str) -> asyncio.Queue[Message]:
        """Subscribe to a topic and return a queue."""
        async with self._get_lock():
            if topic not in self._topics:
                self._topics[topic] = []
            q: asyncio.Queue[Message] = asyncio.Queue(maxsize=1000)
            self._topics[topic].append(q)
            return q

    async def unsubscribe(self, topic: str, q: asyncio.Queue[Message]) -> None:
        """Unsubscribe from a topic."""
        async with self._get_lock():
            bucket = self._topics.get(topic, [])
            if q in bucket:
                bucket.remove(q)


# Global singleton for the application
bus = MessageBus()
