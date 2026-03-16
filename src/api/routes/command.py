from fastapi import APIRouter, HTTPException, Body, Depends, Request
from typing import Dict, Any
from src.api.orchestrator import SignalOrchestrator

router = APIRouter(prefix="/api/command", tags=["intelligence"])

def get_orchestrator(request: Request):
    return request.app.state.orchestrator

@router.post("/route")
async def route_command(payload: Dict[str, str] = Body(...), orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    """
    Entry point for the terminal's AI Command Palette.
    Routes natural language to intents, agents, and views.
    """
    prompt = payload.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing prompt")
        
    result = await orchestrator.dispatch_task("analyst", "RESEARCH_QUERY", {"query": prompt})
    return result

@router.get("/status")
async def get_analyst_status(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    result = await orchestrator.dispatch_task("analyst", "GET_STATE", {})
    return result
