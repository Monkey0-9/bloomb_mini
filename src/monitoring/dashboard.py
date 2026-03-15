"""
Signal Health Dashboard Metrics — Phase 8.1

Prometheus metrics for Grafana dashboards.
Exposes all metrics required by the spec:
  - Live IC (rolling 63-day):
  - Data coverage map
  - Model confidence distribution
  - Pipeline latency (P50/P95/P99)
  - Signal-to-noise ratio

And drift detection:
  - Monthly PSI on all features
  - PSI > 0.2 → full retrain
  - PSI 0.1-0.2 → fine-tuning flag
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import numpy as np
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# ─── Prometheus Metrics ────────────────────────────────────────────────────────

# Signal quality
SIGNAL_IC = Gauge(
    "sattrade_signal_ic_rolling_63d",
    "Rolling 63-day Information Coefficient",
    ["signal_name"],
)

IC_HISTORICAL_P10 = Gauge(
    "sattrade_signal_ic_historical_p10",
    "Historical 10th percentile IC (alert threshold)",
    ["signal_name"],
)

IC_BELOW_P10_CONSECUTIVE_DAYS = Gauge(
    "sattrade_signal_ic_below_p10_days",
    "Consecutive days IC is below historical 10th percentile",
    ["signal_name"],
)

# Data coverage
DATA_COVERAGE_PCT = Gauge(
    "sattrade_data_coverage_pct",
    "% of target facilities imaged in past 7 days",
    ["region"],
)

# Pipeline
PIPELINE_LATENCY = Histogram(
    "sattrade_pipeline_latency_seconds",
    "Pipeline stage latency",
    ["stage"],
    buckets=[60, 300, 600, 1800, 3600, 7200, 14400, 21600],  # Up to 6h
)

PIPELINE_SLA_BREACH = Counter(
    "sattrade_pipeline_sla_breach_total",
    "Number of SLA breaches (P95 > 6h)",
    ["stage"],
)

SLA_COVERAGE_DROP_ALERT = Counter(
    "sattrade_sla_coverage_drop_alert_total",
    "Number of SLA alerts for >60% coverage drops in 7-day windows",
    ["region"],
)

# Model confidence
MODEL_CONFIDENCE_MEAN = Gauge(
    "sattrade_model_confidence_mean",
    "Mean model confidence across predictions",
    ["model_version"],
)

# Tiles processed
TILES_PROCESSED = Counter(
    "sattrade_tiles_processed_total",
    "Total tiles processed",
    ["source", "status"],
)

FEATURE_PSI = Gauge(
    "sattrade_feature_psi",
    "Population Stability Index for feature drift",
    ["feature_name"],
)

# SNR and Licensing
SIGNAL_SNR = Gauge(
    "sattrade_signal_snr",
    "Signal-to-Noise Ratio (Mean / Std)",
    ["signal_name"],
)

LICENSE_EXPIRY_DAYS = Gauge(
    "sattrade_data_license_expiry_days",
    "Days until data license expires",
    ["license_id"],
)


@dataclass
class ICTracker:
    """Track rolling Information Coefficient for a signal."""

    signal_name: str
    window_days: int = 63
    alert_threshold_consecutive: int = 10
    _values: deque = field(default_factory=lambda: deque(maxlen=252))
    _below_p10_count: int = 0

    def update(self, ic_value: float) -> dict[str, Any]:
        """Update IC with new value and check alert conditions."""
        self._values.append(ic_value)

        if len(self._values) < self.window_days:
            return {"status": "warming_up", "values": len(self._values)}

        recent = list(self._values)[-self.window_days :]
        rolling_ic = float(np.mean(recent))
        historical_p10 = float(np.percentile(list(self._values), 10))

        # Update Prometheus
        SIGNAL_IC.labels(signal_name=self.signal_name).set(rolling_ic)
        IC_HISTORICAL_P10.labels(signal_name=self.signal_name).set(historical_p10)

        # Alert check
        if rolling_ic < historical_p10:
            self._below_p10_count += 1
        else:
            self._below_p10_count = 0

        IC_BELOW_P10_CONSECUTIVE_DAYS.labels(signal_name=self.signal_name).set(
            self._below_p10_count
        )

        alert = None
        if self._below_p10_count >= self.alert_threshold_consecutive:
            alert = (
                f"IC ALERT: {self.signal_name} has been below historical 10th "
                f"percentile for {self._below_p10_count} consecutive days. "
                f"Current IC={rolling_ic:.4f}, threshold={historical_p10:.4f}"
            )
            logger.warning(alert)

        return {
            "rolling_ic": rolling_ic,
            "historical_p10": historical_p10,
            "below_p10_days": self._below_p10_count,
            "alert": alert,
        }


class DriftDetector:
    """
    Population Stability Index (PSI) for concept drift detection.

    PSI > 0.2 → trigger full retraining review
    PSI 0.1-0.2 → flag for incremental fine-tuning
    PSI < 0.1 → stable
    """

    @staticmethod
    def compute_psi(
        reference: np.ndarray,
        current: np.ndarray,
        n_bins: int = 10,
    ) -> float:
        """
        Compute Population Stability Index between reference and current distributions.

        PSI = Σ (pᵢ - qᵢ) × ln(pᵢ / qᵢ)
        Where pᵢ = % of current in bin i, qᵢ = % of reference in bin i
        """
        # Create bins from reference distribution
        _, bin_edges = np.histogram(reference, bins=n_bins)
        ref_counts, _ = np.histogram(reference, bins=bin_edges)
        cur_counts, _ = np.histogram(current, bins=bin_edges)

        # Convert to proportions (add small epsilon to avoid log(0))
        eps = 1e-6
        ref_pct = ref_counts / len(reference) + eps
        cur_pct = cur_counts / len(current) + eps

        # Normalise
        ref_pct = ref_pct / ref_pct.sum()
        cur_pct = cur_pct / cur_pct.sum()

        # PSI
        psi = float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))
        return psi

    @staticmethod
    def classify_drift(psi: float) -> str:
        """Classify drift severity based on PSI value."""
        if psi >= 0.2:
            return "SIGNIFICANT_DRIFT"  # Full retrain
        elif psi >= 0.1:
            return "MODERATE_DRIFT"  # Fine-tuning
        else:
            return "STABLE"

    def check_all_features(
        self,
        reference_features: dict[str, np.ndarray],
        current_features: dict[str, np.ndarray],
    ) -> dict[str, dict[str, Any]]:
        """
        Monthly PSI check on all input features.
        Returns drift classification for each feature.
        """
        results = {}
        for feature_name in reference_features:
            if feature_name not in current_features:
                results[feature_name] = {
                    "psi": float("inf"),
                    "classification": "MISSING_FEATURE",
                    "action": "INVESTIGATE — feature no longer available",
                }
                continue

            psi = self.compute_psi(
                reference_features[feature_name],
                current_features[feature_name],
            )
            classification = self.classify_drift(psi)

            FEATURE_PSI.labels(feature_name=feature_name).set(psi)

            action = {
                "STABLE": "No action required",
                "MODERATE_DRIFT": "Flag for incremental fine-tuning",
                "SIGNIFICANT_DRIFT": "Trigger FULL RETRAINING review",
            }[classification]

            results[feature_name] = {
                "psi": psi,
                "classification": classification,
                "action": action,
            }

            if classification == "SIGNIFICANT_DRIFT":
                logger.warning(
                    f"DRIFT ALERT: Feature '{feature_name}' PSI={psi:.3f} (>{0.2}) — {action}"
                )

        return results


class SignalQualityMonitor:
    """Monitor signal quality metrics like SNR."""

    @staticmethod
    def update_snr(signal_name: str, signal_values: np.ndarray) -> float:
        """Compute and update SNR (Mean/Std)."""
        if signal_values.size < 2:
            return 0.0

        mean_val = np.mean(signal_values)
        std_val = np.std(signal_values)
        snr = float(mean_val / std_val) if std_val > 0 else 0.0

        SIGNAL_SNR.labels(signal_name=signal_name).set(snr)
        if snr < 0.5:
            logger.warning(f"SNR COLLAPSE: Signal {signal_name} SNR={snr:.3f} below 0.5 threshold")

        return snr


class LicenseMonitor:
    """Monitor data license expiry."""

    @staticmethod
    def check_license(license_id: str, expiry_date: datetime) -> int:
        """Calculate days to expiry and update Prometheus."""
        now = datetime.now(UTC)
        days_left = (expiry_date - now).days

        LICENSE_EXPIRY_DAYS.labels(license_id=license_id).set(days_left)

        if days_left < 30:
            logger.critical(
                f"LICENSE EXPIRY ALERT: License {license_id} expires in {days_left} days!"
            )
        elif days_left < 90:
            logger.warning(
                f"LICENSE EXPIRY WARNING: License {license_id} expires in {days_left} days"
            )

        return days_left
