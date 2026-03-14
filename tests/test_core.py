"""
Test Suite for SatTrade.

Tests focus on the most critical invariants:
- Schema validation (data integrity)
- Quality gates (reject invalid data)
- Risk engine (pre-trade checks, kill switch)
- Signal scoring (staleness, normalisation)
- Backtesting (sacred rules enforcement)
- Drift detection (PSI computation)
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ═══════════════════════════════════════════════════════════════════════
# SCHEMA TESTS
# ═══════════════════════════════════════════════════════════════════════

from src.common.schemas import (
    BoundingBox,
    TileMetadata,
    SensorType,
    ProcessingLevel,
    QualityCheckResult,
    SignalRecord,
    IngestEvent,
    IngestStatus,
)


class TestBoundingBox:
    def test_valid_bbox(self):
        bbox = BoundingBox(west=100.0, south=1.0, east=104.0, north=5.0)
        assert bbox.west == 100.0
        assert bbox.north == 5.0

    def test_invalid_bbox_south_gte_north(self):
        with pytest.raises(ValueError, match="south.*must be.*north"):
            BoundingBox(west=100.0, south=5.0, east=104.0, north=1.0)

    def test_invalid_bbox_equal(self):
        with pytest.raises(ValueError):
            BoundingBox(west=100.0, south=5.0, east=104.0, north=5.0)


class TestTileMetadata:
    @pytest.fixture
    def valid_tile(self):
        return TileMetadata(
            tile_id="S2A_20240101_T48NUG",
            source="sentinel-2",
            acquisition_utc=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            cloud_cover_pct=15.0,
            sensor_type=SensorType.OPTICAL,
            resolution_m=10.0,
            bounding_box_wgs84=BoundingBox(west=100.0, south=1.0, east=104.0, north=5.0),
            license_id="copernicus_open_cc_by_sa_3_igo",
            commercial_use_permitted=True,
            processing_level=ProcessingLevel.L2A,
            checksum_sha256="a" * 64,
        )

    def test_valid_tile_creation(self, valid_tile):
        assert valid_tile.tile_id == "S2A_20240101_T48NUG"
        assert valid_tile.commercial_use_permitted is True

    def test_missing_tile_id(self):
        with pytest.raises(ValueError):
            TileMetadata(
                tile_id="",
                source="sentinel-2",
                acquisition_utc=datetime(2024, 1, 1, tzinfo=timezone.utc),
                cloud_cover_pct=15.0,
                sensor_type=SensorType.OPTICAL,
                resolution_m=10.0,
                bounding_box_wgs84=BoundingBox(west=100, south=1, east=104, north=5),
                license_id="test",
                commercial_use_permitted=True,
                processing_level=ProcessingLevel.L2A,
                checksum_sha256="a" * 64,
            )

    def test_naive_datetime_rejected(self):
        with pytest.raises(ValueError, match="timezone-aware"):
            TileMetadata(
                tile_id="test123",
                source="sentinel-2",
                acquisition_utc=datetime(2024, 1, 1, 12, 0, 0),  # No tzinfo!
                cloud_cover_pct=15.0,
                sensor_type=SensorType.OPTICAL,
                resolution_m=10.0,
                bounding_box_wgs84=BoundingBox(west=100, south=1, east=104, north=5),
                license_id="test",
                commercial_use_permitted=True,
                processing_level=ProcessingLevel.L2A,
                checksum_sha256="a" * 64,
            )

    def test_invalid_checksum(self):
        with pytest.raises(ValueError, match="valid hex"):
            TileMetadata(
                tile_id="test123",
                source="sentinel-2",
                acquisition_utc=datetime(2024, 1, 1, tzinfo=timezone.utc),
                cloud_cover_pct=15.0,
                sensor_type=SensorType.OPTICAL,
                resolution_m=10.0,
                bounding_box_wgs84=BoundingBox(west=100, south=1, east=104, north=5),
                license_id="test",
                commercial_use_permitted=True,
                processing_level=ProcessingLevel.L2A,
                checksum_sha256="not_a_hex_string_that_is_64_characters_long_xxxxxxxxxxxxxxxxxxxx",  # Exactly 64 chars
            )

    def test_cloud_cover_out_of_range(self):
        with pytest.raises(ValueError):
            TileMetadata(
                tile_id="test123",
                source="sentinel-2",
                acquisition_utc=datetime(2024, 1, 1, tzinfo=timezone.utc),
                cloud_cover_pct=150.0,  # > 100
                sensor_type=SensorType.OPTICAL,
                resolution_m=10.0,
                bounding_box_wgs84=BoundingBox(west=100, south=1, east=104, north=5),
                license_id="test",
                commercial_use_permitted=True,
                processing_level=ProcessingLevel.L2A,
                checksum_sha256="a" * 64,
            )


# ═══════════════════════════════════════════════════════════════════════
# QUALITY GATE TESTS
# ═══════════════════════════════════════════════════════════════════════

from src.ingest.quality_gates import QualityGates


class TestQualityGates:
    @pytest.fixture
    def gates(self):
        return QualityGates()

    @pytest.fixture
    def valid_tile(self):
        return TileMetadata(
            tile_id="S2A_test",
            source="sentinel-2",
            acquisition_utc=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            cloud_cover_pct=15.0,
            sensor_type=SensorType.OPTICAL,
            resolution_m=10.0,
            bounding_box_wgs84=BoundingBox(west=100.0, south=1.0, east=101.0, north=2.0),
            license_id="copernicus",
            commercial_use_permitted=True,
            processing_level=ProcessingLevel.L2A,
            checksum_sha256="b" * 64,
        )

    def test_valid_tile_passes_all_gates(self, gates, valid_tile):
        results = gates.run_all_checks(valid_tile)
        assert all(r.passed for r in results), (
            f"Failed checks: {[r.check_name for r in results if not r.passed]}"
        )

    def test_high_cloud_cover_rejected(self, gates, valid_tile):
        valid_tile.cloud_cover_pct = 50.0  # > 30%
        results = gates.run_all_checks(valid_tile)
        cloud_checks = [r for r in results if r.check_name == "cloud_cover"]
        assert len(cloud_checks) == 1
        assert not cloud_checks[0].passed

    def test_future_acquisition_rejected(self, gates, valid_tile):
        valid_tile.acquisition_utc = datetime(2099, 1, 1, tzinfo=timezone.utc)
        results = gates.run_all_checks(valid_tile)
        time_checks = [r for r in results if r.check_name == "acquisition_time"]
        assert len(time_checks) == 1
        assert not time_checks[0].passed

    def test_duplicate_lower_res_rejected(self, gates, valid_tile):
        existing = TileMetadata(
            tile_id="S2A_existing",
            source="sentinel-2",
            acquisition_utc=valid_tile.acquisition_utc,
            cloud_cover_pct=10.0,
            sensor_type=SensorType.OPTICAL,
            resolution_m=5.0,  # Higher res than the new tile (10m)
            bounding_box_wgs84=valid_tile.bounding_box_wgs84,
            license_id="copernicus",
            commercial_use_permitted=True,
            processing_level=ProcessingLevel.L2A,
            checksum_sha256="c" * 64,
        )
        results = gates.run_all_checks(valid_tile, existing_tiles=[existing])
        dup_checks = [r for r in results if r.check_name == "duplicate_detection"]
        assert len(dup_checks) == 1
        assert not dup_checks[0].passed  # New tile (10m) is lower res than existing (5m)


# ═══════════════════════════════════════════════════════════════════════
# SIGNAL SCORING TESTS
# ═══════════════════════════════════════════════════════════════════════

from src.execution.signal_scoring import (
    SignalScoringEngine,
    RawSignal,
    ScoredSignal,
)


class TestSignalScoring:
    @pytest.fixture
    def engine(self):
        return SignalScoringEngine()

    def test_empty_signals(self, engine):
        assert engine.score_batch([]) == []

    def test_stale_signal_forced_zero(self, engine):
        now = datetime.now(timezone.utc)
        signal = RawSignal(
            asset_id="MAERSK",
            signal_value=0.8,
            confidence=0.9,
            signal_timestamp=now - timedelta(days=10),  # 10 days old
            model_version="v1.0",
            gics_sector="2030",  # Transportation
            source_tile_ids=["tile1"],
        )
        results = engine.score_batch([signal], current_time=now)
        assert len(results) == 1
        assert results[0].is_stale is True
        assert results[0].scored_value == 0.0
        assert results[0].confidence_weight == 0.0

    def test_fresh_signal_non_zero(self, engine):
        now = datetime.now(timezone.utc)
        signals = [
            RawSignal(
                asset_id=f"ASSET_{i}",
                signal_value=float(i),
                confidence=0.9,
                signal_timestamp=now - timedelta(hours=6),
                model_version="v1.0",
                gics_sector="2030",
                source_tile_ids=["tile1"],
            )
            for i in range(5)
        ]
        results = engine.score_batch(signals, current_time=now)
        assert all(not r.is_stale for r in results)
        # Scored values should be in [-1, +1]
        assert all(-1.0 <= r.scored_value <= 1.0 for r in results)

    def test_staleness_decay(self, engine):
        half_life = engine.STALENESS_HALF_LIFE_DAYS
        decay = engine._compute_staleness_decay(half_life)
        assert abs(decay - 0.5) < 0.01  # Should be ~0.5 at half-life

    def test_winsorisation(self, engine):
        values = np.array([1.0] * 98 + [100.0, -100.0])  # Outliers
        result = engine._winsorise(values)
        # Outliers should be clipped
        assert max(result) < 100.0
        assert min(result) > -100.0


# ═══════════════════════════════════════════════════════════════════════
# RISK ENGINE TESTS
# ═══════════════════════════════════════════════════════════════════════

from src.execution.risk_engine import RiskEngine, PortfolioPosition


class TestRiskEngine:
    @pytest.fixture
    def engine(self):
        return RiskEngine()

    @pytest.fixture
    def sample_position(self):
        return PortfolioPosition(
            asset_id="MAERSK",
            quantity=100,
            market_value=50_000,  # 0.5% of $10M NAV
            gics_sector="2030",
            country="DK",
            adtv_30d=1_000_000,
            current_price=500.0,
        )

    def test_all_checks_pass(self, engine, sample_position):
        result = engine.run_pretrade_checks(
            asset_id="MAERSK",
            proposed_quantity=10,
            proposed_price=500.0,
            signal_age_seconds=3600,  # 1 hour old
            current_positions=[sample_position],
        )
        assert result.all_passed is True
        assert result.blocked is False

    def test_position_limit_exceeded(self, engine, sample_position):
        # Try to buy way too much — exceeds 2% NAV limit
        result = engine.run_pretrade_checks(
            asset_id="MAERSK",
            proposed_quantity=10_000,
            proposed_price=500.0,  # $5M = 50% of NAV
            signal_age_seconds=3600,
            current_positions=[sample_position],
        )
        assert result.all_passed is False
        assert result.blocked is True

    def test_stale_signal_blocked(self, engine, sample_position):
        result = engine.run_pretrade_checks(
            asset_id="MAERSK",
            proposed_quantity=10,
            proposed_price=500.0,
            signal_age_seconds=86400 * 10,  # 10 days old
            current_positions=[sample_position],
        )
        stale_checks = [c for c in result.checks if c.check_name == "signal_freshness"]
        assert len(stale_checks) == 1
        assert not stale_checks[0].passed

    def test_kill_switch_blocks_all(self, engine, sample_position):
        engine.manual_kill_switch("test_operator", "test reason")
        assert engine.is_killed is True

        result = engine.run_pretrade_checks(
            asset_id="MAERSK",
            proposed_quantity=10,
            proposed_price=500.0,
            signal_age_seconds=3600,
            current_positions=[sample_position],
        )
        assert result.all_passed is False
        assert result.blocked is True
        assert "KILL SWITCH" in result.block_reason

    def test_drawdown_kill_switch(self, engine):
        # 10% drawdown from peak should trigger kill switch
        nav_history = [10_000_000, 10_100_000, 10_200_000, 10_000_000]
        result = engine.check_drawdown(
            current_nav=9_300_000,  # ~8.8% drawdown from peak
            nav_history_20d=nav_history + [9_300_000],
        )
        assert result["status"] == "kill_switch"
        assert engine.is_killed is True


# ═══════════════════════════════════════════════════════════════════════
# BACKTESTING TESTS
# ═══════════════════════════════════════════════════════════════════════

from src.backtest.engine import BacktestConfig, BacktestEngine


class TestBacktestEngine:
    @pytest.fixture
    def config(self):
        return BacktestConfig(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2024, 12, 31),
            holdout_start=datetime(2023, 7, 1),
        )

    @pytest.fixture
    def engine(self, config):
        return BacktestEngine(config)

    def test_zero_cost_backtest_rejected(self):
        with pytest.raises(ValueError, match="zero costs is forbidden"):
            BacktestConfig(
                start_date=datetime(2020, 1, 1),
                end_date=datetime(2024, 12, 31),
                holdout_start=datetime(2023, 7, 1),
                commission_bps=0.0,
            )
            BacktestEngine(BacktestConfig(
                start_date=datetime(2020, 1, 1),
                end_date=datetime(2024, 12, 31),
                holdout_start=datetime(2023, 7, 1),
                commission_bps=0.0,
            ))

    def test_holdout_contamination_aborts(self, engine):
        T, N = 200, 5
        signals = np.random.randn(T, N)
        returns = np.random.randn(T, N) * 0.01

        # Include dates in holdout period
        dates = [
            datetime(2023, 8, 1) + timedelta(weeks=i) for i in range(T)
        ]

        with pytest.raises(ValueError, match="LOOKAHEAD_BIAS"):
            engine.run_backtest(signals, returns, dates)

    def test_valid_backtest_runs(self, engine):
        T, N = 100, 5
        signals = np.random.randn(T, N)
        returns = np.random.randn(T, N) * 0.01

        # All dates before holdout
        dates = [
            datetime(2020, 1, 1) + timedelta(weeks=i) for i in range(T)
        ]

        metrics = engine.run_backtest(signals, returns, dates)
        # Must have confidence intervals — single-point Sharpe is rejected
        assert metrics.sharpe_ratio_ci != (0.0, 0.0)
        assert metrics.annualised_return_ci != (0.0, 0.0)

    def test_benjamini_hochberg(self):
        p_values = [0.01, 0.04, 0.03, 0.20, 0.05]
        adjusted = BacktestEngine.benjamini_hochberg(p_values)
        # All adjusted p-values should be >= original
        for orig, adj in zip(p_values, adjusted):
            assert adj >= orig or abs(adj - orig) < 1e-10


# ═══════════════════════════════════════════════════════════════════════
# DRIFT DETECTION TESTS
# ═══════════════════════════════════════════════════════════════════════

from src.monitoring.dashboard import DriftDetector


class TestDriftDetection:
    def test_identical_distributions_low_psi(self):
        rng = np.random.RandomState(42)
        data = rng.normal(0, 1, 1000)
        psi = DriftDetector.compute_psi(data, data)
        assert psi < 0.1

    def test_shifted_distribution_high_psi(self):
        rng = np.random.RandomState(42)
        reference = rng.normal(0, 1, 1000)
        current = rng.normal(3, 1, 1000)  # Shifted by 3 sigma
        psi = DriftDetector.compute_psi(reference, current)
        assert psi > 0.2

    def test_drift_classification(self):
        assert DriftDetector.classify_drift(0.05) == "STABLE"
        assert DriftDetector.classify_drift(0.15) == "MODERATE_DRIFT"
        assert DriftDetector.classify_drift(0.30) == "SIGNIFICANT_DRIFT"


# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION TESTS
# ═══════════════════════════════════════════════════════════════════════

from src.common.config import load_constraints, validate_regulatory_gate


class TestConfig:
    def test_load_constraints(self):
        constraints = load_constraints()
        assert constraints.budget.cloud_compute_monthly_usd == 5000
        assert constraints.capital.simulated_nav_usd == 10_000_000
        assert constraints.regulatory.framework == "internal_research_only"
        assert constraints.capital.max_single_name_pct == 2.0

    def test_regulatory_gate_blocks_live_trading(self):
        with pytest.raises(PermissionError, match="REGULATORY GATE"):
            validate_regulatory_gate("live_order_submission")
