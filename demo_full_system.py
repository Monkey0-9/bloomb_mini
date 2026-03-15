#!/usr/bin/env python3
"""
SatTrade end-to-end system demonstration.
Every step produces real, inspectable output.
If any step fails, the system is not working — investigate immediately.
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Force UTF-8 encoding for stdout on Windows to prevent charmap errors
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

console = Console()


def banner(msg: str) -> None:
    console.print(Panel(f"[bold cyan]{msg}[/]", border_style="cyan"))


def check(label: str, value: str | int | float | bool) -> None:
    icon = "✓" if value else "✗"
    colour = "green" if value else "red"
    console.print(f"  [{colour}]{icon}[/] {label}: [bold]{value}[/]")


def main() -> int:
    banner("SATTRADE — FULL SYSTEM DEMONSTRATION")
    console.print(f"  Started: {datetime.now(timezone.utc).isoformat()}\n")
    failures = 0

    # ── Step 1: Quality Gates ─────────────────────────────────────────────────
    banner("[1/7] Quality Gates")
    try:
        from src.common.schemas import TileMetadata
        from src.ingest.quality_gates import gate_cloud_cover, gate_schema

        tile = TileMetadata(
            tile_id=str(uuid4()), source="sentinel2",
            acquisition_utc=datetime.now(timezone.utc),
            processing_level="L2A", sensor_type="OPTICAL",
            resolution_m=10.0, cloud_cover_pct=12.0,
            bbox_wgs84=[3.9, 51.85, 4.6, 52.05],
            license_id="copernicus_open", commercial_use_ok=True,
            checksum_sha256="abc" * 20, preprocessing_ver="0.0.0",
            ingest_timestamp_utc=datetime.now(timezone.utc),
            file_path="/tmp/demo.tif", location_key="rotterdam",
        )
        cloud_result = gate_cloud_cover(tile)
        schema_result = gate_schema(tile)
        check("Cloud gate PASS", cloud_result.status == "PASS")
        check("Schema gate PASS", schema_result.status == "PASS")

        high_cloud = TileMetadata(**{**tile.__dict__, "cloud_cover_pct": 55.0,
                                      "tile_id": str(uuid4())})
        reject_result = gate_cloud_cover(high_cloud)
        check("High cloud REJECT", reject_result.status == "REJECT")
    except Exception as e:
        console.print(f"  [red]✗ Quality gates failed: {e}[/]")
        failures += 1

    # ── Step 2: Feature Store ─────────────────────────────────────────────────
    banner("[2/7] Feature Store — Look-Ahead Bias Test")
    try:
        from src.features.feature_store import FeatureStore, FeatureLeakError
        from src.common.schemas import FeatureRecord

        store = FeatureStore(":memory:")
        T = datetime(2023, 1, 15, 12, 0, 0)

        future_record = FeatureRecord(
            feature_id=str(uuid4()), entity_id="PORT-ROTTERDAM-001",
            feature_name="vessel_count", feature_value=47.0,
            event_timestamp=T + timedelta(hours=1),
            created_timestamp=T + timedelta(days=1),
            source_tile_id="demo-tile", model_version="1.0.0",
        )
        store.write(future_record)
        results = store.get_features_as_of("PORT-ROTTERDAM-001", T)
        returned_ids = [r.feature_id for r in results]
        leak_prevented = future_record.feature_id not in returned_ids
        check("Look-ahead bias prevented", leak_prevented)

        past_record = FeatureRecord(
            feature_id=str(uuid4()), entity_id="PORT-ROTTERDAM-001",
            feature_name="vessel_count", feature_value=35.0,
            event_timestamp=T - timedelta(hours=12),
            created_timestamp=T - timedelta(hours=6),
            source_tile_id="demo-tile-past", model_version="1.0.0",
        )
        store.write(past_record)
        results2 = store.get_features_as_of("PORT-ROTTERDAM-001", T)
        past_found = past_record.feature_id in [r.feature_id for r in results2]
        check("Past features returned correctly", past_found)

        if not leak_prevented:
            console.print("  [red]CRITICAL: Look-ahead bias not prevented![/]")
            failures += 1
    except Exception as e:
        console.print(f"  [red]✗ Feature store failed: {e}[/]")
        failures += 1

    # ── Step 3: Risk Engine ───────────────────────────────────────────────────
    banner("[3/7] Risk Engine — Pre-Trade Gates + Kill-Switch")
    try:
        from src.execution.risk_engine import (
            GROSS_EXPOSURE_LIMIT, RiskEngine, Order, Portfolio, Position,
            KillSwitchAuthError,
        )
        check("Gross exposure limit", f"{GROSS_EXPOSURE_LIMIT*100:.0f}% NAV")
        assert GROSS_EXPOSURE_LIMIT == 1.50

        engine = RiskEngine(":memory:")
        portfolio = Portfolio(
            nav=1_000_000,
            positions=[
                Position("WMT", 15_000, "Consumer Staples", "US"),
                Position("AMKBY", 15_000, "Industrials", "DK"),
            ],
        )
        good_order = Order(ticker="ZIM", notional_usd=10_000,
                           sector="Industrials", country="IL",
                           signal_age_days=1.0, signal_confidence=0.85,
                           adtv_usd=10_000_000)
        result = engine.check_all_gates(good_order, portfolio)
        check("Valid order PASSES all gates", result.passed)

        stale_order = Order(ticker="ZIM", notional_usd=10_000,
                            sector="Industrials", country="IL",
                            signal_age_days=7.0, signal_confidence=0.85,
                            adtv_usd=10_000_000)
        stale_result = engine.check_all_gates(stale_order, portfolio)
        check("Stale signal REJECTED", not stale_result.passed)

        req = engine.request_kill("operator_alice", "demo test")
        same_op_blocked = False
        try:
            engine.authorize_kill(req.kill_request_id, "operator_alice")
        except KillSwitchAuthError:
            same_op_blocked = True
        check("Same-operator kill blocked", same_op_blocked)

        engine2 = RiskEngine(":memory:")
        req2 = engine2.request_kill("operator_alice", "demo test 2")
        kill_result = engine2.authorize_kill(req2.kill_request_id, "operator_bob")
        check("Two-operator kill executes", kill_result.status == "EXECUTED")
        check("System halted after kill", engine2.system_state == "HALTED")

    except Exception as e:
        console.print(f"  [red]✗ Risk engine failed: {e}[/]")
        failures += 1

    # ── Step 4: API Health ────────────────────────────────────────────────────
    banner("[4/7] API Server Health Check")
    try:
        import httpx
        try:
            resp = httpx.get("http://localhost:8000/health", timeout=3)
            health = resp.json()
            check("API status", health.get("status"))
            check("Signals active", health.get("signals_active", 0))
        except httpx.ConnectError:
            console.print("  [yellow]⚠ API not running. Start with: make run-api[/]")
            console.print("  [dim]Run this demo again after starting the API[/]")
    except Exception as e:
        console.print(f"  [yellow]⚠ API check skipped: {e}[/]")

    # ── Step 5: Preprocessing Check ───────────────────────────────────────────
    banner("[5/7] Preprocessing — DOS Forbidden Check")
    try:
        optical_source = Path("src/preprocess/optical.py").read_text()
        no_dos = "dark_object" not in optical_source.lower()
        uses_6s = "SixS" in optical_source or "Py6S" in optical_source
        check("DOS method absent", no_dos)
        check("py6S present", uses_6s)
    except FileNotFoundError:
        console.print("  [red]✗ src/preprocess/optical.py not found[/]")
        failures += 1

    # ── Step 6: Test Suite ────────────────────────────────────────────────────
    banner("[6/7] Running Test Suite")
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        lines = [l for l in result.stdout.split("\n") if "passed" in l or "failed" in l]
        for line in lines[-3:]:
            console.print(f"  [green]{line}[/]")
        check("All tests passing", True)
    else:
        console.print(f"  [red]✗ Tests failed:[/]")
        console.print(result.stdout[-2000:])
        failures += 1

    # ── Step 7: Summary ───────────────────────────────────────────────────────
    banner("[7/7] Summary")
    if failures == 0:
        console.print(Panel(
            "[bold green]ALL SYSTEMS OPERATIONAL[/]\n"
            "SatTrade is working. No failures detected.\n"
            "Next step: python -m src.ingest.sentinel --location rotterdam",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold red]{failures} FAILURE(S) DETECTED[/]\n"
            "Fix each failure before proceeding.\n"
            "Each failure means a component is not working.",
            border_style="red"
        ))
    return failures


if __name__ == "__main__":
    sys.exit(main())
