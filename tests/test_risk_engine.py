import pytest
from src.execution.risk_engine import (
    GROSS_EXPOSURE_LIMIT, KillSwitchAuthError, HaltedSystemError,
    Order, Portfolio, Position, RiskEngine,
)


def make_portfolio(nav: float = 1_000_000, exposure_pct: float = 0.5) -> Portfolio:
    return Portfolio(
        nav=nav,
        positions=[
            Position(ticker="WMT", notional_usd=nav * exposure_pct * 0.5,
                     sector="Consumer Staples", country="US"),
            Position(ticker="AMKBY", notional_usd=nav * exposure_pct * 0.5,
                     sector="Industrials", country="DK"),
        ],
    )


def make_order(**kwargs) -> Order:
    defaults = dict(
        ticker="ZIM", notional_usd=10_000, sector="Industrials",
        country="IL", signal_age_days=1.0, signal_confidence=0.85,
        adtv_usd=10_000_000,
    )
    defaults.update(kwargs)
    return Order(**defaults)


def test_gross_exposure_constant_is_150pct():
    """This test catches any accidental change to the exposure limit."""
    assert GROSS_EXPOSURE_LIMIT == 1.50, (
        "GROSS_EXPOSURE_LIMIT was changed from 1.50. "
        "This requires investment committee approval."
    )


def test_gross_exposure_gate_blocks_breach():
    engine = RiskEngine(":memory:")
    portfolio = make_portfolio(nav=1_000_000, exposure_pct=1.49)
    order = make_order(notional_usd=20_000)  # pushes over 150%
    result = engine.check_all_gates(order, portfolio)
    assert not result.passed
    assert result.failed_gate == "gross_exposure"


def test_gross_exposure_gate_passes_within_limit():
    engine = RiskEngine(":memory:")
    portfolio = make_portfolio(nav=1_000_000, exposure_pct=0.5)
    order = make_order(notional_usd=10_000)
    result = engine.check_all_gates(order, portfolio)
    assert result.passed


def test_kill_switch_requires_two_different_operators():
    engine = RiskEngine(":memory:")
    req = engine.request_kill("operator_alice", "drawdown breach test")
    with pytest.raises(KillSwitchAuthError, match="cannot authorize their own"):
        engine.authorize_kill(req.kill_request_id, "operator_alice")


def test_kill_switch_executes_with_two_operators():
    engine = RiskEngine(":memory:")
    req = engine.request_kill("operator_alice", "drawdown breach")
    result = engine.authorize_kill(req.kill_request_id, "operator_bob")
    assert result.status == "EXECUTED"
    assert engine.system_state == "HALTED"


def test_halted_system_rejects_all_orders():
    engine = RiskEngine(":memory:")
    engine.system_state = "HALTED"
    with pytest.raises(HaltedSystemError):
        engine.check_all_gates(make_order(), make_portfolio())


def test_stale_signal_blocks_order():
    engine = RiskEngine(":memory:")
    order = make_order(signal_age_days=6.0)
    result = engine.check_all_gates(order, make_portfolio())
    assert not result.passed
    assert result.failed_gate == "signal_staleness"


def test_low_confidence_blocks_order():
    engine = RiskEngine(":memory:")
    order = make_order(signal_confidence=0.35)
    result = engine.check_all_gates(order, make_portfolio())
    assert not result.passed
    assert result.failed_gate == "signal_confidence"
