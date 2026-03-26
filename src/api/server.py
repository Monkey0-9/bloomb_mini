from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio, json
from datetime import datetime, timezone

from src.live.aircraft  import fetch_aircraft, to_geojson, get_squawk_alerts, Aircraft
from src.live.thermal   import get_global_thermal
from src.live.vessels   import get_all_vessels, get_vessels_near, detect_dark_vessels
from src.live.conflicts import get_all_conflicts, get_chokepoint_data
from src.live.orbits    import get_all_eo_satellites
from src.live.market    import get_prices, get_ohlcv, get_options, get_earnings
from src.live.macro     import get_macro_snapshot, get_series
from src.live.news      import get_all_news, fetch_gdelt
from src.intelligence.swarm import run_swarm_simulation

_clients: list[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Background task: push live updates to all connected WebSocket clients
    asyncio.create_task(_live_push_loop())
    yield


app = FastAPI(title="SatTrade Intelligence Terminal v2", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])


async def _live_push_loop():
    """Push live aircraft + squawk alerts to all WebSocket clients every 10s."""
    while True:
        await asyncio.sleep(10)
        if not _clients:
            continue
        try:
            aircraft  = fetch_aircraft()
            squawks   = get_squawk_alerts()
            geojson   = to_geojson(aircraft)
            payload   = json.dumps({
                "type":    "LIVE_UPDATE",
                "ts":      datetime.now(timezone.utc).isoformat(),
                "aircraft":geojson,
                "squawks": squawks,
                "summary": geojson["meta"],
            })
            dead = []
            for ws in _clients:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                _clients.remove(ws)
        except Exception:
            pass


# ─── HEALTH ──────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status":  "live",
        "version": "2.0.0",
        "cost":    "$0.00/month",
        "keys":    "zero API keys",
        "sources": ["OpenSky","NASA FIRMS","NOAA AIS","Celestrak","UCDP","ACLED",
                    "USGS","yfinance","FRED CSV","GDELT","RSS feeds"],
        "ts":      datetime.now(timezone.utc).isoformat(),
    }


# ─── AIRCRAFT ────────────────────────────────────────────────────────────────
@app.get("/api/aircraft")
async def aircraft_all(category: str = ""):
    cats   = [category.upper()] if category else None
    data   = fetch_aircraft(cats)
    return to_geojson(data)

@app.get("/api/aircraft/military")
async def aircraft_military():
    return to_geojson(fetch_aircraft(["MILITARY"]))

@app.get("/api/aircraft/cargo")
async def aircraft_cargo():
    return to_geojson(fetch_aircraft(["CARGO"]))

@app.get("/api/aircraft/government")
async def aircraft_government():
    return to_geojson(fetch_aircraft(["GOVERNMENT"]))

@app.get("/api/aircraft/squawk")
async def squawk_alerts():
    return {"alerts": get_squawk_alerts(),
            "ts":     datetime.now(timezone.utc).isoformat()}


# ─── THERMAL ────────────────────────────────────────────────────────────────
@app.get("/api/thermal")
async def thermal_all(top_n: int = 100):
    clusters = get_global_thermal(top_n=top_n)
    return {
        "clusters": [
            {
                "id":          c.cluster_id,
                "lat":         c.lat,
                "lon":         c.lon,
                "country":     c.country,
                "name":        c.facility_name,
                "type":        c.facility_type,
                "frp_avg":     c.avg_frp,
                "frp_base":    c.baseline_frp,
                "sigma":       c.anomaly_sigma,
                "score":       c.signal_score,
                "signal":      c.signal,
                "reason":      c.signal_reason,
                "tickers":     c.tickers,
                "hotspots":    c.hotspot_count,
                "quality":     c.data_quality,
                "color": (
                    "#E24B4A" if c.anomaly_sigma > 1.5
                    else "#EF9F27" if c.anomaly_sigma > 0.5
                    else "#639922" if c.anomaly_sigma > -0.5
                    else "#378ADD"
                ),
            }
            for c in clusters
        ],
        "count": len(clusters),
        "source": "NASA FIRMS global CSV (zero key)",
        "ts":     datetime.now(timezone.utc).isoformat(),
    }


