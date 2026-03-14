"""
Position Sizing — Phase 7.2

Method: Volatility-targeted sizing (Kelly fraction capped at 0.25 Kelly)

Constraints:
  - Max single-name: 2% of NAV
  - Max sector (GICS L2): 15% of NAV
  - Max country: 25% of NAV
  - Max gross exposure: 150% of NAV
  - Min liquidity: position < 5% of 30-day ADTV
  - Forced zero: signal staleness > 5 days
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from src.common.config import get_constraints
from src.execution.signal_scoring import ScoredSignal

logger = logging.getLogger(__name__)


@dataclass
class PositionTarget:
    """Target position for a single asset."""
    asset_id: str
    target_weight: float  # fraction of NAV, can be negative (short)
    target_shares: int
    target_dollar: float
    signal_score: float
    confidence: float
    capped_by: Optional[str] = None  # which constraint limited the size


class PositionSizer:
    """
    Volatility-targeted position sizing with Kelly fraction cap.
    
    Kelly criterion: f* = (p * b - q) / b
    Where: p = win probability, b = win/loss ratio, q = 1 - p
    
    We cap at 0.25 * Kelly to reduce variance.
    """

    KELLY_CAP = 0.25  # Use quarter-Kelly for conservative sizing
    TARGET_VOL_ANNUAL = 0.10  # Target 10% annual portfolio volatility

    def __init__(self) -> None:
        self._constraints = get_constraints()
        self._nav = self._constraints.capital.simulated_nav_usd

    def compute_targets(
        self,
        signals: list[ScoredSignal],
        asset_vols: dict[str, float],  # asset_id → annualised vol
        asset_prices: dict[str, float],
        asset_adtv: dict[str, float],
        asset_sectors: dict[str, str],
        asset_countries: dict[str, str],
        existing_weights: Optional[dict[str, float]] = None,
    ) -> list[PositionTarget]:
        """
        Compute target positions for all assets with active signals.
        
        Steps:
        1. Compute unconstrained Kelly weights
        2. Scale to target portfolio volatility
        3. Apply all hard constraints (position, sector, country, gross, liquidity)
        4. Force zero for stale signals
        """
        existing = existing_weights or {}
        targets: list[PositionTarget] = []

        # Step 1: Compute raw Kelly-inspired weights
        raw_weights = {}
        for sig in signals:
            if sig.is_stale:
                raw_weights[sig.asset_id] = 0.0
                continue

            vol = asset_vols.get(sig.asset_id, 0.2)  # Default 20% vol
            if vol < 0.01:
                vol = 0.01  # Floor to avoid div by zero

            # Simplified Kelly: weight proportional to signal / vol²
            # Capped at KELLY_CAP
            kelly_weight = sig.scored_value * sig.confidence_weight / (vol ** 2)
            kelly_weight = np.clip(kelly_weight, -self.KELLY_CAP, self.KELLY_CAP)
            raw_weights[sig.asset_id] = kelly_weight

        # Step 2: Scale to target vol
        if raw_weights:
            total_gross = sum(abs(w) for w in raw_weights.values())
            if total_gross > 0:
                scale = self.TARGET_VOL_ANNUAL / (total_gross * 0.2)  # rough approx
                scaled_weights = {k: v * min(scale, 1.0) for k, v in raw_weights.items()}
            else:
                scaled_weights = raw_weights
        else:
            scaled_weights = {}

        # Step 3: Apply constraints
        max_single = self._constraints.capital.max_single_name_pct / 100
        max_sector = self._constraints.capital.max_sector_pct / 100
        max_country = self._constraints.capital.max_country_pct / 100
        max_gross = self._constraints.capital.max_gross_exposure_pct / 100
        max_adtv_pct = self._constraints.capital.min_liquidity_adtv_pct / 100

        # Track sector/country totals
        sector_totals: dict[str, float] = {}
        country_totals: dict[str, float] = {}

        for asset_id, weight in scaled_weights.items():
            capped_by = None
            price = asset_prices.get(asset_id, 1.0)
            sector = asset_sectors.get(asset_id, "Unknown")
            country = asset_countries.get(asset_id, "Unknown")
            adtv = asset_adtv.get(asset_id, float("inf"))

            # Single-name cap
            if abs(weight) > max_single:
                weight = max_single * np.sign(weight)
                capped_by = "single_name_limit"

            # Sector cap
            sector_total = sector_totals.get(sector, 0.0)
            if abs(sector_total + weight) > max_sector:
                room = max_sector - abs(sector_total)
                weight = room * np.sign(weight) if room > 0 else 0
                capped_by = "sector_limit"

            # Country cap
            country_total = country_totals.get(country, 0.0)
            if abs(country_total + weight) > max_country:
                room = max_country - abs(country_total)
                weight = room * np.sign(weight) if room > 0 else 0
                capped_by = "country_limit"

            # Liquidity cap: position < 5% of 30-day ADTV
            dollar_value = abs(weight * self._nav)
            max_dollar_from_adtv = adtv * price * max_adtv_pct
            if dollar_value > max_dollar_from_adtv and max_dollar_from_adtv > 0:
                weight = (max_dollar_from_adtv / self._nav) * np.sign(weight)
                capped_by = "liquidity_limit"

            # Update trackers
            sector_totals[sector] = sector_totals.get(sector, 0.0) + weight
            country_totals[country] = country_totals.get(country, 0.0) + weight

            # Compute share count
            target_dollar = weight * self._nav
            target_shares = int(target_dollar / price) if price > 0 else 0

            sig = next((s for s in signals if s.asset_id == asset_id), None)
            targets.append(PositionTarget(
                asset_id=asset_id,
                target_weight=weight,
                target_shares=target_shares,
                target_dollar=target_dollar,
                signal_score=sig.scored_value if sig else 0.0,
                confidence=sig.confidence_weight if sig else 0.0,
                capped_by=capped_by,
            ))

        # Step 4: Gross exposure check
        gross = sum(abs(t.target_weight) for t in targets)
        if gross > max_gross:
            scale_down = max_gross / gross
            for t in targets:
                t.target_weight *= scale_down
                t.target_dollar *= scale_down
                t.target_shares = int(t.target_dollar / asset_prices.get(t.asset_id, 1.0))
                if t.capped_by is None:
                    t.capped_by = "gross_exposure_limit"
            logger.warning(f"Gross exposure {gross:.2%} exceeds {max_gross:.2%} — scaled down by {scale_down:.2f}")

        logger.info(f"Position sizing complete: {len(targets)} targets, "
                   f"gross={sum(abs(t.target_weight) for t in targets):.2%}")

        return targets
