"""
All pre-trade risk gates are SYNCHRONOUS and BLOCKING.
An order that fails any gate never reaches the broker.
No exceptions to this rule. No overrides by individual operators.
"""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Final, Literal
from uuid import uuid4


GROSS_EXPOSURE_LIMIT: Final[float] = 1.50
# This constant is tested in CI. Changing it will break the test.
# Any change requires investment committee approval + code review sign-off.

SINGLE_NAME_LIMIT:    Final[float] = 0.02
SECTOR_LIMIT:         Final[float] = 0.15
COUNTRY_LIMIT:        Final[float] = 0.25
VAR_99_LIMIT:         Final[float] = 0.015
SIGNAL_MAX_AGE_DAYS:  Final[int]   = 5
MIN_CONFIDENCE:       Final[float] = 0.40


class KillSwitchAuthError(Exception):
    """Raised when same operator tries to both request and authorize a kill."""


class HaltedSystemError(Exception):
    """Raised when any order is attempted while system is HALTED."""


@dataclass
class Order:
    order_id: str = field(default_factory=lambda: str(uuid4()))
    ticker: str = ""
    notional_usd: float = 0.0
    sector: str = ""
    country: str = ""
    signal_age_days: float = 0.0
    signal_confidence: float = 1.0
    adtv_usd: float = 1_000_000.0


@dataclass
class Position:
    ticker: str
    notional_usd: float
    sector: str = ""
    country: str = ""


@dataclass
class Portfolio:
    nav: float
    positions: list[Position] = field(default_factory=list)

    @property
    def gross_exposure(self) -> float:
        return sum(abs(p.notional_usd) for p in self.positions)

    def sector_exposure(self, sector: str) -> float:
        return sum(abs(p.notional_usd) for p in self.positions
                   if p.sector == sector)

    def country_exposure(self, country: str) -> float:
        return sum(abs(p.notional_usd) for p in self.positions
                   if p.country == country)


@dataclass
class GateResult:
    status: Literal["PASS", "FAIL"]
    gate_name: str
    reason: str = ""


@dataclass
class RiskCheckResult:
    passed: bool
    order_id: str
    failed_gate: str | None = None
    reason: str | None = None


@dataclass
class KillRequest:
    kill_request_id: str = field(default_factory=lambda: str(uuid4()))
    requesting_operator: str = ""
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: Literal["PENDING", "EXECUTED", "CANCELLED"] = "PENDING"


@dataclass
class KillResult:
    status: Literal["EXECUTED", "FAILED"]
    kill_request_id: str
    authorized_by: str
    executed_at: datetime = field(default_factory=datetime.utcnow)


