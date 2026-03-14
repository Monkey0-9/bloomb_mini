"""
Economic Proxy Construction — Phase 5.1

Translate satellite-derived features into economic proxies:

Port Container Throughput Signal:
  CV features → container_count, vessel_dwell, crane_activity
  → weighted index → normalise to TEU estimate
  → compare vs consensus (analyst estimates / historical moving avg)
  → alpha = (satellite_TEU - consensus_TEU) / consensus_TEU

Retail Parking Lot Signal:
  CV features → car_count, empty_spaces
  → occupancy_rate = cars / (cars + empties)
  → relative to same-day-of-week, same-store historical
  → alpha = z-score of occupancy vs trailing 52-week same-DoW

Industrial Thermal Signal:
  Thermal features → LST anomaly z-score
  → operational intensity proxy
  → compare vs seasonal normal
  → alpha = deviation from 5-year seasonal pattern
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

from src.features.feature_store import FeatureStore, FeatureVector

logger = logging.getLogger(__name__)


@dataclass
class EconomicProxy:
    """A constructed economic proxy value."""
    entity_id: str
    proxy_name: str
    proxy_value: float
    alpha_signal: float  # satellite - consensus
    alpha_confidence: float  # 0-1
    consensus_value: Optional[float] = None
    unit: str = ""
    feature_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_features: dict[str, float] = field(default_factory=dict)


class PortThroughputProxy:
    """
    Convert port CV features into TEU (Twenty-foot Equivalent Unit) estimates.
    
    Formula:
    TEU_estimate = (
        container_count × avg_teu_per_stack +
        vessels_at_berth × avg_teu_per_vessel × berth_utilisation_factor +
        crane_activity_score × teu_per_crane_hour
    )
    
    Alpha = (satellite_TEU - consensus_TEU) / consensus_TEU
    """

    AVG_TEU_PER_STACK = 40
    AVG_TEU_PER_VESSEL = 4_000  # Panamax container ship
    TEU_PER_CRANE_HOUR = 30
    BERTH_UTILISATION_FACTOR = 0.75

    def __init__(self, feature_store: FeatureStore) -> None:
        self._store = feature_store
        self._consensus_cache: dict[str, list[float]] = {}

    def compute(
        self,
        entity_id: str,
        feature_vector: FeatureVector,
        consensus_teu: Optional[float] = None,
    ) -> EconomicProxy:
        """Compute TEU estimate and alpha signal for a port."""
        features = feature_vector.features

        container_count = features.get("container_count", 0)
        vessels_at_berth = features.get("vessels_at_berth", 0)
        crane_activity = features.get("crane_activity_score", 0)
        port_utilisation = features.get("port_utilisation_rate", 0)

        # TEU estimate
        teu_from_containers = container_count * self.AVG_TEU_PER_STACK
        teu_from_vessels = (
            vessels_at_berth
            * self.AVG_TEU_PER_VESSEL
            * self.BERTH_UTILISATION_FACTOR
            * port_utilisation
        )
        teu_from_cranes = crane_activity * self.TEU_PER_CRANE_HOUR * 24

        satellite_teu = teu_from_containers + teu_from_vessels + teu_from_cranes

        # Consensus: use provided value or historical rolling average
        if consensus_teu is None:
            consensus_teu = self._get_consensus(entity_id)

        # Alpha signal
        if consensus_teu and consensus_teu > 0:
            alpha = (satellite_teu - consensus_teu) / consensus_teu
        else:
            alpha = 0.0

        # Confidence: higher when more feature sources agree
        non_zero_features = sum(1 for v in [container_count, vessels_at_berth, crane_activity] if v > 0)
        confidence = non_zero_features / 3.0

        # Cache for rolling consensus
        if entity_id not in self._consensus_cache:
            self._consensus_cache[entity_id] = []
        self._consensus_cache[entity_id].append(satellite_teu)
        if len(self._consensus_cache[entity_id]) > 52:
            self._consensus_cache[entity_id] = self._consensus_cache[entity_id][-52:]

        return EconomicProxy(
            entity_id=entity_id,
            proxy_name="port_throughput_teu",
            proxy_value=satellite_teu,
            alpha_signal=alpha,
            alpha_confidence=confidence,
            consensus_value=consensus_teu,
            unit="TEU",
            feature_timestamp=feature_vector.timestamp,
            source_features=features,
        )

    def _get_consensus(self, entity_id: str) -> float:
        """Get consensus TEU from historical rolling average."""
        history = self._consensus_cache.get(entity_id, [])
        if not history:
            return 0.0
        return float(np.mean(history))


class RetailOccupancyProxy:
    """
    Convert parking lot CV features into occupancy signals.
    
    Alpha = z-score of current occupancy vs trailing 52-week same-DoW baseline.
    """

    def __init__(self, feature_store: FeatureStore) -> None:
        self._store = feature_store
        self._dow_baselines: dict[str, dict[int, list[float]]] = {}  # entity → dow → values

    def compute(
        self,
        entity_id: str,
        feature_vector: FeatureVector,
    ) -> EconomicProxy:
        """Compute occupancy rate and generate alpha signal."""
        features = feature_vector.features

        car_count = features.get("car_count", 0)
        empty_spaces = features.get("empty_spaces", 0)
        total_spaces = car_count + empty_spaces

        # Occupancy rate
        occupancy_rate = car_count / total_spaces if total_spaces > 0 else 0.0

        # Day-of-week baseline for same-store comparison
        dow = feature_vector.timestamp.weekday()

        if entity_id not in self._dow_baselines:
            self._dow_baselines[entity_id] = {}
        if dow not in self._dow_baselines[entity_id]:
            self._dow_baselines[entity_id][dow] = []

        self._dow_baselines[entity_id][dow].append(occupancy_rate)

        baseline = self._dow_baselines[entity_id][dow]
        if len(baseline) >= 4:  # Need at least 4 weeks
            mean_occ = float(np.mean(baseline[:-1]))  # Exclude current
            std_occ = float(np.std(baseline[:-1]))
            alpha = (occupancy_rate - mean_occ) / std_occ if std_occ > 0 else 0.0
        else:
            alpha = 0.0

        confidence = min(len(baseline) / 12.0, 1.0)  # More history = more confident

        return EconomicProxy(
            entity_id=entity_id,
            proxy_name="retail_parking_occupancy",
            proxy_value=occupancy_rate,
            alpha_signal=alpha,
            alpha_confidence=confidence,
            unit="occupancy_rate",
            feature_timestamp=feature_vector.timestamp,
            source_features=features,
        )


class IndustrialThermalProxy:
    """
    Convert LST anomalies into industrial output intensity proxy.
    
    Alpha = deviation from 5-year seasonal pattern.
    """

    SEASONAL_WINDOW_YEARS = 5

    def __init__(self, feature_store: FeatureStore) -> None:
        self._store = feature_store
        self._seasonal_baselines: dict[str, dict[int, list[float]]] = {}

    def compute(
        self,
        entity_id: str,
        feature_vector: FeatureVector,
    ) -> EconomicProxy:
        """Compute thermal anomaly and generate alpha signal."""
        features = feature_vector.features

        lst_anomaly_zscore = features.get("lst_anomaly_zscore", 0.0)
        thermal_plume_active = features.get("thermal_plume_count_active", 0)
        thermal_plume_inactive = features.get("thermal_plume_count_inactive", 0)

        total_plumes = thermal_plume_active + thermal_plume_inactive
        activity_ratio = thermal_plume_active / total_plumes if total_plumes > 0 else 0.0

        # Operational intensity proxy: combine LST anomaly with activity ratio
        intensity = (lst_anomaly_zscore * 0.6 + activity_ratio * 0.4)

        # Seasonal comparison
        month = feature_vector.timestamp.month
        if entity_id not in self._seasonal_baselines:
            self._seasonal_baselines[entity_id] = {}
        if month not in self._seasonal_baselines[entity_id]:
            self._seasonal_baselines[entity_id][month] = []

        self._seasonal_baselines[entity_id][month].append(intensity)

        baseline = self._seasonal_baselines[entity_id][month]
        if len(baseline) >= 2:
            mean_intensity = float(np.mean(baseline[:-1]))
            std_intensity = float(np.std(baseline[:-1]))
            alpha = (intensity - mean_intensity) / std_intensity if std_intensity > 0 else 0.0
        else:
            alpha = 0.0

        confidence = min(len(baseline) / (self.SEASONAL_WINDOW_YEARS * 1.0), 1.0)

        return EconomicProxy(
            entity_id=entity_id,
            proxy_name="industrial_thermal_intensity",
            proxy_value=intensity,
            alpha_signal=alpha,
            alpha_confidence=confidence,
            unit="intensity_score",
            feature_timestamp=feature_vector.timestamp,
            source_features=features,
        )
