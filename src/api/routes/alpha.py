import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, Request

from src.api.orchestrator import SignalOrchestrator

router = APIRouter(prefix="/api/alpha", tags=["Alpha Intelligence"])

def get_orchestrator(request: Request):
    return request.app.state.orchestrator

@router.get("/signals")
async def get_signals(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    state = await orchestrator.get_unified_state()
    return state.get("signals", {})

@router.get("/thermal")
async def get_thermal_signals(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    result = await orchestrator.dispatch_task("thermal", "RUN_SCAN", {})
    return result

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

@router.get("/earnings")
async def get_earnings_alpha(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    result = await orchestrator.dispatch_task("fundamentals", "GET_EARNINGS", {})
    return result

@router.get("/matrix")
async def get_alpha_matrix(orchestrator: SignalOrchestrator = Depends(get_orchestrator)):
    """Unified alpha matrix for the frontend dashboard."""
    from src.intelligence.swarm import run_swarm_simulation
    from src.live.thermal import get_global_thermal

    swarm_task = run_swarm_simulation()
    thermal_task = get_global_thermal(top_n=20)

    swarm, thermal = await asyncio.gather(swarm_task, thermal_task)

    rows = []
    # Swarm predictions
    for p in swarm.get("predictions", []):
        rows.append({
            "ticker": p.get("ticker") or p.get("region"),
            "direction": p.get("action"),
            "final_score": p.get("confidence", 0) / 100,
            "confidence": p.get("confidence", 0) / 100,
            "regime": "ACTIVE_SWARM",
            "as_of": datetime.now().isoformat(),
            "headline": p.get("prediction"),
            "source": "MiroFish Swarm"
        })

    # Thermal signals
    for t in thermal:
        ticker = t.tickers[0] if t.tickers else t.facility_name
        rows.append({
            "ticker": ticker,
            "direction": t.signal,
            "final_score": t.signal_score / 100,
            "confidence": abs(t.anomaly_sigma) / 4.0, # Normalised
            "regime": "THERMAL_DISCOVERY",
            "as_of": t.detected_at,
            "headline": t.signal_reason,
            "source": "NASA FIRMS"
        })

    return {"rows": sorted(rows, key=lambda x: x["final_score"], reverse=True)}
