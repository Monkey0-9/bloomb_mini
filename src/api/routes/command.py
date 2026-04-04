import json
import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from src.api.orchestrator import SignalOrchestrator

router = APIRouter(prefix="/api/command", tags=["intelligence"])

def get_orchestrator(request: Request):
    return request.app.state.orchestrator

@router.get("/stream")
async def stream_command(query: str, orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    """
    Server-Sent Events (SSE) endpoint for terminal streaming.
    """
    analyst = orchestrator.agents.get("analyst")
    if not analyst:
        raise HTTPException(404, "Analyst agent not found")

    async def event_generator():
        try:
            async for chunk in analyst.stream_research(query):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'content': f'!! SIGNAL ERROR: {str(e)}'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/route")
async def route_command(payload: dict[str, str] = Body(...), orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    """
    Entry point for the terminal's AI Command Palette.
    Routes natural language to intents, agents, and views.
    """
    prompt = payload.get("prompt") or payload.get("command")
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing prompt or command")

    result = await orchestrator.dispatch_task("analyst", "RESEARCH_QUERY", {"query": prompt})
    return result

@router.get("/status")
async def get_analyst_status(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    result = await orchestrator.dispatch_task("analyst", "GET_STATE", {})
    return result

@router.post("/godmode")
async def godmode_dispatch(payload: dict = Body(...), orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    """
    GodMode Dispatch: Simultaneously queries multiple intelligence agents.
    Inspired by smol-ai/GodMode.
    """
    query = payload.get("query")
    if not query:
        raise HTTPException(400, "Missing query")

    # Select core agents for GodMode view
    agent_names = ["analyst", "risk", "news", "maritime", "macro", "satellite", "thermal", "FUNDAMENTALS"]
    
    tasks = []
    active_agents = []
    for name in agent_names:
        if name in orchestrator.agents:
            active_agents.append(name)
            tasks.append(orchestrator.dispatch_task(name, "RESEARCH_QUERY", {"query": query}))
    
    if not tasks:
        raise HTTPException(404, "No suitable agents found for GodMode")

    results = await asyncio.gather(*tasks)
    
    return {
        "query": query,
        "responses": {name: res for name, res in zip(active_agents, results)},
        "timestamp": datetime.now(UTC).isoformat()
    }
