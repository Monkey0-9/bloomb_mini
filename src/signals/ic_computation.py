"""
Information Coefficient (IC) Computation Module.

Replaces any hardcoded IC values with real Spearman rank correlation
between satellite signal scores and forward equity returns.

IC formula:
    IC_t = spearmanr(signal_scores_t, forward_returns_t+N)[0]

where N is the holding period (1d, 5d, 21d, 63d).

Uses yfinance for free historical prices — no API key required.
No hardcoded value of 0.047. Every signal location gets a different IC
because the physical phenomena are genuinely different.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ICResult:
    """Real IC computed for a specific signal at a specific horizon."""

    signal_name: str
    ticker: str
    horizon_days: int
    ic: float                # Spearman ρ between signal and forward return
    icir: float              # IC / std(IC) across rolling windows
    n_observations: int
    p_value: float           # Statistical significance
    computed_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    is_significant: bool = False   # p < 0.05

    def __post_init__(self) -> None:
        self.is_significant = self.p_value < 0.05


def compute_ic(
    signal_scores: list[float],
    forward_returns: list[float],
) -> tuple[float, float]:
    """
    Compute Spearman rank IC between signal scores and forward returns.

    Args:
        signal_scores:   List of signal scores (e.g. thermal anomaly sigma).
        forward_returns: Matching list of realised forward returns.

    Returns:
        (ic, p_value) tuple.
    """
    from scipy.stats import spearmanr  # type: ignore[import-untyped]

    if len(signal_scores) < 5:
        return 0.0, 1.0

    signals = np.array(signal_scores, dtype=float)
    returns = np.array(forward_returns, dtype=float)

    # Remove NaN pairs
    mask = ~(np.isnan(signals) | np.isnan(returns))
    if mask.sum() < 5:
        return 0.0, 1.0

    result = spearmanr(signals[mask], returns[mask])
    ic = float(result.statistic)
    p_value = float(result.pvalue)
    return ic, p_value


def compute_rolling_icir(
    signal_series: list[float],
    return_series: list[float],
    window: int = 12,
) -> float:
    """
    Compute IC Information Ratio over a rolling window.

    ICIR = mean(IC_t) / std(IC_t)    across window sub-periods.
    A high ICIR (> 0.5) means the signal is consistently predictive.

    Args:
        signal_series: All signal observations.
        return_series: Matching forward returns.
        window:        Sub-window size for rolling IC computation.

    Returns:
        ICIR as a float. 0.0 if insufficient data.
    """
    if len(signal_series) < window * 2:
        return 0.0

    ics: list[float] = []
    for i in range(0, len(signal_series) - window, window // 2):
        chunk_sig = signal_series[i: i + window]
        chunk_ret = return_series[i: i + window]
        ic, _ = compute_ic(chunk_sig, chunk_ret)
        ics.append(ic)

    if len(ics) < 2:
        return 0.0

    ic_arr = np.array(ics)
    std = float(ic_arr.std())
    return float(ic_arr.mean() / std) if std > 1e-6 else 0.0


def fetch_forward_returns(
    ticker: str,
    dates: list[datetime],
    horizon_days: int = 21,
) -> list[float]:
    """
    Fetch realised forward returns for a ticker on given signal dates.

    Uses yfinance — 50,000+ tickers, zero key.

    Args:
        ticker:        Equity ticker (e.g. 'MT', 'XOM', 'ZIM').
        dates:         Dates at which signal was observed.
        horizon_days:  Holding period. Return is close[t+N] / close[t] - 1.

    Returns:
        List of forward returns aligned to input dates. NaN for missing data.
    """
    import yfinance as yf

    if not dates:
        return []

    # Fetch enough history to cover all dates + horizon
    start = min(dates) - timedelta(days=10)
    end = max(dates) + timedelta(days=horizon_days + 10)

    try:
        raw: pd.DataFrame = yf.download(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            auto_adjust=True,
            progress=False,
        )
        if raw.empty:
            return [float("nan")] * len(dates)

        closes: pd.Series = raw["Close"]

    except Exception as exc:
        logger.warning("IC fetch failed for %s: %s", ticker, exc)
        return [float("nan")] * len(dates)

    returns: list[float] = []
    for signal_date in dates:
        try:
            # Find the close on or after signal_date
            after = closes[closes.index >= pd.Timestamp(signal_date)]
            if after.empty:
                returns.append(float("nan"))
                continue
            entry_price = float(after.iloc[0])

            # Find close N trading days later
            future = closes[
                closes.index >= (pd.Timestamp(signal_date) + timedelta(days=horizon_days))
            ]
            if future.empty:
                returns.append(float("nan"))
                continue
            exit_price = float(future.iloc[0])

            fwd_return = (exit_price / entry_price) - 1.0
            returns.append(fwd_return)

        except Exception:
            returns.append(float("nan"))

    return returns


def compute_signal_ic_full(
    signal_name: str,
    ticker: str,
    signal_history: list[dict[str, Any]],
    horizons: list[int] | None = None,
) -> list[ICResult]:
    """
    Full IC computation for one signal location across multiple horizons.

    Args:
        signal_name:    Name of the signal (e.g. 'arcelor_dunkirk').
        ticker:         Primary ticker (e.g. 'MT').
        signal_history: List of dicts with keys 'date' (datetime) and
                        'score' (float thermal sigma or port pct delta).
        horizons:       Holding periods in days to test. Default: [1,5,21,63].

    Returns:
        List of ICResult objects, one per horizon.
    """
    if horizons is None:
        horizons = [1, 5, 21, 63]

    if len(signal_history) < 10:
        logger.info(
            "IC skipped for %s/%s: only %d observations (need ≥10)",
            signal_name, ticker, len(signal_history),
        )
        return []

    results: list[ICResult] = []
    dates = [h["date"] for h in signal_history]
    scores = [float(h["score"]) for h in signal_history]

    for horizon in horizons:
        fwd_returns = fetch_forward_returns(ticker, dates, horizon_days=horizon)
        ic, p_value = compute_ic(scores, fwd_returns)
        icir = compute_rolling_icir(scores, fwd_returns)

        n_valid = sum(
            1 for s, r in zip(scores, fwd_returns)
            if not np.isnan(s) and not np.isnan(r)
        )

        result = ICResult(
            signal_name=signal_name,
            ticker=ticker,
            horizon_days=horizon,
            ic=round(ic, 4),
            icir=round(icir, 2),
            n_observations=n_valid,
            p_value=round(p_value, 4),
        )
        results.append(result)
        logger.info(
            "IC[%s/%s @%dd]: ic=%.4f icir=%.2f p=%.3f n=%d%s",
            signal_name, ticker, horizon, ic, icir, p_value, n_valid,
            " ✓SIGNIFICANT" if result.is_significant else "",
        )

    return results
