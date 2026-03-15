import pytest
from src.signals.facility_mapper import FacilityMapper

def test_mapper_retrieves_by_ticker():
    mapper = FacilityMapper()
    mappings = mapper.get_by_ticker("AMKBY")
    assert len(mappings) == 1
    assert mappings[0].facility_id == "PORT-ROTTERDAM-001"
    assert "Maersk" in mappings[0].causal_hypothesis

def test_mapper_filters_by_type():
    mapper = FacilityMapper()
    ports = mapper.get_all_by_type("PORT")
    assert len(ports) >= 3
    assert all(p.facility_type == "PORT" for p in ports)

def test_causal_hypothesis_not_empty():
    mapper = FacilityMapper()
    for m in mapper.INITIAL_MAPPINGS:
        assert len(m.causal_hypothesis) > 50
        assert m.lag_days_expected > 0
