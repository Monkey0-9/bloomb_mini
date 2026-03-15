"""
Point-in-time correct feature store.
THE CARDINAL RULE: get_features_as_of(entity, T) NEVER returns a feature
whose created_timestamp > T. Violating this rule invalidates every backtest
result in the entire system.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from src.common.schemas import FeatureRecord


class FeatureLeakError(Exception):
    """Raised when look-ahead bias is detected. NEVER catch and continue."""


class DuplicateFeatureError(Exception):
    """Raised when inserting a duplicate feature_id."""


class HoldoutAccessError(Exception):
    """Raised when training code attempts to access holdout data."""


HOLDOUT_START_DATE = datetime(2023, 7, 1, 0, 0, 0)


class FeatureStore:
    def __init__(self, db_path: str = "data/features.db",
                 is_holdout: bool = False) -> None:
        self.db_path = db_path
        self.is_holdout = is_holdout
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS features (
                    feature_id        TEXT PRIMARY KEY,
                    entity_id         TEXT NOT NULL,
                    feature_name      TEXT NOT NULL,
                    feature_value     REAL NOT NULL,
                    event_timestamp   TEXT NOT NULL,
                    created_timestamp TEXT NOT NULL,
                    source_tile_id    TEXT NOT NULL,
                    model_version     TEXT NOT NULL DEFAULT '1.0.0'
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_entity_created "
                "ON features(entity_id, created_timestamp)"
            )
            conn.commit()

    def write(self, record: FeatureRecord) -> None:
        if record.created_timestamp < record.event_timestamp:
            raise ValueError(
                f"created_timestamp {record.created_timestamp} cannot be before "
                f"event_timestamp {record.event_timestamp}. "
                "A feature cannot be available before the event that produced it."
            )
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT feature_id FROM features WHERE feature_id = ?",
                (record.feature_id,)
            ).fetchone()
            if existing:
                raise DuplicateFeatureError(
                    f"feature_id {record.feature_id} already exists"
                )
            conn.execute(
                "INSERT INTO features VALUES (?,?,?,?,?,?,?,?)",
                (
                    record.feature_id, record.entity_id, record.feature_name,
                    record.feature_value,
                    record.event_timestamp.isoformat(),
                    record.created_timestamp.isoformat(),
                    record.source_tile_id, record.model_version,
                ),
            )
            conn.commit()

    def get_features_as_of(
        self,
        entity_id: str,
        as_of: datetime,
        feature_names: list[str] | None = None,
    ) -> list[FeatureRecord]:
        # HOLDOUT PROTECTION: training code must never access holdout period
        if not self.is_holdout and as_of >= HOLDOUT_START_DATE:
            raise HoldoutAccessError(
                f"as_of={as_of} is in the holdout period (>= {HOLDOUT_START_DATE}). "
                "Training and backtesting code must not access holdout data. "
                "Use the holdout FeatureStore only for final evaluation."
            )

        with sqlite3.connect(self.db_path) as conn:
            query = (
                "SELECT feature_id, entity_id, feature_name, feature_value, "
                "event_timestamp, created_timestamp, source_tile_id, model_version "
                "FROM features "
                "WHERE entity_id = ? AND created_timestamp <= ?"
            )
            params: list = [entity_id, as_of.isoformat()]
            if feature_names:
                placeholders = ",".join("?" * len(feature_names))
                query += f" AND feature_name IN ({placeholders})"
                params.extend(feature_names)
            rows = conn.execute(query, params).fetchall()

        results = []
        for row in rows:
            r = FeatureRecord(
                feature_id=row[0], entity_id=row[1], feature_name=row[2],
                feature_value=row[3],
                event_timestamp=datetime.fromisoformat(row[4]),
                created_timestamp=datetime.fromisoformat(row[5]),
                source_tile_id=row[6], model_version=row[7],
            )
            # Double-check: this should never fire if SQL is correct
            if r.created_timestamp > as_of:
                raise FeatureLeakError(
                    f"LOOK-AHEAD BIAS DETECTED: feature {r.feature_id} "
                    f"created at {r.created_timestamp} returned for "
                    f"as_of={as_of}. This is a critical bug."
                )
            results.append(r)
        return results
