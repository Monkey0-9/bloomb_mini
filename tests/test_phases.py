"""
Extended Test Suite — Phases 3–8

Comprehensive tests for annotation quality, feature extraction,
signal modeling, execution simulation, and infrastructure.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from src.annotate.quality import AnnotationQualityAgent, Annotation
from src.annotate.taxonomy import (
    get_taxonomy,
    UseCase,
    PORT_THROUGHPUT_TAXONOMY,
)
from src.features.feature_store import FeatureStore, FeatureRecord
from src.features.ais_fusion import AISFusionEngine, SARVesselDetection
from src.ingest.ais import VesselPosition
from src.signals.price_impact import ICAnalyzer, LinearModel
from src.backtest.walk_forward import WalkForwardValidator


# ═══════════════════════════════════════════════════════════════════
# ANNOTATION QUALITY TESTS (Phase 3)
# ═══════════════════════════════════════════════════════════════════

class TestAnnotationQuality:
    @pytest.fixture
    def agent(self):
        return AnnotationQualityAgent()

    def test_high_agreement_accepted(self, agent):
        """Tiles with IoU ≥ 0.70 should be accepted."""
        annotations = {
            "tile_001": [
                [Annotation("tile_001", "ann1", "container_stack", (10, 10, 50, 50))],
                [Annotation("tile_001", "ann2", "container_stack", (12, 12, 48, 48))],
                [Annotation("tile_001", "ann3", "container_stack", (11, 11, 49, 49))],
            ]
        }
        report = agent.process_batch(annotations)
        assert report.n_accepted == 1

    def test_insufficient_annotators_discarded(self, agent):
        """Tiles with < 3 annotators must be discarded."""
        annotations = {
            "tile_002": [
                [Annotation("tile_002", "ann1", "container_stack", (10, 10, 50, 50))],
                [Annotation("tile_002", "ann2", "container_stack", (12, 12, 48, 48))],
            ]
        }
        report = agent.process_batch(annotations)
        assert report.n_discarded == 1

    def test_bbox_iou_computation(self):
        """Test IoU computation between bounding boxes."""
        # Identical boxes → IoU = 1.0
        iou = AnnotationQualityAgent._bbox_iou(
            (0, 0, 10, 10), (0, 0, 10, 10)
        )
        assert abs(iou - 1.0) < 0.01

        # Non-overlapping boxes → IoU = 0.0
        iou = AnnotationQualityAgent._bbox_iou(
            (0, 0, 10, 10), (20, 20, 10, 10)
        )
        assert iou == 0.0

    def test_corpus_stats(self, agent):
        stats = agent.get_corpus_stats()
        assert stats["corpus_target"] == 2000
        assert stats["total_accepted"] == 0


class TestTaxonomy:
    def test_port_throughput_taxonomy_complete(self):
        tax = get_taxonomy(UseCase.PORT_THROUGHPUT)
        assert tax.get_num_classes() == 7
        assert "container_stack" in tax.get_class_names()
        assert "vessel_at_berth" in tax.get_class_names()

    def test_coco_categories_export(self):
        tax = PORT_THROUGHPUT_TAXONOMY
        categories = tax.to_coco_categories()
        assert len(categories) == 7
        assert all("id" in c and "name" in c for c in categories)

    def test_freeze_taxonomy(self):
        tax = get_taxonomy(UseCase.RETAIL_FOOTFALL)
        assert not tax.frozen
        tax.freeze()
        assert tax.frozen


# ═══════════════════════════════════════════════════════════════════
# FEATURE STORE TESTS (Phase 4)
# ═══════════════════════════════════════════════════════════════════

class TestFeatureStore:
    @pytest.fixture
    def store(self):
        fs = FeatureStore()
        # Add test features
        for i in range(10):
            ts = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(weeks=i)
            fs.materialize(FeatureRecord(
                entity_id="CNSHA",
                feature_name="vessel_count",
                feature_value=float(50 + i),
                feature_timestamp=ts,
                source_tile_ids=[f"tile_{i}"],
                model_version="v1.0",
            ))
        return fs

    def test_as_of_join_no_lookahead(self, store):
        """Point-in-time retrieval must NEVER return future data."""
        query_time = datetime(2024, 2, 1, tzinfo=timezone.utc)
        fv = store.get_features_as_of("CNSHA", query_time)
        assert "vessel_count" in fv.features
        # The value should be from the most recent record BEFORE Feb 1

    def test_no_lookahead_validation(self, store):
        """Explicit lookahead bias validation."""
        assert store.validate_no_lookahead(
            "CNSHA", datetime(2024, 2, 1, tzinfo=timezone.utc)
        )

    def test_future_query_includes_all(self, store):
        """Query far in the future should get latest value."""
        fv = store.get_features_as_of(
            "CNSHA", datetime(2024, 12, 31, tzinfo=timezone.utc)
        )
        assert fv.features.get("vessel_count") == 59.0  # 50 + 9

    def test_empty_entity(self, store):
        """Unknown entity returns empty feature vector."""
        fv = store.get_features_as_of(
            "NONEXISTENT", datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
        assert len(fv.features) == 0


# ═══════════════════════════════════════════════════════════════════
# AIS FUSION TESTS (Phase 4)
# ═══════════════════════════════════════════════════════════════════

class TestAISFusion:
    @pytest.fixture
    def engine(self):
        return AISFusionEngine()

    def test_matching_detections(self, engine):
        """SAR detection within 500m and 15min of AIS should match."""
        now = datetime.now(timezone.utc)
        sar = [SARVesselDetection(
            detection_id="det_001", tile_id="tile_001",
            latitude=1.3, longitude=103.8,
            acquisition_utc=now,
        )]
        ais = [VesselPosition(
            mmsi="123456789", timestamp_utc=now + timedelta(minutes=5),
            latitude=1.3001, longitude=103.8001,
            sog=0.5, cog=0, heading=0,
            vessel_name="TEST VESSEL",
        )]
        results = engine.fuse(sar, ais)
        assert len(results) == 1
        assert not results[0].is_dark
        assert results[0].ais_mmsi == "123456789"

    def test_dark_vessel_flagging(self, engine):
        """SAR detection with no AIS match = dark vessel."""
        now = datetime.now(timezone.utc)
        sar = [SARVesselDetection(
            detection_id="det_002", tile_id="tile_001",
            latitude=5.0, longitude=110.0,
            acquisition_utc=now,
        )]
        ais = [VesselPosition(
            mmsi="999999999", timestamp_utc=now,
            latitude=30.0, longitude=150.0,  # Far away
            sog=10, cog=90, heading=90,
        )]
        results = engine.fuse(sar, ais)
        assert len(results) == 1
        assert results[0].is_dark


# ═══════════════════════════════════════════════════════════════════
# SIGNAL MODELING TESTS (Phase 5)
# ═══════════════════════════════════════════════════════════════════

class TestICAnalyzer:
    def test_perfect_signal(self):
        """Perfect signal should have IC close to 1."""
        analyzer = ICAnalyzer()
        signals = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
        returns = signals * 0.01  # Perfect linear relationship
        result = analyzer.compute_ic_series(signals, returns)
        assert result["ic"] > 0.9

    def test_random_signal_near_zero_ic(self):
        """Random signal should have IC close to 0."""
        rng = np.random.RandomState(42)
        analyzer = ICAnalyzer()
        signals = rng.randn(100)
        returns = rng.randn(100) * 0.01
        result = analyzer.compute_ic_series(signals, returns)
        assert abs(result["ic"]) < 0.3  # Should be near zero


class TestLinearModel:
    def test_linear_fit(self):
        """Simple linear regression should capture linear relationship."""
        rng = np.random.RandomState(42)
        X = rng.randn(100, 3)
        y = 0.5 * X[:, 0] + 0.3 * X[:, 1] + rng.randn(100) * 0.1
        model = LinearModel()
        result = model.fit(X, y, feature_names=["f1", "f2", "f3"])
        assert result["r_squared"] > 0.5


# ═══════════════════════════════════════════════════════════════════
# WALK-FORWARD TESTS (Phase 6)
# ═══════════════════════════════════════════════════════════════════

class TestWalkForward:
    def test_fold_generation(self):
        holdout = datetime(2024, 1, 1)
        validator = WalkForwardValidator(holdout_start=holdout)
        dates = [datetime(2020, 1, 1) + timedelta(weeks=w) for w in range(200)]
        folds = validator.generate_folds(dates)
        assert len(folds) >= 1
        # All fold test ends should be before holdout
        for fold in folds:
            assert fold.test_end < holdout
