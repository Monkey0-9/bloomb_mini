import asyncio
import json
from typing import Any

import structlog
from fastapi import WebSocket

log = structlog.get_logger()

class BroadcastManager:
    """
    Manages WebSocket connections and centralizes data pushes.
    Refactored for Top 0.1% performance: One producer, many consumers.
    """
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self.latest_snapshot: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        # Immediately push the latest snapshot if it exists
        if self.latest_snapshot:
            await websocket.send_text(json.dumps(self.latest_snapshot))
        log.info("websocket.connected", count=len(self.active_connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        log.info("websocket.disconnected", count=len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcasts a message to all connected clients."""
        self.latest_snapshot = message
        if not self.active_connections:
            return

        async with self._lock:
            # Create tasks for parallel sending to avoid one slow client blocking others
            tasks = [
                self._safe_send(websocket, message)
                for websocket in self.active_connections
            ]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_send(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            # Client likely disconnected; will be cleaned up by disconnect()
            pass

# Global Singleton
broadcast_manager = BroadcastManager()
