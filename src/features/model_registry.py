from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog

log = structlog.get_logger()

@dataclass
class ModelVersion:
    version: str
    trained_at: datetime
    metrics: dict[str, float]
    parameters: dict[str, Any]
    is_live: bool = False

class ModelRegistry:
    """
    Tracks different versions of ML models and their performance metrics.
    """
    def __init__(self):
        self._models: dict[str, list[ModelVersion]] = {}

    def register_version(self, model_name: str, version: ModelVersion):
        if model_name not in self._models:
            self._models[model_name] = []
        self._models[model_name].append(version)
        log.info("model_registered", model=model_name, version=version.version)

    def get_latest_version(self, model_name: str) -> ModelVersion:
        return self._models[model_name][-1]

# Singleton instance
model_registry = ModelRegistry()
