"""
Lineage tracking module for recursive feature validation.
Ensures point-in-time correctness, trace validation, and multi-tier lineage graphing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LineageNode:
    """A single tracking node for a feature or raw input over time."""

    feature_name: str
    feature_hash: str
    model_version: str
    dependencies: list[LineageNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert tree to dictionary recursively."""
        return {
            "feature_name": self.feature_name,
            "feature_hash": self.feature_hash,
            "model_version": self.model_version,
            "dependencies": [d.to_dict() for d in self.dependencies],
        }


class LineageTracker:
    """Tracks recursively built features out of raw data to guarantee reproducibility."""

    def __init__(self) -> None:
        self._nodes: dict[tuple[str, str], LineageNode] = {}

    def register_node(self, node: LineageNode) -> None:
        """Register a new traced node manually."""
        key = (node.feature_name, node.feature_hash)
        if key not in self._nodes:
            self._nodes[key] = node

    def get_lineage_graph(self, feature_name: str, feature_hash: str) -> dict[str, Any]:
        """Generate a complete recursive tree of a feature's sub-components."""
        key = (feature_name, feature_hash)
        node = self._nodes.get(key)
        if not node:
            return {
                "feature_name": feature_name,
                "feature_hash": feature_hash,
                "error": "Node not found in lineage tracker.",
            }

        return node.to_dict()

    def validate_dependencies_exist(self, node: LineageNode) -> bool:
        """Trace a node and make sure all its listed dependencies exist down to roots."""
        for dep in node.dependencies:
            key = (dep.feature_name, dep.feature_hash)
            if key not in self._nodes:
                return False
            if not self.validate_dependencies_exist(dep):
                return False
        return True
