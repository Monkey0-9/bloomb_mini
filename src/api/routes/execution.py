from fastapi import APIRouter, HTTPException, Body, Request, Depends
from typing import Dict, Any
from src.api.orchestrator import SignalOrchestrator

router = APIRouter(prefix="/api/execution", tags=["trading"])

def get_orchestrator(request: Request):
    return request.app.state.orchestrator

@router.get("/account")
async def get_account_status(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    return await orchestrator.dispatch_task("execution", "GET_STATE", {})

@router.post("/trade")
async def execute_trade(payload: Dict[str, Any] = Body(...), orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    """
    Institutional endpoint for manual or signal-triggered trades.
    """
    ticker = payload.get("ticker")
    qty = payload.get("qty", 1)
    side = payload.get("side", "BUY")
    
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker required")
        
    result = await orchestrator.dispatch_task("execution", "PLACE_ORDER", {"ticker": ticker, "qty": qty, "side": side})
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result
