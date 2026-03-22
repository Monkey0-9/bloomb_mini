import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import structlog
from src.common.schemas import FeatureRecord

log = structlog.get_logger()

# Constants
HOLDOUT_START_DATE = datetime(2023, 10, 1, tzinfo=timezone.utc)

class FeatureStoreError(Exception):
    """Base class for feature store exceptions."""
    pass

class DuplicateFeatureError(FeatureStoreError):
    """Raised when a duplicate feature_id is written."""
    pass

class FeatureLeakError(FeatureStoreError):
    """Raised when future data is detected in a past query context."""
    pass

class HoldoutAccessError(FeatureStoreError):
    """Raised when holdout data is accessed during training/backtesting."""
    pass

class FeatureStore:
    """
    Institutional-grade Feature Store with point-in-time correctness.
    Prevents look-ahead bias and ensures data lineage.
    """
    def __init__(self, db_path: str = ":memory:", is_holdout: bool = False):
        self.db_path = db_path
        self._records: Dict[str, FeatureRecord] = {}
        self._entity_map: Dict[str, List[str]] = {}
        self.is_holdout = is_holdout

    def write(self, record: FeatureRecord):
        """Atomically write a feature record to the store."""
        if record.feature_id in self._records:
            raise DuplicateFeatureError(f"Feature ID {record.feature_id} already exists.")
        
        self._records[record.feature_id] = record
        if record.entity_id not in self._entity_map:
            self._entity_map[record.entity_id] = []
        self._entity_map[record.entity_id].append(record.feature_id)
        
        log.info("feature_written", 
                 feature_id=record.feature_id, 
                 entity_id=record.entity_id,
                 feature_name=record.feature_name)

    def get_features_as_of(self, entity_id: str, at_timestamp: datetime, feature_names: List[str] = None) -> List[FeatureRecord]:
        """
        Retrieve the latest features for an entity as of a specific point in time.
        Strictly prevents look-ahead bias by filtering on created_timestamp.
        """
        # Ensure at_timestamp is timezone-aware if needed for comparison
        if at_timestamp.tzinfo is None:
            at_timestamp = at_timestamp.replace(tzinfo=timezone.utc)

        # Check holdout access
        if not self.is_holdout and at_timestamp >= HOLDOUT_START_DATE:
            raise HoldoutAccessError("Accessing holdout data (post-2023-10-01) is restricted during this mode.")

        if entity_id not in self._entity_map:
            return []

        relevant_ids = self._entity_map[entity_id]
        results = []
        
        # In a real DB, this would be a window function or a subquery
        # Here we simulate point-in-time logic:
        # 1. Must be created before or at at_timestamp (Prevents look-ahead)
        # 2. Latest event_timestamp for each feature_name
        
        latest_features: Dict[str, FeatureRecord] = {}
        
        for fid in relevant_ids:
            record = self._records[fid]
            
            # Ensure record timestamps are aware
            rec_created = record.created_timestamp
            if rec_created.tzinfo is None:
                rec_created = rec_created.replace(tzinfo=timezone.utc)
            
            # Point-in-time check: was this data KNOWN at at_timestamp?
            if rec_created <= at_timestamp:
                if feature_names and record.feature_name not in feature_names:
                    continue
                
                # Update with the most recent event date seen SO FAR
                existing = latest_features.get(record.feature_name)
                if not existing or record.event_timestamp > existing.event_timestamp:
                    latest_features[record.feature_name] = record

        return list(latest_features.values())

    # Compatibility methods for simpler use cases
    def set_features(self, entity_id: str, features: Dict[str, Any]):
        """Legacy-compatible setter."""
        for name, val in features.items():
            record = FeatureRecord(
                entity_id=entity_id,
                feature_name=name,
                feature_value=float(val),
                event_timestamp=datetime.now(timezone.utc),
                created_timestamp=datetime.now(timezone.utc)
            )
            self.write(record)

    def get_features(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Legacy-compatible getter (gets latest as of NOW)."""
        recs = self.get_features_as_of(entity_id, datetime.now(timezone.utc))
        if not recs:
            return None
        return {r.feature_name: r.feature_value for r in recs}

# Singleton instance for simple global access
feature_store = FeatureStore()
