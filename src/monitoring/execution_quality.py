"""
Unified Live Monitoring & Fill-Quality Dashboard — Phase 12

Tracks real-time execution quality and system health during soft-launch.
"""
from __future__ import annotations

from prometheus_client import Counter, Gauge, Summary

# Execution Monitoring metrics
FILL_PRICE_ERROR_BPS = Gauge(
    "execution_fill_price_error_bps",
    "Difference between expected and actual fill price",
    ["symbol"],
)
ORDER_ROUTE_LATENCY = Summary(
    "execution_order_route_latency_ms", "Time from signal to broker submission"
)
POSITION_RECON_MISMATCH = Counter(
    "execution_recon_mismatch_total", "Number of times internal and broker ledgers disagreed"
)
RAMP_PERCENTAGE = Gauge(
    "execution_ramp_percentage", "Current NAV allocation percentage of the strategy"
)


class ExecutionMonitor:
    def __init__(self) -> None:
        RAMP_PERCENTAGE.set(10.0)  # Start at 10%

    def record_fill_error(self, symbol: str, error_bps: float) -> None:
        FILL_PRICE_ERROR_BPS.labels(symbol=symbol).set(error_bps)

    def record_recon_failure(self) -> None:
        POSITION_RECON_MISMATCH.inc()

    def update_ramp(self, pct: float) -> None:
        RAMP_PERCENTAGE.set(pct * 100)
