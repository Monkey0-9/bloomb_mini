"""
Configuration loader for SatTrade.

Loads hard constraints and environment configuration from YAML files.
All downstream modules reference constraints through this module — never
hardcode budget, NAV, or regulatory parameters.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _find_project_root() -> Path:
    """Walk up from this file to find the project root (contains pyproject.toml)."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root (no pyproject.toml found)")


PROJECT_ROOT = _find_project_root()
CONFIG_DIR = PROJECT_ROOT / "config"


@dataclass(frozen=True)
class BudgetConfig:
    cloud_compute_monthly_usd: int = 5000
    data_license_monthly_usd: int = 2000


@dataclass(frozen=True)
class InfrastructureConfig:
    cloud_provider: str = "aws"
    region: str = "us-east-1"
    data_sovereignty_notes: str = ""


@dataclass(frozen=True)
class RegulatoryConfig:
    framework: str = "internal_research_only"
    live_trading_permitted: bool = False
    audit_log_retention_years: int = 7
    compliance_blocklist_enabled: bool = False


@dataclass(frozen=True)
class CapitalConfig:
    simulated_nav_usd: int = 10_000_000
    max_single_name_pct: float = 2.0
    max_sector_pct: float = 15.0
    max_country_pct: float = 25.0
    max_gross_exposure_pct: float = 150.0
    min_liquidity_adtv_pct: float = 5.0


@dataclass(frozen=True)
class UptimeConfig:
    signal_pipeline_sla_pct: float = 99.5
    batch_job_max_lag_hours: int = 6


@dataclass(frozen=True)
class Constraints:
    """Top-level hard constraints container. Immutable after loading."""

    budget: BudgetConfig = field(default_factory=BudgetConfig)
    infrastructure: InfrastructureConfig = field(default_factory=InfrastructureConfig)
    regulatory: RegulatoryConfig = field(default_factory=RegulatoryConfig)
    capital: CapitalConfig = field(default_factory=CapitalConfig)
    uptime: UptimeConfig = field(default_factory=UptimeConfig)


def _build_dataclass(cls: type, data: dict[str, Any]) -> Any:
    """Build a dataclass instance from a dict, ignoring unknown keys."""
    import dataclasses

    valid_fields = {f.name for f in dataclasses.fields(cls)}
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    return cls(**filtered)


def load_constraints(path: Path | None = None) -> Constraints:
    """
    Load hard constraints from YAML.

    Priority:
      1. Explicit path argument
      2. SATTRADE_CONSTRAINTS_PATH environment variable
      3. Default: config/constraints.yaml relative to project root

    Raises FileNotFoundError if no constraints file is found.
    """
    if path is None:
        env_path = os.environ.get("SATTRADE_CONSTRAINTS_PATH")
        if env_path:
            path = Path(env_path)
        else:
            path = CONFIG_DIR / "constraints.yaml"

    if not path.exists():
        raise FileNotFoundError(f"Constraints file not found: {path}")

    with open(path, encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    return Constraints(
        budget=_build_dataclass(BudgetConfig, raw.get("budget", {})),
        infrastructure=_build_dataclass(InfrastructureConfig, raw.get("infrastructure", {})),
        regulatory=_build_dataclass(RegulatoryConfig, raw.get("regulatory", {})),
        capital=_build_dataclass(CapitalConfig, raw.get("capital", {})),
        uptime=_build_dataclass(UptimeConfig, raw.get("uptime", {})),
    )


# ── Singleton access ──────────────────────────────────────────────────────────
_CONSTRAINTS: Constraints | None = None


def get_constraints() -> Constraints:
    """Return cached constraints singleton. Thread-safe for reads after first call."""
    global _CONSTRAINTS
    if _CONSTRAINTS is None:
        _CONSTRAINTS = load_constraints()
    return _CONSTRAINTS


def validate_regulatory_gate(action: str) -> None:
    """
    Halt execution if the requested action violates the regulatory framework.

    Example:
        validate_regulatory_gate("live_order_submission")
        # Raises if framework != SEC/MiFID and live_trading_permitted is False
    """
    c = get_constraints()
    if action == "live_order_submission" and not c.regulatory.live_trading_permitted:
        raise PermissionError(
            f"REGULATORY GATE VIOLATION: Action '{action}' is not permitted "
            f"under framework '{c.regulatory.framework}'. "
            f"live_trading_permitted = {c.regulatory.live_trading_permitted}"
        )
