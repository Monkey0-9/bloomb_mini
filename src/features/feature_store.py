import time
from typing import Any, Dict, List, Optional
import structlog

log = structlog.get_logger()

class FeatureStore:
    """
    Manages and serves features for ML models and risk engines.
    Initial implementation: In-memory with TTL.
    """
    def __init__(self):
        self._features: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}

    def set_features(self, entity_id: str, features: Dict[str, Any]):
        self._features[entity_id] = features
        self._timestamps[entity_id] = time.time()
        log.info("features_updated", entity_id=entity_id, feature_count=len(features))

    def get_features(self, entity_id: str) -> Optional[Dict[str, Any]]:
        return self._features.get(entity_id)

    def get_all_features(self) -> Dict[str, Dict[str, Any]]:
        return self._features

# Singleton instance
feature_store = FeatureStore()