# ─── VESSELS ─────────────────────────────────────────────────────────────────
@app.get("/api/vessels")
async def vessels_all():
    vessels = get_all_vessels()
    dark    = detect_dark_vessels(vessels)
    return {
        "vessels": [
            {
                "mmsi":     v.mmsi,
                "name":     v.name,
                "lat":      v.lat,
                "lon":      v.lon,
                "sog":      v.sog,
                "heading":  v.heading,
                "type":     v.vessel_type_name,
                "type_code":v.vessel_type,
                "length":   v.length,
                "dark":     v.dark_vessel,
                "source":   v.source,
            }
            for v in vessels.values()
        ],
        "count":        len(vessels),
        "dark_vessels": len(dark),
        "source":       "NOAA Marine Cadastre (zero key)",
        "ts":           datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/vessels/near")
async def vessels_near(lat: float, lon: float, radius_km: float = 100.0):
    nearby = get_vessels_near(lat, lon, radius_km)
    return {
        "lat":         lat,
        "lon":         lon,
        "radius_km":   radius_km,
        "vessels":     [{"mmsi":v.mmsi,"name":v.name,"lat":v.lat,"lon":v.lon,
                          "type":v.vessel_type_name,"sog":v.sog} for v in nearby[:50]],
        "count":       len(nearby),
    }

@app.get("/api/vessels/dark")
async def dark_vessels():
    vessels = get_all_vessels()
    dark    = detect_dark_vessels(vessels)
    return {
        "dark_vessels": [
            {"mmsi":v.mmsi,"name":v.name,"lat":v.lat,"lon":v.lon,
             "type":v.vessel_type_name,"ais_gap_hours":v.ais_gap_hours}
            for v in dark
        ],
        "count": len(dark),
    }


# ─── CONFLICTS AND WAR ───────────────────────────────────────────────────────
@app.get("/api/conflicts")
async def conflicts_all(severity: str = ""):
    events = get_all_conflicts()
    if severity:
        events = [e for e in events if e.severity == severity.upper()]
    return {
        "events": [
            {
                "id":          e.event_id,
                "date":        e.event_date,
                "type":        e.event_type,
                "country":     e.country,
                "region":      e.region,
                "lat":         e.lat,
                "lon":         e.lon,
                "fatalities":  e.fatalities,
                "actor1":      e.actor1,
                "actor2":      e.actor2,
                "severity":    e.severity,
                "chokepoint":  e.chokepoint_impact,
                "tickers":     e.financial_tickers,
                "source":      e.source,
            }
            for e in events
        ],
        "count":           len(events),
        "critical":        sum(1 for e in events if e.severity == "CRITICAL"),
        "near_chokepoints":sum(1 for e in events if e.chokepoint_impact),
        "sources":         "UCDP + ACLED (zero key)",
        "ts":              datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/conflicts/chokepoints")
async def chokepoints():
    return {
        "chokepoints": get_chokepoint_data(),
        "ts":          datetime.now(timezone.utc).isoformat(),
    }


# ─── SATELLITES ──────────────────────────────────────────────────────────────
@app.get("/api/satellites")
async def satellites_all():
    orbits = get_all_eo_satellites()
    return {
        "satellites": [
            {
                "name":         o.name,
                "lat":          o.current.lat,
                "lon":          o.current.lon,
                "alt_km":       o.current.alt_km,
                "period_min":   o.period_min,
                "inclination":  o.inclination,
                "ground_track": [
                    {"lat":p.lat,"lon":p.lon,"alt_km":p.alt_km,"ts":p.ts}
                    for p in o.ground_track[::5]  # Every 5 min to reduce payload
                ],
            }
            for o in orbits
        ],
        "count":  len(orbits),
        "source": "Celestrak TLE (zero key)",
        "ts":     datetime.now(timezone.utc).isoformat(),
    }


# ─── MARKET DATA ─────────────────────────────────────────────────────────────
@app.get("/api/market/prices")
async def prices_endpoint(tickers: str = ""):
    t_list = [t.strip().upper() for t in tickers.split(",")] if tickers else None
    result = get_prices(t_list)
    return {
        "prices": {k: {
            "ticker":     q.ticker,
            "price":      q.price,
            "change_pct": q.change_pct,
            "volume":     q.volume,
            "high":       q.high,
            "low":        q.low,
        } for k, q in result.items()},
        "count":  len(result),
        "source": "yfinance (zero key)",
        "ts":     datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/market/chart/{ticker}")
async def chart_endpoint(ticker: str, period: str = "3mo"):
    ohlcv = get_ohlcv(ticker.upper(), period)
    if not ohlcv:
        raise HTTPException(404, f"No chart data for {ticker}")

    # Get thermal signals for this ticker
    thermal = get_global_thermal(top_n=50)
    sat_signals = [
        {
            "date":    c.detected_at[:10],
            "sigma":   c.anomaly_sigma,
            "signal":  c.signal,
            "name":    c.facility_name,
            "score":   c.signal_score,
        }
        for c in thermal
        if ticker.upper() in c.tickers
    ]

    # Get earnings
    earnings = get_earnings([ticker.upper()])

    return {
        "ticker":          ticker.upper(),
        "ohlcv":           ohlcv,
        "satellite_signals": sat_signals,
        "earnings":        earnings,
        "period":          period,
        "source":          "yfinance (zero key)",
    }

@app.get("/api/market/options/{ticker}")
async def options_endpoint(ticker: str):
    return get_options(ticker.upper())

@app.get("/api/market/earnings")
async def earnings_endpoint(tickers: str = "AAPL,MSFT,MT,ZIM,LNG,WMT,FDX,UPS"):
    t_list = [t.strip().upper() for t in tickers.split(",")]
    return {
        "earnings": get_earnings(t_list),
        "ts":       datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/market/screener")
async def screener(
    sector:     str   = "",
    min_change: float = -99.0,
    max_change: float =  99.0,
):
    prices = get_prices()
    results = [
        q for q in prices.values()
        if min_change <= q.change_pct <= max_change
        and (not sector or q.sector.lower() == sector.lower())
    ]
    results.sort(key=lambda q: abs(q.change_pct), reverse=True)
    return {"results": [
        {"ticker":q.ticker,"price":q.price,"change_pct":q.change_pct,"volume":q.volume}
        for q in results
    ], "count": len(results)}


# ─── MACRO ────────────────────────────────────────────────────────────────────
@app.get("/api/macro")
async def macro_all():
    return {
        "data":   get_macro_snapshot(),
        "source": "FRED CSV endpoint (zero key)",
        "ts":     datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/macro/{series_key}")
async def macro_series_endpoint(series_key: str, limit: int = 252):
    data = get_series(series_key.upper(), limit=limit)
    if not data:
        raise HTTPException(404, f"Series {series_key} not found")
    return {"series": series_key.upper(), "data": data, "source": "FRED CSV"}


# ─── NEWS ─────────────────────────────────────────────────────────────────────
@app.get("/api/news")
async def news_endpoint(category: str = "", limit: int = 50):
    items = get_all_news()
    if category:
        items = [i for i in items if i.category == category]
    return {
        "news": [
            {"title":i.title,"summary":i.summary,"url":i.url,
             "source":i.source,"category":i.category,"published":i.published}
            for i in items[:limit]
        ],
        "count": min(len(items), limit),
        "ts":    datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/news/search")
async def news_search(q: str = "shipping military conflict", limit: int = 25):
    items = fetch_gdelt(q, max_records=limit)
    return {
        "query": q,
        "articles": [
            {"title":i.title,"url":i.url,"source":i.source,"published":i.published}
            for i in items
        ],
        "count": len(items),
    }


# ─── INTELLIGENCE SUMMARY ────────────────────────────────────────────────────
@app.get("/api/intelligence")
async def intelligence_summary():
    """Complete world intelligence picture. Everything significant. Dynamic."""
    aircraft  = fetch_aircraft()
    thermal   = get_global_thermal(top_n=30)
    conflicts = get_all_conflicts()
    satellites= get_all_eo_satellites()
    squawks   = get_squawk_alerts()

    # All tickers affected across all intelligence sources
    all_tickers: set[str] = set()
    for c in thermal:   all_tickers.update(c.tickers)
    for e in conflicts: all_tickers.update(e.financial_tickers)
    for a in aircraft:  all_tickers.update(a.alert["watch"] if a.alert and "watch" in a.alert else [])

    threat_score = min(100, (
        len([c for c in thermal   if abs(c.anomaly_sigma) > 1.5]) * 2 +
        len([e for e in conflicts if e.severity == "CRITICAL"]) * 8 +
        len([e for e in conflicts if e.severity == "HIGH"])     * 4 +
        len(squawks) * 10
    ))

    return {
        "threat_score":      threat_score,
        "squawk_alerts":     squawks,
        "thermal_anomalies": len(thermal),
        "conflict_events":   len(conflicts),
        "critical_conflicts":sum(1 for e in conflicts if e.severity == "CRITICAL"),
        "military_aircraft": sum(1 for a in aircraft if a.category == "MILITARY"),
        "cargo_aircraft":    sum(1 for a in aircraft if a.category == "CARGO"),
        "eo_satellites":     len(satellites),
        "tickers_affected":  list(all_tickers)[:30],
        "top_thermal":       [
            {"name":c.facility_name,"lat":c.lat,"lon":c.lon,
             "sigma":c.anomaly_sigma,"signal":c.signal,"tickers":c.tickers}
            for c in thermal[:5]
        ],
        "top_conflicts":     [
            {"country":e.country,"severity":e.severity,"fatalities":e.fatalities,
             "chokepoint":e.chokepoint_impact,"tickers":e.financial_tickers}
            for e in conflicts[:5]
        ],
        "ts": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/intelligence/swarm")
async def swarm_intelligence():
    """MiroFish-inspired global trade flow prediction swarm."""
    return run_swarm_simulation()


# ─── WEBSOCKET ────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _clients.append(websocket)
    # Send immediate snapshot on connect
    try:
        aircraft = fetch_aircraft()
        await websocket.send_text(json.dumps({
            "type":    "CONNECTED",
            "aircraft":to_geojson(aircraft),
            "squawks": get_squawk_alerts(),
            "ts":      datetime.now(timezone.utc).isoformat(),
        }))
        while True:
            await asyncio.sleep(60)  # Keep-alive
    except WebSocketDisconnect:
        if websocket in _clients:
            _clients.remove(websocket)
    except Exception:
        if websocket in _clients:
            _clients.remove(websocket)
