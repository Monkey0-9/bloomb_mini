from fastapi import APIRouter, Depends, HTTPException, Request
from src.api.orchestrator import SignalOrchestrator
from typing import Any
import os
import alpaca_trade_api as tradeapi
import asyncio

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio Management"])

def get_orchestrator(request: Request):
    return request.app.state.orchestrator

@router.get("/nav")
async def get_nav(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    api_key = os.environ.get("ALPACA_API_KEY")
    api_secret = os.environ.get("ALPACA_SECRET_KEY")
    base_url = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    
    if not api_key or not api_secret:
        return {"status": "NOT_CONNECTED", "message": "Alpaca API Key missing."}
    
    try:
        api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')
        account = await asyncio.to_thread(api.get_account)
        return {
            "status": "CONNECTED",
            "nav_usd": float(account.equity),
            "buying_power": float(account.buying_power),
            "as_of": account.created_at.isoformat()
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@router.get("/risk")
async def get_risk(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    state = await orchestrator.get_unified_state()
    return state.get("risk", {})
