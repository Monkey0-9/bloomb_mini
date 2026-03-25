"""
SatTrade Alert Engine — Real-time satellite + market alerts via WebSocket.
Alert types Bloomberg can't offer: THERMAL_THRESHOLD, DARK_VESSEL_GEO, etc.
Evaluates events against user subscriptions. 30-min deduplication.
Delivery: WebSocket broadcast (100% free, no third-party email service).
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import structlog

log = structlog.get_logger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


@dataclass
class FiredAlert:
    id: str
    user_id: str
    alert_type: str
    headline: str
    message: str
    data: dict
    timestamp_utc: float


class AlertEngine:
    """Evaluates events against rules and dispatches alerts."""

    ALERT_TYPES = [
        "PRICE_LEVEL", "VOLUME_SPIKE", "COMPOSITE_SCORE",
        "THERMAL_THRESHOLD", "DARK_VESSEL_GEO", "DARK_VESSEL_COMMODITY",
        "MACRO_DIVERGENCE", "TFT_DIRECTION_FLIP", "SAR_CONFIRMATION"
    ]

    def __init__(self) -> None:
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
            except Exception as exc:
                log.warning("alert_engine_redis_failed", error=str(exc))
        return self._redis

    async def _get_active_rules(self, event_type: str) -> List[dict]:
        """Fetch active user alert rules from DB/Redis."""
        # In production this queries PostgreSQL user_alerts table where type=event_type
        # For demonstration, we'll return a mock rule list
        return []

    async def evaluate(self, event_type: str, event_data: dict) -> List[FiredAlert]:
        """
        Evaluate an incoming event against all user rules for that type.
        Returns list of newly fired alerts.
        """
        rules = await self._get_active_rules(event_type)
        fired: List[FiredAlert] = []

        for rule in rules:
            if self._matches(rule, event_data):
                alert_id = str(uuid.uuid4())
                user_id = rule.get("user_id", "")
                dedupe_key = f"alert_dedupe:{user_id}:{rule.get('id')}"

                # 30-min deduplication cooldown
                r = await self._get_redis()
                if r:
                    try:
                        exists = await r.exists(dedupe_key)
                        if exists:
                            continue
                        await r.setex(dedupe_key, 1800, "1")
                    except Exception:
                        pass

                alert = FiredAlert(
                    id=alert_id,
                    user_id=user_id,
                    alert_type=event_type,
                    headline=self._format_headline(rule, event_data),
                    message=self._format_message(rule, event_data),
                    data=event_data,
                    timestamp_utc=time.time(),
                )
                fired.append(alert)

        # Dispatch
        if fired:
            await self._dispatch(fired)

        return fired

    def _matches(self, rule: dict, event: dict) -> bool:
        """Evaluate rule criteria against event data."""
        params = rule.get("params", {})
        alert_type = rule.get("type", "")

        if alert_type == "THERMAL_THRESHOLD":
            if event.get("frp_mw", 0) < params.get("min_frp_mw", 0):
                return False
            if params.get("region") and event.get("region") != params.get("region"):
                return False
            return True
            
        elif alert_type == "DARK_VESSEL_COMMODITY":
            if event.get("cargo_commodity") != params.get("commodity"):
                return False
            if event.get("count", 0) < params.get("min_count", 0):
                return False
            if event.get("chokepoint") != params.get("chokepoint"):
                return False
            return True

        elif alert_type == "MACRO_DIVERGENCE":
            return event.get("signal_z", 0) > 1.5 and event.get("macro_z", 0) < 0.5

        elif alert_type == "COMPOSITE_SCORE":
            if event.get("ticker") != params.get("ticker"):
                return False
            direction = params.get("direction", "ABOVE")
            threshold = params.get("threshold", 0.0)
            score = event.get("composite_score", 0.0)
            if direction == "ABOVE" and score >= threshold:
                return True
            if direction == "BELOW" and score <= threshold:
                return True
            return False

        elif alert_type == "TFT_DIRECTION_FLIP":
            return event.get("ticker") == params.get("ticker")

        return False

    def _format_headline(self, rule: dict, event: dict) -> str:
        t = rule.get("type", "")
        if t == "THERMAL_THRESHOLD":
            return f"Thermal Anomaly: {event.get('frp_mw', 0)} MW at {event.get('region', 'Unknown')}"
        if t == "DARK_VESSEL_COMMODITY":
            return f"{event.get('count')} Dark {event.get('cargo_commodity').title()} Vessels at {event.get('chokepoint').title()}"
        if t == "COMPOSITE_SCORE":
            return f"Alpha Alert: {event.get('ticker')} cross {rule.get('params', {}).get('threshold')}"
        return f"Alert: {t}"

    def _format_message(self, rule: dict, event: dict) -> str:
        return json.dumps(event)

    async def _dispatch(self, alerts: list[FiredAlert]) -> None:
        """Dispatch via WebSocket broadcast (Redis pub/sub channel)."""
        r = await self._get_redis()
        if r:
            try:
                for a in alerts:
                    await r.publish("alerts", json.dumps(asdict(a)))
                log.info("alerts_dispatched_ws", count=len(alerts))
            except Exception as exc:
                log.error("alert_ws_dispatch_failed", error=str(exc))
