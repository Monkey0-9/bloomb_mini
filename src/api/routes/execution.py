from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from src.api.orchestrator import SignalOrchestrator

router = APIRouter(prefix="/api/execution", tags=["trading"])

def get_orchestrator(request: Request):
    return request.app.state.orchestrator

@router.get("/account")
async def get_account_status(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    return await orchestrator.dispatch_task("execution", "GET_STATE", {})

@router.post("/trade")
async def execute_trade(payload: dict[str, Any] = Body(...), orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    """
    Institutional endpoint with pre-trade risk audit.
    """
    ticker = payload.get("ticker")
    qty = payload.get("qty", 1)
    side = payload.get("side", "BUY")
    notional = payload.get("notional", qty * 150.0) # Mock price if not provided

    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker required")

    # 1. Pre-Trade Risk Audit
    audit_params = {
        "order": {
            "ticker": ticker,
            "notional": notional,
            "side": side,
            "market_price": 150.0,
            "price": 150.0,
            "adv_30d": 100_000_000
        }
    }
    audit = await orchestrator.dispatch_task("risk", "RUN_AUDIT", audit_params)

    if not audit.get("passed"):
        return {
            "status": "REJECTED",
            "reason": "Risk limits exceeded",
            "audit_results": audit.get("results")
        }

    # 2. Execution
    execution_result = await orchestrator.dispatch_task(
        "execution",
        "EXECUTE_TRADE",
        {"ticker": ticker, "qty": qty, "side": side}
    )

    if "error" in execution_result:
        raise HTTPException(status_code=500, detail=execution_result["error"])

    return {
        "status": "FILLED",
        "execution": execution_result,
        "audit": audit
    }
