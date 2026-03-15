import pytest
from datetime import datetime, timezone, timedelta
from src.features.feature_store import FeatureStore, FeatureRecord

@pytest.fixture
def store():
    return FeatureStore()

def test_as_of_join_correctness(store):
    t0 = datetime(2023, 1, 1, tzinfo=timezone.utc)
    t1 = t0 + timedelta(hours=1)
    t2 = t0 + timedelta(hours=2)
    
    # Materialize features at different times
    store.materialize(FeatureRecord("F1", "signal", 10.0, t0, t0))
    store.materialize(FeatureRecord("F1", "signal", 20.0, t1, t1))
    
    # Query at t0.5 -> should get t0
    fv_half = store.get_features_as_of("F1", t0 + timedelta(minutes=30))
    assert fv_half.features["signal"] == 10.0
    
    # Query at t1.5 -> should get t1
    fv_one_half = store.get_features_as_of("F1", t0 + timedelta(minutes=90))
    assert fv_one_half.features["signal"] == 20.0
    
    # Query at t-1 -> should get nothing
    fv_none = store.get_features_as_of("F1", t0 - timedelta(minutes=1))
    assert "signal" not in fv_none.features

def test_lookahead_prevention(store):
    t0 = datetime(2023, 1, 1, tzinfo=timezone.utc)
    # Feature timestamp is t0, but created at t1 (future)
    t1 = t0 + timedelta(hours=1)
    store.materialize(FeatureRecord("F1", "signal", 10.0, t0, t1))
    
    # Query at t0 -> should NOT see the feature because it wasn't created yet
    fv = store.get_features_as_of("F1", t0)
    assert "signal" not in fv.features
    
    # Query at t1 -> should see it
    fv_later = store.get_features_as_of("F1", t1)
    assert fv_later.features["signal"] == 10.0
