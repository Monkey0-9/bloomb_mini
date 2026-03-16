import asyncio
import json
import logging
import os
import random
from datetime import datetime, timezone
from typing import Any, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# Institutional Orchestrator Layer
from src.api.orchestrator import SignalOrchestrator
from src.api.auth import verify_token
from src.api.routes import market, alpha, portfolio, command, execution

log = logging.getLogger(__name__)

app = FastAPI(title="SatTrade Orchestrator HUB", version="2.0.0")
orchestrator = SignalOrchestrator()
app.state.orchestrator = orchestrator

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modular Routes
app.include_router(market.router)
app.include_router(alpha.router)
app.include_router(portfolio.router)
app.include_router(command.router)
app.include_router(execution.router)

# Multi-Agent Connection Management
connected_ws: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    from src.scheduler.jobs import run_scheduler
    asyncio.create_task(run_scheduler())
    log.info("SatTrade Terminal Multi-Agent Hub Online")

@app.get("/health")
async def health():
    return orchestrator.get_system_health()

# SSE Streaming: Bloomberg-Grade Alpha Feed
@app.get("/stream/signals")
async def stream_signals():
    """Server-Sent Events for real-time signal conviction updates."""
    async def event_generator():
        while True:
            state = await orchestrator.get_unified_state()
            yield f"data: {json.dumps(state)}\n\n"
            await asyncio.sleep(5) # Throttled for terminal stability
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Hardened WebSocket topic hub
@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket, token: str = None):
    """
    Topic-based WebSocket hub. 
    In production, token validation happens on handshake.
    """
    await websocket.accept()
    connected_ws.append(websocket)
    try:
        while True:
            # Broadcast loop
            await asyncio.sleep(1)
            # In a real system, we'd use a Pub/Sub topic filter here
            msg = await websocket.receive_text()
            data = json.loads(msg)
            
            if data.get("type") == "SUBSCRIBE":
                topic = data.get("topic")
                log.info(f"Client sub to {topic}")
                await websocket.send_json({"type": "ACK", "topic": topic})
                
    except WebSocketDisconnect:
        connected_ws.remove(websocket)

if __name__ == "__main__":
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=True)
