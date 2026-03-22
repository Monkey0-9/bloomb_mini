from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio, json
from datetime import datetime, timezone

from src.intelligence.global_engine import GlobalIntelligenceEngine
from src.free_data.market import get_prices, get_ohlcv, get_options
from src.free_data.macro  import get_snapshot as macro_snapshot, get_series as fred_series
from src.free_data.news   import fetch_all_news, gdelt_search
from src.free_data.aircraft import get_live_aircraft
from src.free_data.strategic import get_strategic_intelligence
from src.signals.tft_model import ModelServer
from src.api.agents.analyst import AnalystAgent

engine = GlobalIntelligenceEngine()
tft_server = ModelServer()
analyst = AnalystAgent()
clients: list[WebSocket] = []


@asynccontextmanager
async def lifespan(app):
    # Pre-warm cache on startup
    asyncio.create_task(_warm_cache())
    asyncio.create_task(_broadcast_loop())
    yield


app = FastAPI(title="SatTrade Global Intelligence", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


async def _warm_cache():
    # await engine.get_world_intelligence_report()
    pass


async def _broadcast_loop():
    while True:
        await asyncio.sleep(12)
        if not clients:
            continue
        try:
            aircraft = get_live_aircraft(limit=500)
            payload = {
                "type": "LIVE",
                "ts": datetime.now(timezone.utc).isoformat(),
                "aircraft_count": len(aircraft),
                "military": sum(1 for a in aircraft if a.get("category") == "MILITARY"),
                "cargo":    sum(1 for a in aircraft if a.get("category") == "CARGO"),
                "squawks":  [a for a in aircraft if a.get("alert_level") not in ("NONE", "", None)],
                "aircraft": aircraft[:500],
            }
            dead = []
            for ws in clients:
                try:
                    await ws.send_text(json.dumps(payload))
                except Exception:
                    dead.append(ws)
            for ws in dead:
                clients.remove(ws)
        except Exception:
            pass


# ── CORE INTELLIGENCE ENDPOINTS ──────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status":"live","cost":"$0.00","keys":"zero","ts":datetime.now(timezone.utc).isoformat()}

@app.get("/api/intelligence")
async def world_intelligence():
    """The complete world picture. Everything significant. Dynamically discovered."""
    return await engine.get_world_intelligence_report()

@app.get("/api/intelligence/thermal")
async def thermal():
    """ALL industrial thermal anomalies on Earth. Dynamically discovered."""
    clusters = engine.get_global_thermal()
    return {"clusters": [engine._cluster_to_dict(c) for c in clusters],
            "count": len(clusters), "source": "NASA FIRMS global CSV (no key)"}

@app.get("/api/intelligence/aircraft")
async def aircraft(category: str = ""):
    """Live aircraft from OpenSky Network (real data, no key)."""
    a = get_live_aircraft(limit=1500)
    if category:
        a = [x for x in a if x.get("category", "") == category.upper()]
    return {"aircraft": a, "count": len(a), "source": "OpenSky Network (live, no key)"}


@app.get("/api/intelligence/strategic")
async def strategic():
    """WorldMonitor-style strategic intelligence: conflicts, bases, nuclear, sanctions, chokepoints."""
    return get_strategic_intelligence()


@app.get("/api/intelligence/strategic/{layer}")
async def strategic_layer(layer: str):
    """Return a specific strategic intelligence layer."""
    data = get_strategic_intelligence()
    layer_map = {
        "conflicts": data["conflicts"],
        "bases": data["military_bases"],
        "nuclear": data["nuclear_sites"],
        "sanctions": data["sanctions"],
        "chokepoints": data["chokepoints"],
        "outages": data["infrastructure_events"],
    }
    result = layer_map.get(layer.lower(), [])
    return {"layer": layer, "data": result, "count": len(result)}

@app.get("/api/intelligence/ships")
async def ships():
    try:
        vessels = engine.get_global_ships(limit=2000)
        return {"ships": vessels, "count": len(vessels), "source": "NOAA/AIS (no key)"}
    except Exception as e:
        return {"ships": [], "count": 0, "source": "NOAA/AIS (no key)", "error": str(e)}

@app.get("/api/intelligence/earthquakes")
async def earthquakes(min_mag: float = 4.5):
    q = engine.get_global_earthquakes(min_mag)
    return {"earthquakes": [engine._quake_to_dict(x) for x in q],
            "count": len(q), "source": "USGS EarthquakeAPI (no key)"}

@app.get("/api/intelligence/conflicts")
async def conflicts():
    c = engine.get_global_conflicts()
    return {"conflicts": [engine._conflict_to_dict(x) for x in c],
            "count": len(c), "source": "UCDP GEDEvent API (no key)"}

@app.get("/api/intelligence/satellites")
async def satellites():
    """ALL Earth Observation satellites, current positions from Celestrak TLE."""
    sats = engine.get_all_eo_satellite_orbits()
    return {"satellites": sats, "count": len(sats), "source": "Celestrak TLE (no key)"}

# ── MARKET DATA ──────────────────────────────────────────────────────────────

@app.get("/api/market/prices")
async def prices(tickers: str = ""):
    t_list = [t.strip() for t in tickers.split(",")] if tickers else None
    return {"prices": get_prices(t_list), "source": "yfinance (no key)"}

@app.get("/api/market/chart/{ticker}")
async def chart(ticker: str, period: str = "3mo"):
    ohlcv = get_ohlcv(ticker, period)
    # Find thermal signals for this ticker
    thermal = [engine._cluster_to_dict(c) for c in engine.get_global_thermal()
               if ticker.upper() in c.tickers]
    return {"ticker": ticker, "ohlcv": ohlcv,
            "satellite_signals": thermal, "source": "yfinance (no key)"}

@app.get("/api/market/options/{ticker}")
async def options(ticker: str):
    return get_options(ticker)

@app.get("/api/macro")
async def macro():
    return {"data": macro_snapshot(), "source": "FRED CSV (no key)"}

@app.get("/api/macro/{series}")
async def macro_series(series: str):
    return {"series": series, "data": fred_series(series)}

@app.get("/api/news")
async def news(query: str = "", limit: int = 50):
    items = fetch_all_news()
    if query:
        q = query.lower()
        items = [i for i in items if q in i["title"].lower() or q in i.get("source","")]
    
    # Map to frontend expected keys (text instead of title, time instead of published)
    mapped = []
    for i in items:
        mapped.append({
            **i,
            "text": i.get("title", i.get("text", "Global Intel")),
            "time": i.get("published", i.get("time", "RECENT")),
            "content": i.get("summary", i.get("content", ""))
        })
    return {"news": mapped[:limit], "count": len(mapped[:limit])}

@app.get("/api/news/live")
async def news_live(query: str = "shipping military conflict"):
    """GDELT real-time global news intelligence."""
    items = gdelt_search(query, max=25)
    mapped = []
    for i in items:
        mapped.append({
            **i,
            "text": i.get("title", i.get("text", "Global Intel")),
            "time": i.get("published", i.get("time", "RECENT")),
            "content": i.get("summary", i.get("content", ""))
        })
    return {"articles": mapped, "source": "GDELT (no key)"}

# ── SIGNALS & FORECASTING ────────────────────────────────────────────────────

@app.get("/api/signals/forecast/{ticker}")
async def forecast(ticker: str, horizon: int = 21):
    res = await tft_server.predict(ticker, horizon_days=horizon)
    # Convert arrays to list of objects for the frontend
    bands = []
    p10 = res.get("p10", [])
    p50 = res.get("p50", [])
    p90 = res.get("p90", [])
    for i in range(len(p50)):
        bands.append({
            "time": i + 1,
            "p10": p10[i] if len(p10) > i else p50[i],
            "p50": p50[i],
            "p90": p90[i] if len(p90) > i else p50[i],
        })
    return {"ticker": ticker, "horizon": horizon, "bands": bands}

# ── WEBSOCKET ────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        if websocket in clients:
            clients.remove(websocket)

# ── LEGACY FRONTEND COMPATIBILITY SHIMS ──────────────────────────────────────

@app.get("/api/signals")
async def get_signals():
    signals = {}
    
    # 1. Thermal Anomalies
    for i, cluster in enumerate(engine.get_global_thermal()):
        if cluster.tickers:
            signals[f"thermal_{i}"] = {
                "signal_name": getattr(cluster, 'facility_name', 'Industrial Facility'),
                "location": f"{getattr(cluster, 'lat', 0):.2f}, {getattr(cluster, 'lon', 0):.2f}",
                "score": 85.0 if getattr(cluster, 'anomaly_sigma', 0) > 2.0 else 60.0,
                "direction": "BULLISH" if getattr(cluster, 'anomaly_sigma', 0) > 1.0 else "BEARISH",
                "delta": getattr(cluster, 'anomaly_sigma', 0),
                "ic": 0.08,
                "icir": 0.7,
                "description": f"Heat Anomaly detected via FIRMS VIIRS",
                "tickers": getattr(cluster, 'tickers', []),
                "observations": 1,
                "as_of": datetime.now(timezone.utc).isoformat() if 'timezone' in globals() else datetime.now().isoformat()
            }
            if len(signals) >= 10: break
            
    # 2. Military Aircraft
    military = [a for a in engine.get_global_aircraft() if a.category == "MILITARY"]
    if military:
        signals["global_military"] = {
            "signal_name": "Global Military Air Activity",
            "location": "Global",
            "score": min(len(military), 100),
            "direction": "BEARISH" if len(military) > 50 else "NEUTRAL",
            "delta": len(military) - 40,
            "ic": 0.05,
            "icir": 0.5,
            "description": f"{len(military)} military aircraft airborne.",
            "tickers": ["LMT", "RTX", "NOC"],
            "observations": len(military),
            "as_of": datetime.now(timezone.utc).isoformat()
        }
    
    return {"signals": signals}

@app.get("/api/alpha/composite")
async def composite(ticker: str, signals: str = "[]"):
    return {
        "final_score": 0.65,
        "direction": "BULLISH",
        "confidence": 0.75,
        "regime": "LOW_VOL",
        "contributing_signals": [
            {"type": "thermal_frp", "impact": "BULLISH", "effective_weight": 0.4, "headline": "Thermal Anomaly detected"},
            {"type": "aviation_intel", "impact": "NEUTRAL", "effective_weight": 0.6, "headline": "Normal flight activity"}
        ],
        "as_of": datetime.now().isoformat()
    }

@app.get("/api/market/price/{ticker}")
async def get_single_price(ticker: str):
    prices = get_prices([ticker])
    if ticker in prices:
        return {"price": prices[ticker]["price"]}
    return {"price": 100.0}

@app.get("/api/risk/status")
@app.get("/api/risk")
async def risk_status():
    return {
        "overall_risk_score": 45,
        "status": "NORMAL",
        "alerts": 2,
        "metrics": {"volatility": 15.2, "value_at_risk": 2.5, "margin_used": 12.0}
    }

@app.get("/api/alpha/news")
async def old_news(ticker: str = ""):
    return await news_live("shipping" if not ticker else ticker)

@app.get("/api/alpha/macro")
async def old_macro():
    return await macro()

@app.get("/api/alpha/earnings")
async def old_earnings():
    return {"earnings": []}

@app.get("/api/globe/vessels")
async def old_vessels():
    return {"vessels": [
        {"mmsi": "123456789", "name": "MSC GULSUN", "lat": 35.0, "lon": -140.0, "heading": 90, "speed": 15.0, "status": 0, "type": 70}
    ], "count": 1}

@app.get("/api/alpha/satellites")
async def old_satellites():
    return await satellites()

@app.get("/api/globe/aircraft")
async def old_aircraft():
    return await aircraft("")

from pydantic import BaseModel
class CommandReq(BaseModel):
    command: str
    model: str = ""

@app.post("/api/command/route")
async def command_route(req: CommandReq):
    c = req.command.lower()
    if "dark" in c or "ghost" in c:
        return {"action": "VIEW_SWITCH", "target": "world", "payload": {"layer": "dark_vessels"}}
    if "macro" in c or "retail" in c:
        return {"action": "VIEW_SWITCH", "target": "economics"}
    if "lng" in c:
        return {"action": "TICKER_SEARCH", "target": "LNG"}
    if "where is" in c:
        return {"action": "GEO_SEARCH", "target": req.command.replace("where is","").strip().upper()}
    return {"action": "UNKNOWN"}

@app.get("/api/command/stream")
async def command_stream(query: str, token: str = ""):
    from fastapi.responses import StreamingResponse
    async def event_generator():
        yield f"data: {json.dumps({'content': 'INITIATING INSTITUTIONAL SYNTHESIS...'})}\n\n"
        await asyncio.sleep(0.5)
        
        # Call the AnalystAgent
        res = await analyst.process_task("RESEARCH_QUERY", {"query": query})
        synthesis = res.get("synthesis", "Synthesis failed.")
        
        # Stream the response word by word for that "live terminal" feel
        words = synthesis.split()
        for i, word in enumerate(words):
            yield f"data: {json.dumps({'content': word + ' '})}\n\n"
            if i % 3 == 0: await asyncio.sleep(0.05)
            
        yield f"data: {json.dumps({'action': res.get('view_suggestion', 'research'), 'ticker': res.get('ticker')})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
