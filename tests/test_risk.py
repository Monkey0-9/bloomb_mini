import pytest
from src.risk.engine import RiskEngine, RiskGateResult

@pytest.fixture
def risk_engine():
    return RiskEngine()

def test_max_gross_exposure_gate(risk_engine):
    portfolio = {"gross_exposure": 1.4, "equity": 1000000}
    order = {"notional": 200000} # Would push gross to 1.6
    
    results = risk_engine.run_pre_trade_audit(order, portfolio)
    gross_gate = next(r for r in results if r.gate_name == "max_gross_exposure")
    assert gross_gate.passed is False

def test_kill_switch_impact(risk_engine):
    risk_engine.activate_kill_switch("Manual trigger")
    portfolio = {"gross_exposure": 0.5, "equity": 1000000}
    order = {"notional": 1000}
    
    results = risk_engine.run_pre_trade_audit(order, portfolio)
    assert any(r.gate_name == "kill_switch" and not r.passed for r in results)

def test_kill_switch_reset(risk_engine):
    risk_engine.activate_kill_switch("Test")
    risk_engine.reset_kill_switch("secret", witness_witness=True)
    assert risk_engine._kill_switch_active is False
