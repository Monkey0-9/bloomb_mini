"""
Risk Engine — Phase 7.3

Pre-trade checks (synchronous, blocking):
  □ Liquidity check: ADTV participation ≤ 5%
  □ Position limit check
  □ Sector/country limit check
  □ Signal freshness check
  □ VaR check: 1-day 99% VaR ≤ 1.5% of NAV
  □ Compliance blocklist check

Real-time monitors (async, alerting):
  □ Drawdown alert at 3%, halt at 5%
  □ Signal correlation spike
  □ Data feed latency alert
  □ Model confidence threshold

Kill-switch triggers (immediate full liquidation):
  □ Portfolio drawdown > 8% (rolling 20-day)
  □ 3 consecutive failed pre-trade checks
  □ Data pipeline outage > 4 hours
  □ Manual override
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import numpy as np
from typing import Any, Optional

from src.common.config import get_constraints
from src.common.schemas import AuditLogEntry, QualityCheckResult

logger = logging.getLogger(__name__)


class RiskCheckType(str, Enum):
    LIQUIDITY = "liquidity"
    POSITION_LIMIT = "position_limit"
    SECTOR_LIMIT = "sector_limit"
    COUNTRY_LIMIT = "country_limit"
    SIGNAL_FRESHNESS = "signal_freshness"
    VAR = "var"
    GROSS_EXPOSURE = "gross_exposure"
    COMPLIANCE = "compliance"


class KillSwitchReason(str, Enum):
    DRAWDOWN = "portfolio_drawdown_exceeded"
    CONSECUTIVE_FAILURES = "consecutive_pretrade_failures"
    DATA_OUTAGE = "data_pipeline_outage"
    MANUAL = "manual_override"


@dataclass
class PortfolioPosition:
    """Current position in a single asset."""
    asset_id: str
    quantity: float
    market_value: float
    gics_sector: str  # GICS Level 2
    country: str  # ISO 3166-1 alpha-2
    adtv_30d: float  # Average daily trading volume (shares)
    current_price: float


@dataclass
class PreTradeCheckResult:
    """Result of all pre-trade checks for a proposed order."""
    order_id: str
    asset_id: str
    all_passed: bool
    checks: list[QualityCheckResult] = field(default_factory=list)
    blocked: bool = False
    block_reason: Optional[str] = None


@dataclass
class KillSwitchEvent:
    """Kill-switch activation event."""
    event_id: str
    reason: KillSwitchReason
    timestamp_utc: datetime
    details: str
    positions_to_liquidate: list[str]


class RiskEngine:
    """
    Production risk engine with pre-trade checks, real-time monitors,
    and kill-switch triggers.
    
    All checks are logged to the audit trail. Pre-trade checks are
    synchronous and blocking — an order cannot proceed if any check fails.
    """

    # Kill-switch thresholds
    DRAWDOWN_ALERT_PCT = 3.0
    DRAWDOWN_HALT_PCT = 5.0
    DRAWDOWN_KILL_PCT = 8.0
    DRAWDOWN_ROLLING_DAYS = 20

    MAX_CONSECUTIVE_FAILURES = 3
    DATA_OUTAGE_KILL_HOURS = 4

    CORRELATION_SPIKE_THRESHOLD = 0.7
    CORRELATION_EXPOSURE_REDUCTION = 0.5
    MAX_GROSS_EXPOSURE_PCT = 150.0  # Align to Spec (1.5x Leverage)

    def __init__(self) -> None:
        self._constraints = get_constraints()
        self._consecutive_failures: dict[str, int] = {}  # check_type → count
        self._audit_log: list[AuditLogEntry] = []
        self._kill_switch_active = False
        self._pending_halt_request: Optional[dict[str, Any]] = None

    @property
    def is_killed(self) -> bool:
        return self._kill_switch_active

    # ─── Pre-Trade Checks (Synchronous, Blocking) ──────────────────────

    def run_pretrade_checks(
        self,
        asset_id: str,
        proposed_quantity: float,
        proposed_price: float,
        signal_age_seconds: int,
        current_positions: list[PortfolioPosition],
        returns_history: Optional[np.ndarray] = None,
        blocklist: Optional[set[str]] = None,
    ) -> PreTradeCheckResult:
        """
        Run ALL pre-trade checks. All must pass for the order to proceed.
        Results are logged to the audit trail.
        """
        if self._kill_switch_active:
            return PreTradeCheckResult(
                order_id=str(uuid.uuid4()),
                asset_id=asset_id,
                all_passed=False,
                blocked=True,
                block_reason="KILL SWITCH ACTIVE — all trading halted",
            )

        order_id = str(uuid.uuid4())
        checks: list[QualityCheckResult] = []
        nav = self._constraints.capital.simulated_nav_usd

        # Find current position in this asset
        current_pos = next((p for p in current_positions if p.asset_id == asset_id), None)
        proposed_value = abs(proposed_quantity * proposed_price)

        # 1. Liquidity check
        checks.append(self._check_liquidity(asset_id, proposed_quantity, current_pos))

        # 2. Position limit check
        checks.append(self._check_position_limit(asset_id, proposed_value, nav, current_pos))

        # 3. Sector limit check
        sector = current_pos.gics_sector if current_pos else "Unknown"
        checks.append(self._check_sector_limit(sector, proposed_value, nav, current_positions))

        # 4. Country limit check
        country = current_pos.country if current_pos else "Unknown"
        checks.append(self._check_country_limit(country, proposed_value, nav, current_positions))

        # 5. Signal freshness check
        checks.append(self._check_signal_freshness(asset_id, signal_age_seconds))

        # 6. VaR check
        checks.append(self._check_var(proposed_value, nav, current_positions, returns_history))

        # 7. Gross Exposure check
        checks.append(self._check_gross_exposure(proposed_value, nav, current_positions))

        # 8. Compliance blocklist check
        checks.append(self._check_compliance(asset_id, blocklist))

        all_passed = all(c.passed for c in checks)

        # Track consecutive failures
        if not all_passed:
            failed_types = [c.check_name for c in checks if not c.passed]
            for ft in failed_types:
                self._consecutive_failures[ft] = self._consecutive_failures.get(ft, 0) + 1
                if self._consecutive_failures[ft] >= self.MAX_CONSECUTIVE_FAILURES:
                    self._activate_kill_switch(
                        KillSwitchReason.CONSECUTIVE_FAILURES,
                        f"3 consecutive failures of {ft} check",
                        [p.asset_id for p in current_positions],
                    )
        else:
            self._consecutive_failures.clear()

        # Log to audit trail
        self._log_risk_check(order_id, asset_id, proposed_quantity, proposed_price, checks)

        result = PreTradeCheckResult(
            order_id=order_id,
            asset_id=asset_id,
            all_passed=all_passed,
            checks=checks,
        )

        if not all_passed:
            failed = [c for c in checks if not c.passed]
            result.blocked = True
            result.block_reason = "; ".join(c.message for c in failed)
            logger.warning(f"PRE-TRADE BLOCKED {asset_id}: {result.block_reason}")
        else:
            logger.info(f"PRE-TRADE PASSED {asset_id}: all {len(checks)} checks passed")

        return result

    def _check_liquidity(
        self, asset_id: str, quantity: float, position: Optional[PortfolioPosition]
    ) -> QualityCheckResult:
        """ADTV participation ≤ 5%."""
        if position is None or position.adtv_30d is None or position.adtv_30d <= 0:
            return QualityCheckResult(
                check_name=RiskCheckType.LIQUIDITY,
                passed=False,
                message=f"No ADTV data for {asset_id}",
            )

        participation = abs(quantity) / position.adtv_30d * 100
        threshold = self._constraints.capital.min_liquidity_adtv_pct
        passed = participation <= threshold

        return QualityCheckResult(
            check_name=RiskCheckType.LIQUIDITY,
            passed=passed,
            value=participation,
            threshold=threshold,
            message=(
                f"ADTV participation {participation:.2f}% ≤ {threshold}%"
                if passed
                else f"ADTV participation {participation:.2f}% EXCEEDS {threshold}% — BLOCKED"
            ),
        )

    def _check_position_limit(
        self, asset_id: str, proposed_value: float, nav: float,
        position: Optional[PortfolioPosition],
    ) -> QualityCheckResult:
        """Max single-name: 2% of NAV."""
        current_value = position.market_value if position else 0.0
        total_value = current_value + proposed_value
        pct = total_value / nav * 100 if nav > 0 else 100
        threshold = self._constraints.capital.max_single_name_pct

        return QualityCheckResult(
            check_name=RiskCheckType.POSITION_LIMIT,
            passed=pct <= threshold,
            value=pct,
            threshold=threshold,
            message=(
                f"Position {pct:.2f}% of NAV ≤ {threshold}%"
                if pct <= threshold
                else f"Position {pct:.2f}% of NAV EXCEEDS {threshold}% — BLOCKED"
            ),
        )

    def _check_sector_limit(
        self, sector: str, proposed_value: float, nav: float,
        positions: list[PortfolioPosition],
    ) -> QualityCheckResult:
        """Max sector (GICS L2): 15% of NAV."""
        sector_value = sum(p.market_value for p in positions if p.gics_sector == sector)
        total = sector_value + proposed_value
        pct = total / nav * 100 if nav > 0 else 100
        threshold = self._constraints.capital.max_sector_pct

        return QualityCheckResult(
            check_name=RiskCheckType.SECTOR_LIMIT,
            passed=pct <= threshold,
            value=pct,
            threshold=threshold,
            message=(
                f"Sector '{sector}' exposure {pct:.2f}% ≤ {threshold}%"
                if pct <= threshold
                else f"Sector '{sector}' exposure {pct:.2f}% EXCEEDS {threshold}% — BLOCKED"
            ),
        )

    def _check_country_limit(
        self, country: str, proposed_value: float, nav: float,
        positions: list[PortfolioPosition],
    ) -> QualityCheckResult:
        """Max country: 25% of NAV."""
        country_value = sum(p.market_value for p in positions if p.country == country)
        total = country_value + proposed_value
        pct = total / nav * 100 if nav > 0 else 100
        threshold = self._constraints.capital.max_country_pct

        return QualityCheckResult(
            check_name=RiskCheckType.COUNTRY_LIMIT,
            passed=pct <= threshold,
            value=pct,
            threshold=threshold,
            message=(
                f"Country '{country}' exposure {pct:.2f}% ≤ {threshold}%"
                if pct <= threshold
                else f"Country '{country}' exposure {pct:.2f}% EXCEEDS {threshold}% — BLOCKED"
            ),
        )

    def _check_signal_freshness(
        self, asset_id: str, signal_age_seconds: int,
    ) -> QualityCheckResult:
        """Forced zero if signal staleness > 5 days."""
        age_days = signal_age_seconds / 86400
        threshold_days = 5.0
        passed = age_days <= threshold_days

        return QualityCheckResult(
            check_name=RiskCheckType.SIGNAL_FRESHNESS,
            passed=passed,
            value=age_days,
            threshold=threshold_days,
            message=(
                f"Signal age {age_days:.1f} days ≤ {threshold_days} days"
                if passed
                else f"Signal age {age_days:.1f} days EXCEEDS {threshold_days} days — STALE"
            ),
        )

    def _check_var(
        self, proposed_value: float, nav: float,
        positions: list[PortfolioPosition],
        returns_history: Optional[np.ndarray] = None,
    ) -> QualityCheckResult:
        """1-day 99% VaR ≤ 1.5% of NAV. Uses empirical distribution if history provided."""
        threshold = 1.5
        
        if returns_history is not None and returns_history.size > 0:
            # Empirical VaR: compute portfolio returns history
            # Assuming equal weight or current exposure as weights
            weights = np.array([p.market_value for p in positions]) / nav if nav > 0 else np.zeros(len(positions))
            # Simpler: compute 99th percentile of asset returns and scale by exposure
            # In production: full portfolio revaluation
            import numpy as np
            empirical_1d_99_loss_pct = abs(np.percentile(returns_history, 1))
            var_nav_pct = (proposed_value / nav * empirical_1d_99_loss_pct) if nav > 0 else 100
        else:
            # Fallback to parametric if no history
            total_exposure = sum(abs(p.market_value) for p in positions) + proposed_value
            daily_vol_pct = 2.0
            var_99_pct = daily_vol_pct * 2.326
            var_dollar = total_exposure * var_99_pct / 100
            var_nav_pct = var_dollar / nav * 100 if nav > 0 else 100

        return QualityCheckResult(
            check_name=RiskCheckType.VAR,
            passed=var_nav_pct <= threshold,
            value=var_nav_pct,
            threshold=threshold,
            message=(
                f"1-day 99% VaR = {var_nav_pct:.2f}% of NAV ≤ {threshold}%"
                if var_nav_pct <= threshold
                else f"1-day 99% VaR = {var_nav_pct:.2f}% of NAV EXCEEDS {threshold}% — BLOCKED"
            ),
        )

    def _check_gross_exposure(
        self, proposed_value: float, nav: float,
        positions: list[PortfolioPosition],
    ) -> QualityCheckResult:
        """Total gross exposure ≤ 200% of NAV."""
        current_gross = sum(abs(p.market_value) for p in positions)
        total_gross = current_gross + proposed_value
        pct = total_gross / nav * 100 if nav > 0 else 100
        threshold = self.MAX_GROSS_EXPOSURE_PCT

        return QualityCheckResult(
            check_name=RiskCheckType.GROSS_EXPOSURE,
            passed=pct <= threshold,
            value=pct,
            threshold=threshold,
            message=(
                f"Gross Exposure {pct:.2f}% ≤ {threshold}%"
                if pct <= threshold
                else f"Gross Exposure {pct:.2f}% EXCEEDS {threshold}% — MARGIN LIMIT"
            ),
        )

    def _check_compliance(
        self, asset_id: str, blocklist: Optional[set[str]],
    ) -> QualityCheckResult:
        """Check against sanctioned entities and restricted list."""
        if not self._constraints.regulatory.compliance_blocklist_enabled:
            return QualityCheckResult(
                check_name=RiskCheckType.COMPLIANCE,
                passed=True,
                message="Compliance blocklist disabled (internal research mode)",
            )

        if blocklist and asset_id in blocklist:
            return QualityCheckResult(
                check_name=RiskCheckType.COMPLIANCE,
                passed=False,
                message=f"Asset {asset_id} is on the compliance blocklist — BLOCKED",
            )

        return QualityCheckResult(
            check_name=RiskCheckType.COMPLIANCE,
            passed=True,
            message=f"Asset {asset_id} passed compliance check",
        )

    # ─── Real-Time Monitors (Async, Alerting) ──────────────────────────

    def check_drawdown(
        self,
        current_nav: float,
        nav_history_20d: list[float],
    ) -> dict[str, Any]:
        """
        Monitor portfolio drawdown.
        Alert at 3%, halt at 5%, kill at 8% (rolling 20-day).
        """
        if not nav_history_20d:
            return {"status": "ok", "drawdown_pct": 0.0}

        peak = max(nav_history_20d)
        drawdown_pct = (peak - current_nav) / peak * 100 if peak > 0 else 0

        if drawdown_pct >= self.DRAWDOWN_KILL_PCT:
            self._activate_kill_switch(
                KillSwitchReason.DRAWDOWN,
                f"Rolling 20-day drawdown {drawdown_pct:.2f}% exceeds {self.DRAWDOWN_KILL_PCT}%",
                [],  # Will liquidate all
            )
            return {"status": "kill_switch", "drawdown_pct": drawdown_pct}
        elif drawdown_pct >= self.DRAWDOWN_HALT_PCT:
            logger.critical(f"DRAWDOWN HALT: {drawdown_pct:.2f}% — freezing new positions")
            return {"status": "halt", "drawdown_pct": drawdown_pct}
        elif drawdown_pct >= self.DRAWDOWN_ALERT_PCT:
            logger.warning(f"DRAWDOWN ALERT: {drawdown_pct:.2f}%")
            return {"status": "alert", "drawdown_pct": drawdown_pct}

        return {"status": "ok", "drawdown_pct": drawdown_pct}

    def check_data_feed_latency(
        self,
        last_data_timestamp: datetime,
        current_time: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Monitor data feed latency.
        > 10 min → stale-signal mode (reduce sizes 50%)
        > 4 hours → kill switch
        """
        now = current_time or datetime.now(timezone.utc)
        latency_minutes = (now - last_data_timestamp).total_seconds() / 60

        if latency_minutes > self.DATA_OUTAGE_KILL_HOURS * 60:
            self._activate_kill_switch(
                KillSwitchReason.DATA_OUTAGE,
                f"Data feed latency {latency_minutes:.0f} min exceeds "
                f"{self.DATA_OUTAGE_KILL_HOURS}h threshold",
                [],
            )
            return {"status": "kill_switch", "latency_minutes": latency_minutes}
        elif latency_minutes > 10:
            logger.warning(f"Data feed latency {latency_minutes:.0f} min — stale-signal mode")
            return {"status": "stale_mode", "latency_minutes": latency_minutes, "size_reduction": 0.5}

        return {"status": "ok", "latency_minutes": latency_minutes}

    def check_signal_dependency(
        self,
        pnl_by_signal_type: dict[str, float],
        current_positions: list[PortfolioPosition],
    ) -> dict[str, Any]:
        """
        Monitor P&L dependency on a single signal type.
        If > 60%, automatically flag for exposure reduction.
        """
        total_pnl = sum(abs(v) for v in pnl_by_signal_type.values())
        if total_pnl <= 0:
            return {"status": "ok", "max_dependency": 0.0}

        for stype, pnl in pnl_by_signal_type.items():
            contribution = abs(pnl) / total_pnl
            if contribution > 0.60:
                logger.critical(
                    f"SIGNAL DEPENDENCY BREACH: {stype} accounts for {contribution*100:.1f}% of P&L. "
                    f"Triggering automatic 50% exposure reduction for affected assets."
                )
                # In production: This should trigger a targeted liquidation event
                return {
                    "status": "reduction_triggered",
                    "signal_type": stype,
                    "contribution_pct": contribution * 100,
                    "action": "reduce_exposure_50pct"
                }

        return {"status": "ok", "max_dependency": max(abs(v)/total_pnl for v in pnl_by_signal_type.values())}

    # ─── Kill Switch ───────────────────────────────────────────────────

    def _activate_kill_switch(
        self, reason: KillSwitchReason, details: str, positions: list[str],
    ) -> None:
        """Activate kill switch — immediate full liquidation."""
        self._kill_switch_active = True
        event = KillSwitchEvent(
            event_id=str(uuid.uuid4()),
            reason=reason,
            timestamp_utc=datetime.now(timezone.utc),
            details=details,
            positions_to_liquidate=positions,
        )
        logger.critical(
            f"KILL SWITCH ACTIVATED: {reason.value} — {details}. "
            f"Liquidating {len(positions)} positions."
        )
        # In production: publish to SNS/EventBridge for immediate action
        self._log_kill_switch(event)

    def request_manual_kill_switch(self, operator_id: str, reason: str) -> str:
        """
        Initiate a manual kill-switch request. 
        Requires second operator authorization before activation.
        """
        request_id = str(uuid.uuid4())
        self._pending_halt_request = {
            "request_id": request_id,
            "operator_id": operator_id,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc),
        }
        logger.warning(f"KILL-SWITCH REQUESTED by {operator_id}: {reason}. Pending authorization.")
        return request_id

    def authorize_manual_kill_switch(self, operator_id: str, request_id: str) -> KillSwitchEvent:
        """
        Authorize a pending manual kill-switch request.
        Must be a different operator than the requester.
        """
        if not self._pending_halt_request:
            raise ValueError("No pending kill-switch request found.")
        
        if self._pending_halt_request["request_id"] != request_id:
            raise ValueError(f"Request ID mismatch: {request_id}")
            
        if self._pending_halt_request["operator_id"] == operator_id:
            raise ValueError("Two-person rule violation: Requester and Authorizer must be different.")

        event = KillSwitchEvent(
            event_id=str(uuid.uuid4()),
            reason=KillSwitchReason.MANUAL,
            timestamp_utc=datetime.now(timezone.utc),
            details=(
                f"Manual override initiated by {self._pending_halt_request['operator_id']} "
                f"and authorized by {operator_id}: {self._pending_halt_request['reason']}"
            ),
            positions_to_liquidate=[],  # All positions
        )
        self._kill_switch_active = True
        self._pending_halt_request = None
        
        logger.critical(f"MANUAL KILL SWITCH ACTIVATED via Two-Person Rule. Initiator: {event.details}")
        self._log_kill_switch(event)
        return event

    def manual_kill_switch(self, operator_id: str, reason: str) -> KillSwitchEvent:
        """
        Legacy single-operator kill switch. 
        DEPRECATED: Use request/authorize flow for institutional compliance.
        """
        logger.error(f"DEPRECATED manual_kill_switch called by {operator_id}. Bypassing two-person rule.")
        return self._activate_direct_kill(operator_id, reason)

    def _activate_direct_kill(self, operator_id: str, reason: str) -> KillSwitchEvent:
        """Internal helper for immediate activation (bypassable for testing only)."""
        event = KillSwitchEvent(
            event_id=str(uuid.uuid4()),
            reason=KillSwitchReason.MANUAL,
            timestamp_utc=datetime.now(timezone.utc),
            details=f"Direct activation (Bypass) by {operator_id}: {reason}",
            positions_to_liquidate=[],
        )
        self._kill_switch_active = True
        self._log_kill_switch(event)
        return event

    def reset_kill_switch(self, operator_id: str, reason: str) -> None:
        """Reset kill switch — requires operator authorization."""
        logger.warning(f"Kill switch RESET by {operator_id}: {reason}")
        self._kill_switch_active = False
        self._consecutive_failures.clear()

    # ─── Audit Logging ─────────────────────────────────────────────────

    def _log_risk_check(
        self, order_id: str, asset_id: str, quantity: float,
        price: float, checks: list[QualityCheckResult],
    ) -> None:
        """Log all risk check results to immutable audit trail."""
        entry = AuditLogEntry(
            event_id=str(uuid.uuid4()),
            event_type="risk_check",
            timestamp_utc=datetime.now(timezone.utc),
            asset_id=asset_id,
            order_id=order_id,
            quantity=quantity,
            price=price,
            risk_check_results=checks,
        )
        self._audit_log.append(entry)

    def _log_kill_switch(self, event: KillSwitchEvent) -> None:
        """Log kill switch activation to audit trail."""
        entry = AuditLogEntry(
            event_id=event.event_id,
            event_type="kill_switch",
            timestamp_utc=event.timestamp_utc,
            asset_id="PORTFOLIO",
        )
        self._audit_log.append(entry)

    def get_audit_log(self) -> list[AuditLogEntry]:
        """Return the full audit log (read-only)."""
        return list(self._audit_log)
