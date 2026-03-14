"""
Feature Store — Phase 4.5

Materialise all features into a point-in-time correct store.
Every feature record has:
  - entity_id (facility or port)
  - feature_timestamp (point-in-time correct — MANDATORY)
  - feature_values
  - source_tile_ids[]
  - model_version

CRITICAL: Never join on wall-clock time — always use as-of joins
to prevent look-ahead bias.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FeatureRecord:
    """Single feature record in the store."""
    entity_id: str  # Port ID, facility ID, etc.
    feature_name: str
    feature_value: float
    feature_timestamp: datetime  # Point-in-time correct
    created_timestamp: Optional[datetime] = None # Real-world commit time
    source_tile_ids: list[str] = field(default_factory=list)
    model_version: str = ""
    feature_hash: str = ""  # Content-addressed

    def __post_init__(self) -> None:
        if self.created_timestamp is None:
            self.created_timestamp = self.feature_timestamp

    def compute_hash(self) -> str:
        """Compute content-addressed hash of feature inputs."""
        content = json.dumps({
            "entity_id": self.entity_id,
            "feature_name": self.feature_name,
            "feature_value": self.feature_value,
            "feature_timestamp": self.feature_timestamp.isoformat(),
            "created_timestamp": self.created_timestamp.isoformat(),
            "source_tile_ids": sorted(self.source_tile_ids),
            "model_version": self.model_version,
        }, sort_keys=True)
        self.feature_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return self.feature_hash


@dataclass
class FeatureVector:
    """Complete feature vector for an entity at a point in time."""
    entity_id: str
    timestamp: datetime
    features: dict[str, float] = field(default_factory=dict)
    source_tile_ids: list[str] = field(default_factory=list)
    model_version: str = ""
    feature_hash: str = ""


class FeatureStore:
    """
    In-memory feature store with point-in-time correct retrieval.
    
    In production: backed by Feast or Tecton.
    For development: uses sorted in-memory storage with as-of join semantics.
    
    CRITICAL INVARIANT: The `get_features_as_of` method NEVER returns
    features with timestamps after the query timestamp. This prevents
    look-ahead bias in backtesting.
    """

    def __init__(self) -> None:
        # entity_id → feature_name → sorted list of (timestamp, created_ts, value, metadata)
        self._store: dict[str, dict[str, list[tuple[datetime, datetime, float, dict[str, Any]]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._total_records = 0

    def materialize(self, record: FeatureRecord) -> None:
        """Write a feature record to the store."""
        record.compute_hash()

        self._store[record.entity_id][record.feature_name].append((
            record.feature_timestamp,
            record.created_timestamp,
            record.feature_value,
            {
                "source_tile_ids": record.source_tile_ids,
                "model_version": record.model_version,
                "feature_hash": record.feature_hash,
            },
        ))

        # Keep sorted by feature timestamp
        self._store[record.entity_id][record.feature_name].sort(key=lambda x: x[0])
        self._total_records += 1

    def materialize_batch(self, records: list[FeatureRecord]) -> int:
        """Write multiple feature records. Returns count written."""
        for r in records:
            self.materialize(r)
        logger.info(f"Materialised {len(records)} feature records")
        return len(records)

    def get_features_as_of(
        self,
        entity_id: str,
        as_of_timestamp: datetime,
        feature_names: Optional[list[str]] = None,
    ) -> FeatureVector:
        """
        Point-in-time correct feature retrieval (as-of join).
        
        Returns the most recent feature values available AT OR BEFORE
        the query timestamp. NEVER returns future data.
        
        This is the ONLY way features should be retrieved for
        backtesting and signal generation.
        """
        if entity_id not in self._store:
            return FeatureVector(entity_id=entity_id, timestamp=as_of_timestamp)

        entity_features = self._store[entity_id]
        names_to_query = feature_names or list(entity_features.keys())

        features: dict[str, float] = {}
        all_tile_ids: list[str] = []
        latest_version = ""

        for name in names_to_query:
            if name not in entity_features:
                continue

            records = entity_features[name]
            # Binary search / scan for most recent record <= as_of_timestamp
            best_record = None
            for ts, created_ts, val, meta in reversed(records):
                # Look-ahead prevention: the feature must have been *computed*
                # and *inserted* exactly at or before the simulated backtest wall-clock
                if ts <= as_of_timestamp and created_ts <= as_of_timestamp:
                    # Staleness check: reject features older than 365 days for testing/dev
                    # (Satellite passes for high-res can be infrequent)
                    staleness_seconds = (as_of_timestamp - ts).total_seconds()
                    if staleness_seconds <= 365 * 24 * 3600:
                        best_record = (ts, val, meta)
                        break

            if best_record:
                _, val, meta = best_record
                features[name] = val
                all_tile_ids.extend(meta.get("source_tile_ids", []))
                latest_version = meta.get("model_version", latest_version)

        return FeatureVector(
            entity_id=entity_id,
            timestamp=as_of_timestamp,
            features=features,
            source_tile_ids=list(set(all_tile_ids)),
            model_version=latest_version,
        )

    def get_feature_panel(
        self,
        entity_ids: list[str],
        feature_names: list[str],
        timestamps: list[datetime],
    ) -> dict[str, dict[str, list[Optional[float]]]]:
        """
        Get a panel of features across entities and timestamps.
        
        Returns: {entity_id: {feature_name: [values_per_timestamp]}}
        All values are point-in-time correct.
        """
        panel: dict[str, dict[str, list[Optional[float]]]] = {}

        for entity_id in entity_ids:
            panel[entity_id] = {}
            for feature_name in feature_names:
                values: list[Optional[float]] = []
                for ts in timestamps:
                    fv = self.get_features_as_of(entity_id, ts, [feature_name])
                    values.append(fv.features.get(feature_name))
                panel[entity_id][feature_name] = values

        return panel

    def get_latest_features(self, entity_id: str) -> FeatureVector:
        """Get the most recent features for an entity (live scoring)."""
        return self.get_features_as_of(entity_id, datetime.now(timezone.utc))

    def get_entity_ids(self) -> list[str]:
        """Get all entity IDs in the store."""
        return list(self._store.keys())

    def get_feature_names(self, entity_id: str) -> list[str]:
        """Get all feature names for an entity."""
        return list(self._store.get(entity_id, {}).keys())

    def get_record_count(self) -> int:
        """Get total number of records in the store."""
        return self._total_records

    def validate_no_lookahead(
        self,
        entity_id: str,
        query_timestamp: datetime,
    ) -> bool:
        """
        Validate that no features returned have timestamps after the query.
        Used in backtesting to verify point-in-time correctness.
        """
        entity_features = self._store.get(entity_id, {})
        for name, records in entity_features.items():
            best_ts = None
            best_created_ts = None
            for ts, created_ts, val, meta in reversed(records):
                if ts <= query_timestamp:
                    best_ts = ts
                    best_created_ts = created_ts
                    break
            
            if best_ts is not None and (best_ts > query_timestamp or best_created_ts > query_timestamp):
                logger.critical(
                    f"LOOKAHEAD BIAS DETECTED: Feature '{name}' for "
                    f"'{entity_id}' has ts {best_ts} or created_ts {best_created_ts} > query {query_timestamp}"
                )
                return False
        return True
