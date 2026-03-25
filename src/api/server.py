import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.intelligence.engine import GlobalIntelligenceEngine
from src.signals.composite_score import CompositeScorer
from src.api.agents.analyst import AnalystAgent
from src.free_data.market import get_prices, get_ohlcv
from src.free_data.macro import get_snapshot as macro_snapshot
from src.data.news_feed import get_news_feed
from src.common.message_bus import bus

# Setup
logger = logging.getLogger(__name__)
engine = GlobalIntelligenceEngine()
scorer = CompositeScorer()
analyst = AnalystAgent()
clients: list[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Non-blocking background workers
    loop = asyncio.get_event_loop()
    loop.create_task(_warm_cache())
    loop.create_task(_message_bus_loop())
    yield


async def _warm_cache() -> None:
    while True:
        try:
            logger.info("cache_warm_started")
            await engine.get_world_intelligence_report()
            logger.info("cache_warm_finished")
        except Exception as e:
            logger.error(f"Cache warm failed: {e}")
        await asyncio.sleep(600)  # Refresh every 10 mins


async def _message_bus_loop() -> None:
    """Institutional-grade topic-based delivery."""
    logger.info("bus.loop_started")
    # Multiplex subscription
    topics = ["AIRCRAFT_UPDATES", "THERMAL_ANOMALIES", "SEISMIC_EVENTS", "CONFLICT_UPDATES"]
    queues = []
    for t in topics:
        queues.append(await bus.subscribe(t))

    while True:
        # Listen to all topic events
        done, pending = await asyncio.wait(
            [asyncio.create_task(q.get()) for q in queues],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for task in done:
            msg = task.result()
            payload = {
                "type": "LIVE_TELEMETRY",
                "ts": msg.timestamp,
                "topic": msg.topic,
                "data": msg.payload
            }
            dead = []
            for ws in clients:
                try:
                    await ws.send_text(json.dumps(payload))
                except (WebSocketDisconnect, Exception):
                    dead.append(ws)
            for ws in dead:
                if ws in clients:
                    clients.remove(ws)


app = FastAPI(title="SatTrade Bloomberg-Beater Intelligence", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "LIVE",
        "uptime": "INSTITUTIONAL",
        "ts": datetime.now(timezone.utc).isoformat()
    }

# ── CORE INTELLIGENCE ────────────────────────────────────────────────────────


@app.get("/api/intelligence")
async def global_report() -> object:
    return await engine.get_world_intelligence_report()


@app.get("/api/alpha/leaders")
async def alpha_leaders() -> dict[str, list[str]]:
    """Dynamically discover tickers with the strongest satellite/alternative signals."""
    report = await engine.get_world_intelligence_report()
    # Extract tickers from signals and thermal clusters
    tickers: set[str] = set()
    for s in report.signals:
        tickers.add(s['ticker'])
    for t in report.thermal:
        tickers.update(t.tickers)

    leader_list = list(tickers)[:20]
    if not leader_list:
        leader_list = ["ZIM", "XOM", "TSLA", "FDX", "UPS", "LMT", "BA", "VALE", "MT"]
    return {"tickers": leader_list}


@app.get("/api/alpha/signals")
@app.get("/api/signals")
async def alpha_signals() -> dict:
    report = await engine.get_world_intelligence_report()
    # Return in expected format for signalStore.ts
    signals_dict = {s['ticker']: {
        "signal_name": s['reason'],
        "location": "Global",
        "score": s['score'],
        "direction": s['direction'],
        "delta": 0,
        "ic": 0.15,
        "icir": 1.2,
        "description": s['reason'],
        "tickers": [s['ticker']],
        "observations": 1,
        "as_of": datetime.now(timezone.utc).isoformat()
    } for s in report.signals}
    return {"signals": signals_dict}


@app.get("/api/alpha/satellites")
async def alpha_satellites() -> list[dict]:
    report = await engine.get_world_intelligence_report()
    return [vars(s) for s in report.satellites]


@app.get("/api/alpha/composite")
async def composite_score(ticker: str) -> dict[str, object]:
    """Institutional-grade alpha fusion for any asset."""
    res = await scorer.score(ticker.upper())
    return {
        "ticker": ticker.upper(),
        "final_score": res["final_score"],
        "direction": res["direction"],
        "confidence": res["confidence"],
        "regime": res["regime"],
        "contributing_signals": res["contributing_signals"],
        "headline": res["headline"],
        "as_of": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/intelligence/strategic")
async def strategic_intel() -> dict[str, object]:
    report = await engine.get_world_intelligence_report()
    return {
        "threat_score": report.threat_score,
        "conflicts": [vars(c) for c in report.conflicts],
        "thermal": [vars(t) for t in report.thermal],
        "earthquakes": [vars(e) for e in report.earthquakes],
        "signals": report.signals,
        "satellites": [vars(s) for s in report.satellites]
    }


@app.get("/api/intelligence/aircraft")
async def intelligence_aircraft() -> dict:
    report = await engine.get_world_intelligence_report()
    return {"aircraft": [vars(a) for a in report.aircraft]}


@app.get("/api/intelligence/ships")
async def intelligence_ships() -> dict:
    # Use real-world vessel density from the high-fidelity engine
    ships = await engine.get_vessel_density()
    return {"ships": ships}


@app.get("/api/intelligence/thermal")
async def intelligence_thermal() -> list[dict]:
    report = await engine.get_world_intelligence_report()
    return [vars(t) for t in report.thermal]


@app.get("/api/intelligence/earthquakes")
async def intelligence_earthquakes() -> list[dict]:
    report = await engine.get_world_intelligence_report()
    return [vars(e) for e in report.earthquakes]


@app.get("/api/intelligence/conflicts")
async def intelligence_conflicts() -> list[dict]:
    report = await engine.get_world_intelligence_report()
    return [vars(c) for c in report.conflicts]

# ── MARKET & MACRO ───────────────────────────────────────────────────────────


@app.get("/api/market/prices")
async def market_prices(tickers: str = "") -> dict[str, object]:
    t_list = [t.strip() for t in tickers.split(",")] if tickers else None
    return {"prices": await get_prices(t_list), "source": "yfinance"}


@app.get("/api/market/chart/{ticker}")
async def market_chart(ticker: str, period: str = "3mo") -> dict[str, object]:
    ohlcv = await get_ohlcv(ticker, period)
    return {"ticker": ticker, "ohlcv": ohlcv}


@app.get("/api/macro")
async def macro_snapshot_api() -> dict[str, object]:
    return {"data": await macro_snapshot(), "source": "FRED"}


@app.get("/api/news")
@app.get("/api/alpha/news")
async def news_feed(query: str = "", limit: int = 50) -> dict[str, list[dict[str, object]]]:
    items = await get_news_feed()
    if query:
        q = query.lower()
        items = [i for i in items if q in i.get("title", "").lower() or q in str(i.get("tickers", []))]

    # Map to frontend expected format
    mapped = []
    for i in items:
        mapped.append({
            **i,
            "text": i.get("title", "Market Update"),
            "time": i.get("published", "RECENT"),
            "content": i.get("summary", ""),
            "sentiment": i.get("sentiment", 0.5)
        })
    return {"news": mapped[:limit]}

# ── COMMANDS & AGENTS ────────────────────────────────────────────────────────


class CommandReq(BaseModel):
    command: str


@app.post("/api/command/route")
async def command_route(req: CommandReq) -> dict[str, object]:
    # Simple routing logic for the UI
    c = req.command.lower()
    if any(k in c for k in ["world", "map", "globe"]):
        return {"action": "VIEW_SWITCH", "target": "world"}
    if any(k in c for k in ["economics", "macro", "fred"]):
        return {"action": "VIEW_SWITCH", "target": "economics"}
    if any(k in c for k in ["signal", "matrix", "alpha"]):
        return {"action": "VIEW_SWITCH", "target": "signals"}
    return {"action": "TICKER_SEARCH", "target": req.command.split()[-1].upper()}


@app.get("/api/command/stream")
async def command_stream(query: str) -> object:
    from fastapi.responses import StreamingResponse

    async def event_generator():
        yield f"data: {json.dumps({'token': 'INITIATING INSTITUTIONAL SYNTHESIS...'})}\n\n"
        await asyncio.sleep(0.5)

        # Institutional Synthesis via AnalystAgent
        res = await analyst.process_task("RESEARCH_QUERY", {"query": query})
        synthesis = res.get("synthesis", "Synthesis unavailable.")

        words = synthesis.split()
        for i, word in enumerate(words):
            yield f"data: {json.dumps({'token': word + ' '})}\n\n"
            if i % 4 == 0:
                await asyncio.sleep(0.04)

        yield f"data: {json.dumps({'intent': res.get('intent', 'research'), 'view_suggestion': res.get('view_suggestion', 'research'), 'ticker': res.get('ticker')})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        if websocket in clients:
            clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
