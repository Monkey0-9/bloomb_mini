"""
Signal Ensemble — Phase 5.4

Combine outputs from IC analysis, linear model, GBM, and TFT
into a single ensemble prediction per asset.

Weighting: inverse validation RMSE, constrained to sum to 1.
Quarterly reweighting on expanding validation window.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

from src.signals.price_impact import LinearModel, GBMModel, EnsembleModel

logger = logging.getLogger(__name__)


@dataclass
class EnsemblePrediction:
    """Final ensemble prediction for an asset."""
    entity_id: str
    ensemble_value: float
    component_values: dict[str, float]
    component_weights: dict[str, float]
    confidence: float  # Weighted average of component confidences
    prediction_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    model_versions: dict[str, str] = field(default_factory=dict)
    shap_attributions: Optional[dict[str, float]] = None


class SignalEnsemble:
    """
    Production ensemble combiner for signal models.
    
    Combines predictions from:
    1. Linear (OLS/WLS)
    2. GBM (LightGBM)
    3. TFT (Temporal Fusion Transformer) — optional, data-dependent
    
    Weight allocation: inverse RMSE on validation set.
    """

    def __init__(self) -> None:
        self._component_weights: dict[str, float] = {}
        self._component_rmses: dict[str, float] = {}
        self._reweight_history: list[dict[str, Any]] = []

    def set_weights_from_validation(
        self,
        component_rmses: dict[str, float],
    ) -> dict[str, float]:
        """
        Compute ensemble weights from validation RMSEs.
        
        Uses inverse RMSE weighting: lower RMSE → higher weight.
        """
        self._component_rmses = component_rmses

        # Inverse RMSE
        inverse_rmse = {}
        for name, rmse in component_rmses.items():
            if rmse > 0:
                inverse_rmse[name] = 1.0 / rmse
            else:
                inverse_rmse[name] = 0.0

        total_inv = sum(inverse_rmse.values())
        if total_inv > 0:
            self._component_weights = {
                name: inv / total_inv for name, inv in inverse_rmse.items()
            }
        else:
            # Equal weight fallback
            n = len(component_rmses)
            self._component_weights = {name: 1.0 / n for name in component_rmses}

        self._reweight_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rmses": component_rmses,
            "weights": self._component_weights.copy(),
        })

        logger.info(f"Ensemble weights updated: {self._component_weights}")
        return self._component_weights

    def combine(
        self,
        entity_id: str,
        component_predictions: dict[str, float],
        component_confidences: Optional[dict[str, float]] = None,
    ) -> EnsemblePrediction:
        """
        Combine component predictions into ensemble output.
        """
        if not self._component_weights:
            # Equal weight if no validation has been done
            n = len(component_predictions)
            weights = {name: 1.0 / n for name in component_predictions}
        else:
            weights = self._component_weights

        # Weighted average
        ensemble_value = sum(
            weights.get(name, 0) * pred
            for name, pred in component_predictions.items()
        )

        # Weighted confidence
        confidences = component_confidences or {name: 1.0 for name in component_predictions}
        ensemble_confidence = sum(
            weights.get(name, 0) * confidences.get(name, 1.0)
            for name in component_predictions
        )

        return EnsemblePrediction(
            entity_id=entity_id,
            ensemble_value=ensemble_value,
            component_values=component_predictions,
            component_weights=weights,
            confidence=min(ensemble_confidence, 1.0),
        )

    def quarterly_reweight(
        self,
        X_val: np.ndarray,
        y_val: np.ndarray,
        component_models: dict[str, Any],
    ) -> dict[str, float]:
        """
        Quarterly reweighting on expanding validation window.
        
        Spec requirement: retrain on expanding window, never shrink.
        """
        rmses = {}
        for name, model in component_models.items():
            try:
                y_pred = model.predict(X_val)
                rmse = float(np.sqrt(np.mean((y_val - y_pred) ** 2)))
                rmses[name] = rmse
            except Exception as e:
                logger.warning(f"Model '{name}' prediction failed: {e}")
                rmses[name] = float("inf")

        return self.set_weights_from_validation(rmses)

    def get_weight_history(self) -> list[dict[str, Any]]:
        """Return full history of weight changes for audit."""
        return self._reweight_history
