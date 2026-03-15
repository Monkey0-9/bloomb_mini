import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.features.feature_store import (
    DuplicateFeatureError, FeatureLeakError, FeatureStore,
    HOLDOUT_START_DATE, HoldoutAccessError,
)
from src.common.schemas import FeatureRecord


def make_record(entity_id="PORT-ROTTERDAM-001",
                feature_name="vessel_count",
                feature_value=47.0,
                event_dt: datetime | None = None,
                created_dt: datetime | None = None) -> FeatureRecord:
    base = datetime(2023, 1, 15, 12, 0, 0)
    return FeatureRecord(
        feature_id=str(uuid4()),
        entity_id=entity_id,
        feature_name=feature_name,
        feature_value=feature_value,
        event_timestamp=event_dt or base,
        created_timestamp=created_dt or (base + timedelta(hours=6)),
        source_tile_id="test-tile-001",
        model_version="1.0.0",
    )


def test_look_ahead_bias_is_prevented():
    """THE MOST IMPORTANT TEST IN THE ENTIRE CODEBASE."""
    store = FeatureStore(":memory:")
    T = datetime(2023, 1, 15, 12, 0, 0)

    future_record = make_record(
        event_dt=T + timedelta(hours=1),
        created_dt=T + timedelta(days=1),  # created ONE DAY AFTER T
    )
    store.write(future_record)

    results = store.get_features_as_of("PORT-ROTTERDAM-001", T)
    returned_ids = [r.feature_id for r in results]

    assert future_record.feature_id not in returned_ids, (
        "CRITICAL: Future feature was returned for a past query. "
        "This is look-ahead bias -- all backtest results are invalid."
    )


def test_past_features_are_returned():
    store = FeatureStore(":memory:")
    T = datetime(2023, 1, 15, 12, 0, 0)

    past_record = make_record(
        event_dt=T - timedelta(hours=12),
        created_dt=T - timedelta(hours=6),  # created 6 hours before T
    )
    store.write(past_record)

    results = store.get_features_as_of("PORT-ROTTERDAM-001", T)
    assert past_record.feature_id in [r.feature_id for r in results]


def test_duplicate_feature_id_raises():
    store = FeatureStore(":memory:")
    record = make_record()
    store.write(record)
    with pytest.raises(DuplicateFeatureError):
        store.write(record)


def test_holdout_access_is_blocked_for_training():
    store = FeatureStore(":memory:", is_holdout=False)
    with pytest.raises(HoldoutAccessError):
        store.get_features_as_of(
            "PORT-ROTTERDAM-001",
            HOLDOUT_START_DATE + timedelta(days=1)  # inside holdout period
        )


def test_feature_filter_by_name():
    store = FeatureStore(":memory:")
    T = datetime(2023, 1, 15, 12, 0, 0)
    r1 = make_record(feature_name="vessel_count",
                     event_dt=T - timedelta(hours=2),
                     created_dt=T - timedelta(hours=1))
    r2 = make_record(feature_name="crane_count",
                     event_dt=T - timedelta(hours=2),
                     created_dt=T - timedelta(hours=1))
    store.write(r1)
    store.write(r2)

    results = store.get_features_as_of(
        "PORT-ROTTERDAM-001", T, feature_names=["vessel_count"]
    )
    names = [r.feature_name for r in results]
    assert "vessel_count" in names
    assert "crane_count" not in names
