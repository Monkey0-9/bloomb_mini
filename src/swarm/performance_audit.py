"""
Swarm Performance Audit - Autonomous Self-Optimization.

Tracks the predictive accuracy of individual agents and personas 
to dynamically re-weight their contribution to the GTFI.
"""
import logging
import json
import os
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

class SwarmAuditor:
    def __init__(self, audit_file: str = "data/cache/swarm_audit.json"):
        self.audit_file = audit_file
        self.performance_data = self._load_audit()

    def _load_audit(self) -> dict[str, Any]:
        if os.path.exists(self.audit_file):
            try:
                with open(self.audit_file) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_audit(self):
        os.makedirs(os.path.dirname(self.audit_file), exist_ok=True)
        with open(self.audit_file, 'w') as f:
            json.dump(self.performance_data, f)

    def record_prediction(self, ticker: str, prediction: dict[str, Any], actual_price_change: float):
        """
        Records the accuracy of a prediction and updates agent/persona scores.
        """
        # Logic to correlate prediction action (BULLISH/BEARISH) with actual move
        is_correct = (prediction['action'] == "BULLISH" and actual_price_change > 0) or \
                     (prediction['action'] == "BEARISH" and actual_price_change < 0)
        
        persona = prediction.get('persona', 'Standard')
        
        if persona not in self.performance_data:
            self.performance_data[persona] = {"correct": 0, "total": 0, "win_rate": 0.0}
            
        self.performance_data[persona]["total"] += 1
        if is_correct:
            self.performance_data[persona]["correct"] += 1
            
        self.performance_data[persona]["win_rate"] = self.performance_data[persona]["correct"] / self.performance_data[persona]["total"]
        
        self._save_audit()
        logger.info(f"Recorded prediction for {ticker}: {is_correct} (Win Rate: {self.performance_data[persona]['win_rate']:.2f})")

    def get_persona_weights(self) -> dict[str, float]:
        """
        Returns persona weights normalized by performance.
        """
        weights = {}
        total_win_rate = sum(p.get("win_rate", 0.5) for p in self.performance_data.values())
        
        if total_win_rate == 0:
            return {p: 1.0/len(self.performance_data) for p in self.performance_data} if self.performance_data else {"Standard": 1.0}
            
        for persona, data in self.performance_data.items():
            weights[persona] = data.get("win_rate", 0.5) / total_win_rate
            
        return weights

# Singleton
_auditor: SwarmAuditor | None = None

def get_swarm_auditor() -> SwarmAuditor:
    global _auditor
    if _auditor is None:
        _auditor = SwarmAuditor()
    return _auditor
