from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from src.api.orchestrator import SignalOrchestrator
from typing import Any

router = APIRouter(prefix="/api/alpha", tags=["Alpha Intelligence"])

def get_orchestrator(request: Request):
    return request.app.state.orchestrator

@router.get("/signals")
async def get_signals(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    state = await orchestrator.get_unified_state()
    return state.get("signals", {})

@router.get("/thermal")
async def get_thermal_signals(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    # This will eventually be handled by a ThermalAgent
    from src.satellite.thermal import scan_industrial_facilities
    return {"data": scan_industrial_facilities(day_range=2), "source": "NASA-FIRMS-VIIRS"}

@router.get("/dark-vessels")
async def get_dark_vessels(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    result = await orchestrator.dispatch_task("maritime", "DETECT_ANOMALIES", {})
    return result

@router.get("/forecast/{ticker}")
async def get_forecast(ticker: str, orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    result = await orchestrator.dispatch_task("signals", "GET_FORECAST", {"ticker": ticker})
    return result

@router.get("/macro")
async def get_macro(indicator: str = "CPI", orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    # Federated query to the MacroAgent
    result = await orchestrator.dispatch_task("macro", "GET_CORRELATION", {"indicator": indicator})
    return result
@router.get("/news")
async def get_news(ticker: str = None, orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    result = await orchestrator.dispatch_task("news", "NEWS_BRIEF", {"ticker": ticker})
    # Transform for compatibility with frontend signalStore
    articles = result.get("articles", [])
    transformed = []
    for i, a in enumerate(articles):
        transformed.append({
            "id": i,
            "text": f"{a['title']} ({a['source']})",
            "time": datetime.now().strftime("%H:%M"),
            "url": a.get("link"),
            "content": a.get("content", "Content restricted. Authenticate with Bloomberg Terminal for full access."),
            "impact": "bullish" if a['sentiment'] > 0 else "bearish" if a['sentiment'] < 0 else "neutral"
        })
    return {"news": transformed}

@router.get("/satellites")
async def get_satellites(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    result = await orchestrator.dispatch_task("satellite", "GET_STATE", {})
    return result
