"""
Signal Scoring Engine — Phase 7.1

Transforms raw model outputs into normalised, risk-adjusted trading signals.

Processing steps:
  a. Apply signal staleness decay (half-life = satellite revisit period)
  b. Winsorise at ±3 sigma cross-sectionally
  c. Sector-neutralise: demean within GICS sector
  d. Scale to [-1, +1] using rolling 252-day rank normalisation
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RawSignal:
    """Raw model output for a single asset."""

    asset_id: str
    signal_value: float
    confidence: float  # 0–1
    signal_timestamp: datetime
    model_version: str
    gics_sector: str  # GICS Level 2 code
    source_tile_ids: list[str]


class FinalScoredSignal:
    """Final scored signal ready for position sizing."""

    def __init__(
        self,
        asset_id: str,
        raw_value: float,
        scored_value: float,
        confidence_weight: float,
        staleness_factor: float,
        sector_neutral: bool,
        signal_age_seconds: int,
        model_version: str,
        is_stale: bool,
    ) -> None:
        self.asset_id = asset_id
        self.raw_value = raw_value
        self.scored_value = scored_value
        self.confidence_weight = confidence_weight
        self.staleness_factor = staleness_factor
        self.sector_neutral = sector_neutral
        self.signal_age_seconds = signal_age_seconds
        self.model_version = model_version
        self.is_stale = is_stale


class SignalScoringEngine:
    """
    Transforms raw signals into normalised, sector-neutral scores.

    Output: normalised signal score ∈ [-1, +1] with confidence weight per asset.
    """

    STALENESS_HALF_LIFE_DAYS = 5.0  # Sentinel revisit period ~5 days
    STALENESS_FORCE_ZERO_DAYS = 5.0  # Forced zero if > 5 days stale
    WINSORIZE_SIGMA = 3.0
    ROLLING_WINDOW_DAYS = 252  # 1 trading year

    def __init__(self) -> None:
        self._historical_signals: list[float] = []

    def score_batch(
        self,
        raw_signals: list[RawSignal],
        current_time: datetime | None = None,
    ) -> list[FinalScoredSignal]:
        """
        Score a batch of raw signals through the full pipeline.

        Steps:
        1. Compute staleness decay
        2. Winsorise cross-sectionally
        3. Sector-neutralise
        4. Rank-normalise to [-1, +1]
        """
        if not raw_signals:
            return []

        now = current_time or datetime.now(UTC)

        # Step 1: Compute staleness for each signal
        signals_with_staleness = []
        for sig in raw_signals:
            age_seconds = int((now - sig.signal_timestamp).total_seconds())
            age_days = age_seconds / 86400
            staleness = self._compute_staleness_decay(age_days)
            is_stale = age_days > self.STALENESS_FORCE_ZERO_DAYS
            signals_with_staleness.append((sig, staleness, age_seconds, is_stale))

        # Step 2: Extract values and winsorise
        values = np.array([s[0].signal_value * s[1] for s in signals_with_staleness])
        winsorised = self._winsorise(values)

        # Step 3: Sector-neutralise
        sectors = [s[0].gics_sector for s in signals_with_staleness]
        neutralised = self._sector_neutralise(winsorised, sectors)

        # Step 4: Rank-normalise to [-1, +1]
        normalised = self._rank_normalise(neutralised)

        # Build results
        results = []
        for i, (sig, staleness, age_sec, is_stale) in enumerate(signals_with_staleness):
            scored = FinalScoredSignal(
                asset_id=sig.asset_id,
                raw_value=sig.signal_value,
                scored_value=0.0 if is_stale else float(normalised[i]),
                confidence_weight=sig.confidence * staleness if not is_stale else 0.0,
                staleness_factor=staleness,
                sector_neutral=True,
                signal_age_seconds=age_sec,
                model_version=sig.model_version,
                is_stale=is_stale,
            )
            results.append(scored)

            if is_stale:
                logger.warning(
                    f"Signal for {sig.asset_id} is STALE ({age_sec / 86400:.1f} days) "
                    f"— forced to zero"
                )

        return results

    def _compute_staleness_decay(self, age_days: float) -> float:
        """
        Exponential decay with half-life = satellite revisit period.

        decay = 0.5 ^ (age / half_life)
        Returns 1.0 for fresh signals, approaches 0 for old signals.
        """
        if age_days <= 0:
            return 1.0
        return math.pow(0.5, age_days / self.STALENESS_HALF_LIFE_DAYS)

    def _winsorise(self, values: np.ndarray) -> np.ndarray:
        """
        Winsorise at ±3 sigma cross-sectionally.
        Clips extreme values to prevent any single outlier from dominating.
        """
        if len(values) < 2:
            return values

        mean = np.nanmean(values)
        std = np.nanstd(values)

        if std < 1e-10:
            return cast(np.ndarray, values - mean)

        lower = mean - self.WINSORIZE_SIGMA * std
        upper = mean + self.WINSORIZE_SIGMA * std
        return cast(np.ndarray, np.clip(values, lower, upper))

    def _sector_neutralise(self, values: np.ndarray, sectors: list[str]) -> np.ndarray:
        """
        Demean within GICS sector to remove sector effects.
        Ensures signals are cross-sectionally comparable.
        """
        result = values.copy()
        unique_sectors = set(sectors)

        for sector in unique_sectors:
            mask = np.array([s == sector for s in sectors])
            if np.sum(mask) > 1:
                sector_mean = np.nanmean(result[mask])
                result[mask] -= sector_mean

        return result

    def _rank_normalise(self, values: np.ndarray) -> np.ndarray:
        """
        Rank-normalise values to [-1, +1].
        """
        n = len(values)
        if n <= 1:
            return values

        temp = values.argsort().argsort() + 1  # ranks from 1 to n
        # Scale to [-1, +1]
        normalised = 2.0 * (temp - 1) / (n - 1) - 1.0
        return cast(np.ndarray, normalised)
