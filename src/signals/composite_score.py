"""
SatTrade Composite Score Engine — IC-Recalibrated WeightOptimizer
=================================================================
Replaces hardcoded weights with Spearman IC dynamic weights.
VIX regime overrides. Correlation penalty. Redis caching. structlog.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import structlog

log = structlog.get_logger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ─── Signal names ─────────────────────────────────────────────────────────────
SIGNALS = ["thermal_frp", "vessel_density", "dark_vessel",
           "flight_intel", "options_flow", "sentiment", "earnings_surprise"]

# ─── VIX Regime Weight Overrides ─────────────────────────────────────────────
VIX_REGIMES: Dict[str, Dict[str, float]] = {
    "CALM": {   # VIX < 15
        "thermal_frp": 0.28, "vessel_density": 0.22, "dark_vessel": 0.12,
        "flight_intel": 0.10, "options_flow": 0.15, "sentiment": 0.08,
        "earnings_surprise": 0.05,
    },
    "NORMAL": None,   # use IC-optimized weights dynamically
    "STRESS": {   # VIX > 25
        "thermal_frp": 0.20, "vessel_density": 0.15, "dark_vessel": 0.30,
        "flight_intel": 0.05, "options_flow": 0.20, "sentiment": 0.05,
        "earnings_surprise": 0.05,
    },
}

# ─── Dataclasses ─────────────────────────────────────────────────────────────
@dataclass
class SignalDataPoint:
    signal_name: str
    score: float             # normalized 0-1
    raw_value: float
    age_s: float
    ic_30d: float = 0.0
    weight: float = 0.0
    direction: str = "NEUTRAL"


@dataclass
class CompositeScoreResult:
    ticker: str
    composite_score: float
    direction: str           # LONG | SHORT | NEUTRAL
    conviction: str          # HIGH | MEDIUM | LOW
    regime: str              # CALM | NORMAL | STRESS
    weight_version: str
    ic_half_life_tag: str    # TACTICAL (<30d) | STRATEGIC (>30d)
    per_signal: Dict[str, dict] = field(default_factory=dict)
    data_freshness: Dict[str, float] = field(default_factory=dict)
    as_of: str = ""
    final_score: float = 0.0
    confidence: float = 0.0
    headline: str = ""


# ─── Weight Optimizer ─────────────────────────────────────────────────────────
class WeightOptimizer:
    """
    Spearman IC-based weight optimizer.
    Runs weekly via Celery beat (Sunday 00:00 UTC).
    Stores results in PostgreSQL signal_weights table.
    """

    FLOOR = 0.02
    CEILING = 0.50
    CORR_THRESHOLD = 0.70
    CORR_PENALTY = 0.25

    def compute_ic(
        self,
        signal_series: np.ndarray,
        return_series: np.ndarray,
        window: int = 63,
    ) -> float:
        """Spearman rank correlation → Information Coefficient."""
        from scipy.stats import spearmanr  # type: ignore
        if len(signal_series) < window or len(return_series) < window:
            return 0.0
        s = signal_series[-window:]
        r = return_series[-window:]
        if np.std(s) == 0 or np.std(r) == 0:
            return 0.0
        corr, pval = spearmanr(s, r)
        return float(corr) if pval < 0.05 else float(corr) * 0.5  # discount insignificant

    def normalize_weights(self, raw_ics: Dict[str, float]) -> Dict[str, float]:
        """Normalize ICs to weights with floor/ceiling constraints."""
        # Shift so minimum IC becomes FLOOR
        min_ic = min(raw_ics.values(), default=0)
        shifted = {k: max(v - min_ic, 0) + self.FLOOR for k, v in raw_ics.items()}
        total = sum(shifted.values())
        if total == 0:
            equal = 1.0 / len(SIGNALS)
            return {k: equal for k in SIGNALS}
        normalized = {k: min(v / total, self.CEILING) for k, v in shifted.items()}
        # Re-normalize after ceiling clamp
        total2 = sum(normalized.values())
        return {k: v / total2 for k, v in normalized.items()}

    def correlation_penalty(
        self,
        weights: Dict[str, float],
        ics: Dict[str, float],
        signal_matrix: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Down-weight lower-IC signal 25% if correlation > 0.70."""
        if signal_matrix is None:
            return weights
        penalized = dict(weights)
        n = len(SIGNALS)
        for i in range(n):
            for j in range(i + 1, n):
                sig_a, sig_b = SIGNALS[i], SIGNALS[j]
                if abs(signal_matrix[i, j]) > self.CORR_THRESHOLD:
                    ic_a = ics.get(sig_a, 0)
                    ic_b = ics.get(sig_b, 0)
                    if ic_a < ic_b:
                        penalized[sig_a] *= (1 - self.CORR_PENALTY)
                    else:
                        penalized[sig_b] *= (1 - self.CORR_PENALTY)
        # Re-normalize
        total = sum(penalized.values())
        return {k: v / total for k, v in penalized.items()} if total else weights

    def get_dynamic_weights(
        self,
        ics: Optional[Dict[str, float]] = None,
        signal_matrix: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Return IC-based weights with correlation penalty applied."""
        if ics is None:
            ics = {s: 0.05 for s in SIGNALS}   # fallback equal IC
        raw = dict(ics)
        weights = self.normalize_weights(raw)
        weights = self.correlation_penalty(weights, ics, signal_matrix)
        return weights

    async def load_stored_weights(self) -> Tuple[Dict[str, float], str]:
        """Load latest IC-optimized weights from Redis/DB."""
        try:
            redis = await _get_redis()
            if redis:
                raw = await redis.get("weights:latest")
                if raw:
                    data = json.loads(raw)
                    return data["weights"], data["version"]
        except Exception as exc:
            log.warning("weight_load_failed", error=str(exc))

        # Fallback balanced weights
        n = len(SIGNALS)
        return {s: 1.0 / n for s in SIGNALS}, "fallback-v0"

    async def run_optimization(
        self,
        signal_histories: Dict[str, np.ndarray],
        return_histories: Dict[str, np.ndarray],
    ) -> Dict[str, float]:
        """Run full IC optimization and persist to Redis."""
        ics: Dict[str, float] = {}
        for signal_name in SIGNALS:
            sig_arr = signal_histories.get(signal_name, np.array([]))
            ret_arr = return_histories.get(signal_name, np.array([]))
            ics[signal_name] = self.compute_ic(sig_arr, ret_arr)

        weights = self.get_dynamic_weights(ics)
        version = f"ic-v-{int(time.time())}"

        payload = json.dumps({"weights": weights, "version": version,
                               "ics": ics, "computed_at": time.time()})
        try:
            redis = await _get_redis()
            if redis:
                await redis.setex("weights:latest", 604_800, payload)
                log.info("weights_stored", version=version, ics=ics)
        except Exception as exc:
            log.error("weight_store_failed", error=str(exc))

        return weights


# ─── Composite Scorer ─────────────────────────────────────────────────────────
class CompositeScorer:
    """Produce composite alpha score for any ticker from all satellite signals."""

    def __init__(self) -> None:
        self._optimizer = WeightOptimizer()
        self._vix: float = 18.0   # default — updated by market_data

    async def _get_vix(self) -> float:
        """Fetch current VIX from Redis quote cache."""
        try:
            redis = await _get_redis()
            if redis:
                raw = await redis.get("quote:VIX")
                if raw:
                    q = json.loads(raw)
                    return float(q.get("price", 18.0))
        except Exception:
            pass
        return self._vix

    def _classify_regime(self, vix: float) -> str:
        if vix < 15:
            return "CALM"
        if vix > 25:
            return "STRESS"
        return "NORMAL"

    async def _fetch_signal_scores(self, ticker: str) -> Dict[str, SignalDataPoint]:
        """Fetch normalized 0-1 scores from each signal agent."""
        scores: Dict[str, SignalDataPoint] = {}

        # Thermal FRP
        try:
            from src.signals.facility_mapper import FacilityMapper
            mapper = FacilityMapper()
            thermal = await mapper.get_ticker_frp(ticker)
            frp = min(float(thermal.get("frp_mw", 0)) / 1500.0, 1.0)
            scores["thermal_frp"] = SignalDataPoint(
                signal_name="thermal_frp",
                score=frp,
                raw_value=thermal.get("frp_mw", 0),
                age_s=thermal.get("age_s", 9999),
                direction="BULLISH" if frp > 0.6 else "NEUTRAL",
            )
        except Exception as exc:
            log.warning("thermal_signal_failed", ticker=ticker, error=str(exc))
            scores["thermal_frp"] = SignalDataPoint("thermal_frp", 0.0, 0, 9999)

        # Vessel density (maritime agent)
        try:
            from src.maritime.vessel_tracker import VesselTracker
            tracker = VesselTracker()
            vs = await tracker.get_ticker_vessel_signal(ticker)
            scores["vessel_density"] = SignalDataPoint(
                signal_name="vessel_density",
                score=float(vs.get("normalized_density", 0)),
                raw_value=vs.get("vessel_count", 0),
                age_s=vs.get("age_s", 9999),
            )
        except Exception:
            scores["vessel_density"] = SignalDataPoint("vessel_density", 0.0, 0, 9999)

        # Dark vessel signal
        try:
            from src.maritime.vessel_tracker import VesselTracker
            tracker = VesselTracker()
            ds = await tracker.get_dark_vessel_signal(ticker)
            dark_score = min(float(ds.get("dark_count", 0)) / 10.0, 1.0)
            scores["dark_vessel"] = SignalDataPoint(
                signal_name="dark_vessel",
                score=dark_score,
                raw_value=ds.get("dark_count", 0),
                age_s=ds.get("age_s", 9999),
                direction="BULLISH" if dark_score > 0.5 else "NEUTRAL",
            )
        except Exception:
            scores["dark_vessel"] = SignalDataPoint("dark_vessel", 0.0, 0, 9999)

        # Flight intel
        try:
            from src.maritime.flight_tracker import FlightTracker
            tracker = FlightTracker()
            fs = await tracker.get_ticker_flight_signal(ticker)
            scores["flight_intel"] = SignalDataPoint(
                signal_name="flight_intel",
                score=float(fs.get("normalized_traffic", 0)),
                raw_value=fs.get("flight_count", 0),
                age_s=fs.get("age_s", 9999),
            )
        except Exception:
            scores["flight_intel"] = SignalDataPoint("flight_intel", 0.0, 0, 9999)

        # Options flow — placeholder (integrate with broker feed)
        scores["options_flow"] = SignalDataPoint("options_flow", 0.5, 0, 300)

        # Sentiment — placeholder (integrate with news score)
        scores["sentiment"] = SignalDataPoint("sentiment", 0.5, 0, 600)

        # Earnings surprise
        scores["earnings_surprise"] = SignalDataPoint("earnings_surprise", 0.5, 0, 86400)

        return scores

    async def score(self, ticker: str) -> dict:
        """
        Produce composite score for ticker.
        Redis cache key: score:{ticker}, TTL=60s.
        """
        # Check cache
        redis = await _get_redis()
        cache_key = f"score:{ticker}"
        if redis:
            try:
                cached = await redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        vix = await self._get_vix()
        regime = self._classify_regime(vix)
        weights, version = await self._optimizer.load_stored_weights()

        # Apply VIX regime override
        if regime != "NORMAL" and VIX_REGIMES[regime]:
            weights = VIX_REGIMES[regime].copy()

        signal_scores = await self._fetch_signal_scores(ticker)

        # Weighted composite
        composite = 0.0
        per_signal: Dict[str, dict] = {}
        data_freshness: Dict[str, float] = {}

        for sig_name, dp in signal_scores.items():
            w = weights.get(sig_name, 1.0 / len(SIGNALS))
            dp.weight = w
            composite += dp.score * w
            per_signal[sig_name] = {
                "score": round(dp.score, 4),
                "weight": round(w, 4),
                "raw_value": dp.raw_value,
                "direction": dp.direction,
                "age_s": dp.age_s,
            }
            data_freshness[sig_name] = dp.age_s

        # Normalize to [-1, 1] → 0 baseline = 0.5 weighted avg
        final_score = (composite - 0.5) * 2   # -1.0 to +1.0

        direction = "NEUTRAL"
        if final_score > 0.15:
            direction = "LONG"
        elif final_score < -0.15:
            direction = "SHORT"

        abs_score = abs(final_score)
        conviction = "HIGH" if abs_score > 0.5 else "MEDIUM" if abs_score > 0.25 else "LOW"
        ic_half_life = "TACTICAL" if any(
            d < 86400 for d in data_freshness.values()
        ) else "STRATEGIC"

        result: dict = {
            "ticker": ticker,
            "composite_score": round(composite, 4),
            "final_score": round(final_score, 4),
            "direction": direction,
            "conviction": conviction,
            "regime": regime,
            "weight_version": version,
            "ic_half_life_tag": ic_half_life,
            "per_signal": per_signal,
            "data_freshness": data_freshness,
            "confidence": round(abs_score, 3),
            "headline": f"{direction} signal (IC {conviction.lower()} conviction) regime={regime}",
            "as_of": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "contributing_signals": [
                {"type": k, "impact": v["direction"], "effective_weight": v["weight"],
                 "headline": f"{k.replace('_', ' ').title()} score {v['score']:.2f}"}
                for k, v in per_signal.items()
            ],
        }

        # Cache 60s
        if redis:
            try:
                await redis.setex(cache_key, 60, json.dumps(result, default=str))
            except Exception:
                pass

        log.info("composite_scored", ticker=ticker, direction=direction,
                 score=round(composite, 4), regime=regime)
        return result


# ─── Redis helper ─────────────────────────────────────────────────────────────
_redis_pool = None

async def _get_redis():
    global _redis_pool
    if _redis_pool is None:
        try:
            import redis.asyncio as aioredis
            _redis_pool = await aioredis.from_url(REDIS_URL, decode_responses=True)
        except Exception as exc:
            log.warning("redis_unavailable", error=str(exc))
            return None
    return _redis_pool
