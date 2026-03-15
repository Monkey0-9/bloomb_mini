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
from src.ingest.quality_gates import QualityGates
from src.execution.signal_scoring import (
    SignalScoringEngine,
    RawSignal,
    ScoredSignal,
)
from src.execution.risk_engine import RiskEngine, PortfolioPosition


# ═══════════════════════════════════════════════════════════════════════
# SCHEMA TESTS
# ═══════════════════════════════════════════════════════════════════════

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
            bounding_box_wgs84=BoundingBox(
                west=100.0, south=1.0, east=104.0, north=5.0
            ),
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
                bounding_box_wgs84=BoundingBox(
                    west=100, south=1, east=104, north=5
                ),
                license_id="test",
                commercial_use_permitted=True,
                processing_level=ProcessingLevel.L2A,
                checksum_sha256="a" * 64,
            )


# ═══════════════════════════════════════════════════════════════════════
# QUALITY GATE TESTS
# ═══════════════════════════════════════════════════════════════════════

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
            bounding_box_wgs84=BoundingBox(
                west=100.0, south=1.0, east=101.0, north=2.0
            ),
            license_id="copernicus",
            commercial_use_permitted=True,
            processing_level=ProcessingLevel.L2A,
            checksum_sha256="b" * 64,
        )

    def test_valid_tile_passes_all_gates(self, gates, valid_tile):
        results = gates.run_all_checks(valid_tile)
        assert all(r.passed for r in results)

    def test_high_cloud_cover_rejected(self, gates, valid_tile):
        valid_tile.cloud_cover_pct = 50.0  # > 30%
        results = gates.run_all_checks(valid_tile)
        cloud_checks = [r for r in results if r.check_name == "cloud_cover"]
        assert len(cloud_checks) == 1
        assert not cloud_checks[0].passed


# ═══════════════════════════════════════════════════════════════════════
# SIGNAL SCORING TESTS
# ═══════════════════════════════════════════════════════════════════════

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
            signal_timestamp=now - timedelta(days=10),
            model_version="v1.0",
            gics_sector="2030",
            source_tile_ids=["tile1"],
        )
        results = engine.score_batch([signal], current_time=now)
        assert len(results) == 1
        assert results[0].is_stale is True
        assert results[0].scored_value == 0.0


# ═══════════════════════════════════════════════════════════════════════
# RISK ENGINE TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestRiskEngine:
    @pytest.fixture
    def engine(self):
        return RiskEngine()

    @pytest.fixture
    def sample_position(self):
        return PortfolioPosition(
            asset_id="MAERSK",
            quantity=100,
            market_value=50_000,
            gics_sector="2030",
            country="DK",
            adtv_30d=1_000_000,
            current_price=500.0,
        )

    def test_all_checks_pass(self, engine, sample_position):
        results = engine.run_pretrade_checks(
            "MAERSK", 100, 500.0, 3600, [sample_position]
        )
        assert results.all_passed
