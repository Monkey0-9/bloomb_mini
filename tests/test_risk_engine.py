import pytest
import asyncio
from src.risk.engine import RiskEngine, Position

@pytest.mark.asyncio
async def test_risk_engine_initialization():
    engine = RiskEngine()
    status = await engine.get_status()
    assert status["engine"] == "Monte Carlo VaR (10,000 sims)"
    assert status["gates"] == 9
    assert "kill_switch_active" in status

@pytest.mark.asyncio
async def test_position_pnl_calculation():
    # pnl_pct logic in engine.py: mult * (current - entry) / entry
    p = Position(ticker="AAPL", qty=100, entry_price=150.0, current_price=165.0, side="LONG")
    assert p.notional == 16500.0
    # mult=1, (165-150)/150 = 15/150 = 0.1
    assert round(p.pnl_pct, 2) == 0.10

    p_short = Position(ticker="TSLA", qty=50, entry_price=200.0, current_price=180.0, side="SHORT")
    assert p_short.notional == 9000.0
    # mult=-1, (180-200)/200 = -20/200 = -0.1. mult*-0.1 = 0.1
    assert round(p_short.pnl_pct, 2) == 0.10

@pytest.mark.asyncio
async def test_risk_engine_evaluate_trade():
    engine = RiskEngine()
    trade = {
        "ticker": "AAPL",
        "qty": 10,
        "price": 150.0,
        "side": "LONG",
        "user_id": "test_user"
    }
    result = await engine.evaluate_trade(trade)
    assert "overall" in result
    assert "gates" in result
    assert len(result["gates"]) == 9