class RiskEngine:
    def __init__(self, audit_db: str = "data/audit.db") -> None:
        self.system_state: Literal["ACTIVE", "HALTED", "REDUCED"] = "ACTIVE"
        self._pending_kills: dict[str, KillRequest] = {}
        self.audit_db = audit_db
        Path(audit_db).parent.mkdir(parents=True, exist_ok=True)
        self._init_audit_db()

    def _init_audit_db(self) -> None:
        with sqlite3.connect(self.audit_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS risk_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    order_id TEXT,
                    gate_name TEXT,
                    result TEXT NOT NULL,
                    reason TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kill_requests (
                    kill_request_id TEXT PRIMARY KEY,
                    requesting_operator TEXT NOT NULL,
                    authorizing_operator TEXT,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    requested_at TEXT NOT NULL,
                    executed_at TEXT
                )
            """)
            conn.commit()

    def _log(self, event_type: str, result: str,
             order_id: str = "", gate_name: str = "", reason: str = "") -> None:
        with sqlite3.connect(self.audit_db) as conn:
            conn.execute(
                "INSERT INTO risk_events "
                "(event_type, order_id, gate_name, result, reason, timestamp) "
                "VALUES (?,?,?,?,?,datetime('now'))",
                (event_type, order_id, gate_name, result, reason),
            )
            conn.commit()

    def check_all_gates(self, order: Order, portfolio: Portfolio) -> RiskCheckResult:
        if self.system_state == "HALTED":
            raise HaltedSystemError(
                "System is HALTED. No orders permitted until restart is authorized."
            )
        gates = [
            (self.gate_signal_staleness, "signal_staleness"),
            (self.gate_signal_confidence, "signal_confidence"),
            (self.gate_liquidity, "liquidity"),
            (self.gate_single_name, "single_name"),
            (self.gate_sector, "sector"),
            (self.gate_country, "country"),
            (self.gate_gross_exposure, "gross_exposure"),
            (self.gate_var_parametric, "var_parametric"),
            (self.gate_compliance, "compliance"),
        ]
        for gate_fn, gate_name in gates:
            result: GateResult = gate_fn(order, portfolio)
            self._log("PRE_TRADE_CHECK", result.status,
                      order.order_id, gate_name, result.reason)
            if result.status == "FAIL":
                return RiskCheckResult(
                    passed=False, order_id=order.order_id,
                    failed_gate=gate_name, reason=result.reason,
                )
        return RiskCheckResult(passed=True, order_id=order.order_id)

    def gate_signal_staleness(self, order: Order, _: Portfolio) -> GateResult:
        if order.signal_age_days > SIGNAL_MAX_AGE_DAYS:
            return GateResult("FAIL", "signal_staleness",
                f"Signal {order.signal_age_days:.1f}d old > {SIGNAL_MAX_AGE_DAYS}d max. "
                "Force position to zero.")
        return GateResult("PASS", "signal_staleness")

    def gate_signal_confidence(self, order: Order, _: Portfolio) -> GateResult:
        if order.signal_confidence < MIN_CONFIDENCE:
            return GateResult("FAIL", "signal_confidence",
                f"Confidence {order.signal_confidence:.2f} < {MIN_CONFIDENCE} min.")
        return GateResult("PASS", "signal_confidence")

    def gate_liquidity(self, order: Order, _: Portfolio) -> GateResult:
        participation = abs(order.notional_usd) / max(order.adtv_usd, 1.0)
        if participation > 0.05:
            return GateResult("FAIL", "liquidity",
                f"Order is {participation*100:.1f}% of ADTV. Max: 5%.")
        return GateResult("PASS", "liquidity")

    def gate_single_name(self, order: Order, portfolio: Portfolio) -> GateResult:
        current = sum(abs(p.notional_usd) for p in portfolio.positions
                      if p.ticker == order.ticker)
        new_total = current + abs(order.notional_usd)
        if new_total / portfolio.nav > SINGLE_NAME_LIMIT:
            return GateResult("FAIL", "single_name",
                f"Would be {new_total/portfolio.nav*100:.1f}% of NAV. "
                f"Max: {SINGLE_NAME_LIMIT*100:.0f}%.")
        return GateResult("PASS", "single_name")

    def gate_sector(self, order: Order, portfolio: Portfolio) -> GateResult:
        current = portfolio.sector_exposure(order.sector)
        new_total = current + abs(order.notional_usd)
        if new_total / portfolio.nav > SECTOR_LIMIT:
            return GateResult("FAIL", "sector",
                f"Sector {order.sector}: would be "
                f"{new_total/portfolio.nav*100:.1f}% of NAV. "
                f"Max: {SECTOR_LIMIT*100:.0f}%.")
        return GateResult("PASS", "sector")

    def gate_country(self, order: Order, portfolio: Portfolio) -> GateResult:
        current = portfolio.country_exposure(order.country)
        new_total = current + abs(order.notional_usd)
        if new_total / portfolio.nav > COUNTRY_LIMIT:
            return GateResult("FAIL", "country",
                f"Country {order.country}: {new_total/portfolio.nav*100:.1f}% NAV. "
                f"Max: {COUNTRY_LIMIT*100:.0f}%.")
        return GateResult("PASS", "country")

    def gate_gross_exposure(self, order: Order, portfolio: Portfolio) -> GateResult:
        current = portfolio.gross_exposure
        new_total = current + abs(order.notional_usd)
        if new_total / portfolio.nav > GROSS_EXPOSURE_LIMIT:
            return GateResult("FAIL", "gross_exposure",
                f"Would breach {GROSS_EXPOSURE_LIMIT*100:.0f}% NAV limit. "
                f"Current: {current/portfolio.nav*100:.1f}%, "
                f"New: {new_total/portfolio.nav*100:.1f}%.")
        return GateResult("PASS", "gross_exposure")

    def gate_var_parametric(self, _order: Order, portfolio: Portfolio) -> GateResult:
        # Simplified parametric VaR: assume 1% daily vol per unit exposure
        gross = portfolio.gross_exposure / portfolio.nav
        estimated_var = gross * 0.01 * 2.326  # 99% z-score
        if estimated_var > VAR_99_LIMIT:
            return GateResult("FAIL", "var_parametric",
                f"Est. VaR 99% = {estimated_var*100:.2f}% NAV. "
                f"Max: {VAR_99_LIMIT*100:.1f}%.")
        return GateResult("PASS", "var_parametric")

    def gate_compliance(self, order: Order, _: Portfolio) -> GateResult:
        # Placeholder: in production, check against OFAC SDN list
        # For now: block any ticker that is in a hardcoded test list
        BLOCKED_TICKERS = {"SANCTIONS_TEST_TICKER"}
        if order.ticker in BLOCKED_TICKERS:
            return GateResult("FAIL", "compliance",
                f"{order.ticker} is on the compliance blocklist.")
        return GateResult("PASS", "compliance")

    # ── TWO-PERSON KILL-SWITCH ────────────────────────────────────────────────
    def request_kill(self, operator_id: str, reason: str) -> KillRequest:
        req = KillRequest(
            requesting_operator=operator_id,
            reason=reason,
        )
        self._pending_kills[req.kill_request_id] = req
        with sqlite3.connect(self.audit_db) as conn:
            conn.execute(
                "INSERT INTO kill_requests "
                "(kill_request_id, requesting_operator, reason, status, requested_at) "
                "VALUES (?,?,?,'PENDING',datetime('now'))",
                (req.kill_request_id, operator_id, reason),
            )
            conn.commit()
        return req

    def authorize_kill(
        self, kill_request_id: str, authorizing_operator_id: str
    ) -> KillResult:
        req = self._pending_kills.get(kill_request_id)
        if req is None:
            raise ValueError(f"Kill request {kill_request_id} not found.")

        if authorizing_operator_id == req.requesting_operator:
            raise KillSwitchAuthError(
                f"Operator {authorizing_operator_id} cannot authorize their own "
                "kill request. Two different operators are required."
            )

        self.system_state = "HALTED"
        result = KillResult(
            status="EXECUTED",
            kill_request_id=kill_request_id,
            authorized_by=authorizing_operator_id,
        )
        with sqlite3.connect(self.audit_db) as conn:
            conn.execute(
                "UPDATE kill_requests SET status='EXECUTED', "
                "authorizing_operator=?, executed_at=datetime('now') "
                "WHERE kill_request_id=?",
                (authorizing_operator_id, kill_request_id),
            )
            conn.commit()
        del self._pending_kills[kill_request_id]
        self._log("KILL_SWITCH_EXECUTED", "EXECUTED",
                  reason=f"Requested by {req.requesting_operator}, "
                         f"authorized by {authorizing_operator_id}: {req.reason}")
        return result
