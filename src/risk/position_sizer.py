"""
SatTrade Half-Kelly Position Sizer
====================================
Uses TFT P50 direction accuracy (63d) to compute Kelly fraction.
Endpoint: POST /api/v1/risk/size
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import asdict, dataclass

import structlog

log = structlog.get_logger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


@dataclass
class PositionSizeResult:
    ticker: str
    entry: float
    stop: float
    target: float
    kelly_full: float
    kelly_half: float
    recommended_shares: float
    notional: float
    pct_portfolio: float
    marginal_var_impact: float
    expected_win_pct: float   # TFT P50 direction accuracy
    reward_risk_ratio: float  # b = (target - entry) / (entry - stop)
    all_gate_previews: dict


class HalfKellySizer:
    """
    Half-Kelly position sizing grounded in TFT probabilistic forecast accuracy.
    p = rolling 63d accuracy of TFT P50 direction prediction
    b = (target - entry) / (entry - stop)
    kelly_full = (p*b - (1-p)) / b
    kelly_half = kelly_full / 2
    recommended_shares = min(kelly_half * equity, 0.25 * equity) / entry_price
    """

    CONCENTRATION_CAP = 0.25   # max 25% of equity in single position

    async def _get_redis(self):
        try:
            import redis.asyncio as aioredis
            return await aioredis.from_url(REDIS_URL, decode_responses=True)
        except Exception:
            return None

    async def _get_tft_accuracy(self, ticker: str) -> float:
        """
        Get rolling 63d accuracy of TFT P50 direction prediction.
        Stored by drift watchdog in Redis.
        """
        r = await self._get_redis()
        if r:
            try:
                raw = await r.get(f"tft:accuracy:{ticker}:63d")
                if raw:
                    return float(raw)
            except Exception:
                pass

        # Fallback: run a quick proxy from IC scores
        try:
            from src.signals.tft_model import ModelServer
            srv = ModelServer()
            ic = srv._drift_ic_rolling.get(ticker, 0.05)
            # IC ≈ 2*(accuracy - 0.5), so accuracy ≈ IC/2 + 0.5
            return min(max(ic / 2.0 + 0.5, 0.40), 0.70)
        except Exception:
            return 0.52   # slightly better than coin flip as conservative default

    async def size(
        self,
        ticker: str,
        entry: float,
        stop: float,
        target: float,
        equity: float = 100_000.0,
    ) -> dict:
        """Compute Half-Kelly position size with all 9 gate previews."""
        if entry <= 0 or stop <= 0 or target <= 0:
            raise ValueError("entry, stop, and target must be positive")
        if stop >= entry:
            raise ValueError("stop must be below entry for a long position")
        if target <= entry:
            raise ValueError("target must be above entry for a long position")

        # Fetch accuracy in parallel with gate preview
        p, gate_preview = await asyncio.gather(
            self._get_tft_accuracy(ticker),
            self._preview_gates(ticker, entry, equity),
        )

        b = (target - entry) / (entry - stop)
        if b <= 0:
            kelly_full = 0.0
        else:
            kelly_full = (p * b - (1 - p)) / b

        kelly_half = max(kelly_full / 2.0, 0.0)
        kelly_notional = kelly_half * equity
        capped_notional = min(kelly_notional, self.CONCENTRATION_CAP * equity)
        shares = capped_notional / entry if entry > 0 else 0
        pct = capped_notional / equity

        # Estimate marginal VaR impact (simplified)
        daily_vol = abs(entry - stop) / entry
        marginal_var = pct * daily_vol * 2.33   # ~99th percentile

        result = PositionSizeResult(
            ticker=ticker,
            entry=round(entry, 4),
            stop=round(stop, 4),
            target=round(target, 4),
            kelly_full=round(kelly_full, 4),
            kelly_half=round(kelly_half, 4),
            recommended_shares=round(shares, 0),
            notional=round(capped_notional, 2),
            pct_portfolio=round(pct, 4),
            marginal_var_impact=round(marginal_var, 4),
            expected_win_pct=round(p, 4),
            reward_risk_ratio=round(b, 4),
            all_gate_previews=gate_preview,
        )

        log.info("position_sized", ticker=ticker, shares=round(shares, 0),
                 kelly_half=round(kelly_half, 4), p=round(p, 4))
        return asdict(result)

    async def _preview_gates(self, ticker: str, entry: float, equity: float) -> dict:
        """Quick non-binding gate preview for UI display."""
        try:
            from src.risk.engine import RiskEngine
            engine = RiskEngine()
            preview = await engine.evaluate_trade({
                "ticker": ticker, "qty": 1, "price": entry,
                "side": "LONG", "user_id": "preview",
            })
            return {g["gate_name"]: g["result"] for g in preview.get("gates", [])}
        except Exception as exc:
            log.warning("gate_preview_failed", error=str(exc))
            return {g: "UNKNOWN" for g in [
                "GROSS_EXPOSURE", "VAR_99", "CVAR_99", "CONCENTRATION",
                "CORRELATION", "FAT_FINGER", "SAT_STALENESS", "STRESS_TEST", "KILL_SWITCH"
            ]}
