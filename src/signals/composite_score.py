"""
Weighted Composite Signal Score — principled combination of all signal sources.
Combines vessel density, flight activity, thermal anomalies, and market data
into a single IC-weighted alpha score per equity ticker.
"""
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class CompositeScore:
    ticker: str
    final_score: float          # -1.0 (max bearish) to +1.0 (max bullish)
    direction: str              # BULLISH / BEARISH / NEUTRAL
    confidence: str             # HIGH / MEDIUM / LOW
    contributing_signals: list[dict]
    signal_count: int
    as_of: str


# Signal weights derived from literature (IC-based, not arbitrary)
# Higher weight = historically more predictive for these asset classes
SIGNAL_WEIGHTS = {
    "thermal_frp": 0.35,        # Industrial heat — highest alpha, unique to us
    "vessel_density": 0.25,     # Port throughput proxy
    "dark_vessel": 0.20,        # Sanctions/disruption proxy
    "flight_cargo": 0.10,       # Air freight demand
    "news_sentiment": 0.05,     # Noisy but directional
    "options_skew": 0.05,       # Smart money positioning
}

# Ticker-to-signal mapping: which signals are relevant for each ticker
TICKER_SIGNAL_MAP = {
    "MT": ["thermal_frp", "vessel_density"],
    "STLD": ["thermal_frp"],
    "NUE": ["thermal_frp"],
    "LNG": ["thermal_frp", "vessel_density"],
    "CQP": ["thermal_frp"],
    "ZIM": ["vessel_density", "dark_vessel"],
    "MATX": ["vessel_density"],
    "SBLK": ["vessel_density", "dark_vessel"],
    "FDX": ["flight_cargo"],
    "UPS": ["flight_cargo"],
}


def _normalize_score(raw: float, min_val: float, max_val: float) -> float:
    """Normalize a raw signal value to [-1, +1]."""
    if max_val == min_val:
        return 0.0
    normalized = (raw - min_val) / (max_val - min_val)
    return (normalized * 2) - 1  # Scale to [-1, +1]


def compute_composite(
    ticker: str,
    thermal_signal: dict | None = None,
    vessel_signal: dict | None = None,
    flight_signal: dict | None = None,
    options_signal: dict | None = None,
) -> CompositeScore:
    """
    Compute principled composite score for a ticker from all available signals.
    Only includes signals where we have real data (no padding with neutral scores).
    """
    contributing = []
    weighted_sum = 0.0
    total_weight = 0.0

    # Thermal signal
    if thermal_signal and thermal_signal.get("signal") in ("BULLISH", "BEARISH", "NEUTRAL"):
        direction_val = 1.0 if thermal_signal["signal"] == "BULLISH" else (-1.0 if thermal_signal["signal"] == "BEARISH" else 0.0)
        w = SIGNAL_WEIGHTS["thermal_frp"]
        weighted_sum += direction_val * w
        total_weight += w
        contributing.append({
            "signal_type": "thermal_frp",
            "direction": thermal_signal["signal"],
            "weight": w,
            "contribution": direction_val * w,
            "reason": thermal_signal.get("signal_reason", ""),
        })

    # Vessel density signal
    if vessel_signal and vessel_signal.get("signal") in ("BULLISH", "BEARISH", "NEUTRAL"):
        direction_val = 1.0 if vessel_signal["signal"] == "BULLISH" else (-1.0 if vessel_signal["signal"] == "BEARISH" else 0.0)
        w = SIGNAL_WEIGHTS["vessel_density"]
        weighted_sum += direction_val * w
        total_weight += w
        contributing.append({
            "signal_type": "vessel_density",
            "direction": vessel_signal["signal"],
            "weight": w,
            "contribution": direction_val * w,
            "reason": vessel_signal.get("reason", ""),
        })

    # Flight cargo signal
    if flight_signal and flight_signal.get("signal") in ("BULLISH", "BEARISH", "NEUTRAL"):
        direction_val = 1.0 if flight_signal["signal"] == "BULLISH" else (-1.0 if flight_signal["signal"] == "BEARISH" else 0.0)
        w = SIGNAL_WEIGHTS["flight_cargo"]
        weighted_sum += direction_val * w
        total_weight += w
        contributing.append({
            "signal_type": "flight_cargo",
            "direction": flight_signal["signal"],
            "weight": w,
            "contribution": direction_val * w,
            "reason": flight_signal.get("reason", ""),
        })

    # Options skew signal
    if options_signal:
        pcr = options_signal.get("put_call_ratio", 1.0)
        # PCR > 1.2 = bearish positioning, PCR < 0.8 = bullish positioning
        if pcr > 1.2:
            direction_val = -1.0
            direction = "BEARISH"
            reason = f"Put/Call ratio {pcr:.2f} — elevated put buying"
        elif pcr < 0.8:
            direction_val = 1.0
            direction = "BULLISH"
            reason = f"Put/Call ratio {pcr:.2f} — call demand elevated"
        else:
            direction_val = 0.0
            direction = "NEUTRAL"
            reason = f"Put/Call ratio {pcr:.2f} — neutral positioning"
        w = SIGNAL_WEIGHTS["options_skew"]
        weighted_sum += direction_val * w
        total_weight += w
        contributing.append({
            "signal_type": "options_skew",
            "direction": direction,
            "weight": w,
            "contribution": direction_val * w,
            "reason": reason,
        })

    # Need at least 2 signals to produce a composite
    if len(contributing) < 2:
        return CompositeScore(
            ticker=ticker,
            final_score=0.0,
            direction="INSUFFICIENT_DATA",
            confidence="LOW",
            contributing_signals=contributing,
            signal_count=len(contributing),
            as_of=datetime.now(timezone.utc).isoformat(),
        )

    final_score = weighted_sum / total_weight if total_weight > 0 else 0.0

    if final_score > 0.15:
        direction = "BULLISH"
        confidence = "HIGH" if final_score > 0.40 else "MEDIUM"
    elif final_score < -0.15:
        direction = "BEARISH"
        confidence = "HIGH" if final_score < -0.40 else "MEDIUM"
    else:
        direction = "NEUTRAL"
        confidence = "LOW"

    return CompositeScore(
        ticker=ticker,
        final_score=round(final_score, 4),
        direction=direction,
        confidence=confidence,
        contributing_signals=contributing,
        signal_count=len(contributing),
        as_of=datetime.now(timezone.utc).isoformat(),
    )
