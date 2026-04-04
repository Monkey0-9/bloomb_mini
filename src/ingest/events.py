"""
Kafka Event Emitter — Phase 1.2

Event-driven ingest pattern: new tile available → emit Kafka event →
downstream consumers. Never poll on a cron if events are available.

Events:
  - raw.tiles.new      — New tile ingested successfully
  - raw.tiles.rejected — Tile failed quality gate
  - raw.tiles.blocked  — Tile blocked by licensing
  - raw.tiles.duplicate— Duplicate tile detected
  - processed.tiles    — Tile preprocessing complete
  - signals.scored     — Signal scored and ready for execution
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EventTopic(str, Enum):
    RAW_TILE_NEW = "raw.tiles.new"
    RAW_TILE_REJECTED = "raw.tiles.rejected"
    RAW_TILE_BLOCKED = "raw.tiles.blocked"
    RAW_TILE_DUPLICATE = "raw.tiles.duplicate"
    PROCESSED_TILE = "processed.tiles"
    SIGNAL_SCORED = "signals.scored"
    RISK_ALERT = "risk.alerts"
    KILL_SWITCH = "risk.kill_switch"
    MODEL_REGISTERED = "models.registered"
    DRIFT_DETECTED = "monitoring.drift"
    PIPELINE_FAILURE = "pipeline.failures"


@dataclass
class PipelineEvent:
    """Structured event for the pipeline event bus."""

    event_id: str
    topic: str
    timestamp_utc: str
    source: str
    payload: dict[str, Any]
    version: str = "1.0"

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def create(
        cls,
        topic: EventTopic,
        source: str,
        payload: dict[str, Any],
    ) -> PipelineEvent:
        return cls(
            event_id=str(uuid.uuid4()),
            topic=topic.value,
            timestamp_utc=datetime.now(UTC).isoformat(),
            source=source,
            payload=payload,
        )


class EventEmitter:
    """
    Kafka event emitter for pipeline orchestration.

    In production: uses kafka-python KafkaProducer.
    For local dev: stores events in memory and logs them.
    """

    def __init__(
        self,
        bootstrap_servers: str | None = None,
        use_local: bool = True,
    ) -> None:
        self._use_local = use_local
        self._local_events: list[PipelineEvent] = []
        self._local_queue: Any | None = None
        self._producer = None

        if use_local:
            import queue

            self._local_queue = queue.Queue()

        if not use_local and bootstrap_servers:
            try:
                from kafka import KafkaProducer

                self._producer = KafkaProducer(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda v: v.encode("utf-8"),
                    acks="all",
                    retries=3,
                    max_in_flight_requests_per_connection=1,
                )
                logger.info(f"Kafka producer connected: {bootstrap_servers}")
            except ImportError:
                logger.warning("kafka-python not installed — falling back to local mode")
                self._use_local = True

    def emit(self, event: PipelineEvent) -> None:
        """Emit an event to the appropriate topic."""
        if self._use_local:
            self._local_events.append(event)
            if self._local_queue is not None:
                self._local_queue.put(event)
            payload_id = event.payload.get("tile_id") or event.payload.get("asset_id") or "N/A"
            logger.info(f"[LOCAL EVENT] {event.topic}: {event.event_id} — {payload_id}")
        else:
            if self._producer is not None:
                self._producer.send(event.topic, value=event.to_json())
                self._producer.flush()
                logger.info(f"[KAFKA EVENT] {event.topic}: {event.event_id}")
            else:
                logger.error("Kafka producer is None but use_local is False")

    def emit_tile_ingested(self, tile_id: str, source: str, metadata: dict[str, Any]) -> None:
        """Convenience: emit NEW_TILE event."""
        event = PipelineEvent.create(
            topic=EventTopic.RAW_TILE_NEW,
            source=source,
            payload={"tile_id": tile_id, "metadata": metadata},
        )
        self.emit(event)

    def emit_tile_rejected(self, tile_id: str, source: str, reason: str) -> None:
        """Convenience: emit REJECTED event."""
        event = PipelineEvent.create(
            topic=EventTopic.RAW_TILE_REJECTED,
            source=source,
            payload={"tile_id": tile_id, "reason": reason},
        )
        self.emit(event)

    def emit_tile_processed(self, tile_id: str, output_chips: list[str], version: str) -> None:
        """Convenience: emit PROCESSED event."""
        event = PipelineEvent.create(
            topic=EventTopic.PROCESSED_TILE,
            source="preprocessor",
            payload={
                "tile_id": tile_id,
                "output_chips": output_chips,
                "preprocessing_version": version,
            },
        )
        self.emit(event)

    def emit_signal_scored(
        self, asset_id: str, signal_value: float, confidence: float, model_version: str
    ) -> None:
        """Convenience: emit SIGNAL_SCORED event."""
        event = PipelineEvent.create(
            topic=EventTopic.SIGNAL_SCORED,
            source="signal_scorer",
            payload={
                "asset_id": asset_id,
                "signal_value": signal_value,
                "confidence": confidence,
                "model_version": model_version,
            },
        )
        self.emit(event)

    def emit_risk_alert(self, alert_type: str, severity: str, details: str) -> None:
        """Convenience: emit risk alert."""
        event = PipelineEvent.create(
            topic=EventTopic.RISK_ALERT,
            source="risk_engine",
            payload={
                "alert_type": alert_type,
                "severity": severity,
                "details": details,
            },
        )
        self.emit(event)

    def get_local_events(self, topic: str | None = None) -> list[PipelineEvent]:
        """Get locally stored events (dev mode only)."""
        if topic:
            return [e for e in self._local_events if e.topic == topic]
        return list(self._local_events)

    def get_event_stream(self) -> Iterator[PipelineEvent]:
        """Generator that yields events as they arrive, blocking if empty. (Local Dev Only)"""
        if not self._use_local or self._local_queue is None:
            raise NotImplementedError("Stream only implemented for local Thread queue mode")

        def _stream() -> Iterator[PipelineEvent]:
            if self._local_queue is None:
                return
            while True:
                event = self._local_queue.get()
                if event is None:  # poison pill
                    break
                yield event

        return _stream()

    def close(self) -> None:
        """Close the Kafka producer."""
        if self._producer:
            self._producer.close()
