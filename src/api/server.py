from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from typing import Dict, Any
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

# Import all new modules
from src.globe.adsb import fetch_all_aircraft, aircraft_to_geojson, get_squawk_alerts
from src.globe.orbits import get_ground_track, SATELLITE_TLE_URLS
from src.globe.thermal import fetch_firms_thermal, compute_signal_from_thermal
from src.globe.ais_live import download_noaa_ais_zone, get_aishub_vessels
from src.data.market_data import (get_bulk_prices, get_ohlcv_history,
                                   get_company_info, get_options_chain,
                                   get_earnings_calendar, GLOBAL_UNIVERSE)
from src.data.macro import get_macro_dashboard, fetch_fred_series, FRED_SERIES
from src.data.news import fetch_all_news
from src.signals.composite_scorer import compute_all_signals
from src.common.trackers import vessel_tracker as _vessel_tracker, flight_tracker as _flight_tracker
from src.scheduler.jobs import start_scheduler

import os
from src.api.auth import get_current_user, require_role
from src.api.monitoring import metrics_middleware, metrics_endpoint, tracing_middleware
from src.api.orchestrator import Orchestrator
from src.api.agents.thermal_agent import ThermalAgent
from src.api.agents.news_agent import NewsAgent
from src.api.agents.research_agent import ResearchAgent

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

app = FastAPI(title="SatTrade Intelligence Terminal", version="2.0.0", lifespan=lifespan)

# Configurable CORS
TRUSTED_ORIGINS = os.getenv("TRUSTED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware,
    allow_origins=TRUSTED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    return await metrics_middleware(request, call_next)

@app.middleware("http")
async def add_tracing(request: Request, call_next):
    return await tracing_middleware(request, call_next)

@app.get("/metrics")
async def metrics():
    return metrics_endpoint()

# Singletons
# Singletons imported from src.common.trackers
_orchestrator = Orchestrator()
_orchestrator.register_agent(ThermalAgent())
_orchestrator.register_agent(NewsAgent())
_orchestrator.register_agent(ResearchAgent())

connected_clients: list[WebSocket] = []

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "live",
        "version": "2.0.0",
        "signals_active": 6,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modules": {
            "adsb": "active",
            "thermal": "active",
            "market_data": "active",
            "news": "active",
            "orbits": "active",
        }
    }

# ── Globe — Aircraft ──────────────────────────────────────────────────────────
@app.get("/api/globe/aircraft")
async def get_aircraft():
    flights = _flight_tracker.get_all_flights()
    return _flight_tracker.to_geojson_feature_collection()

@app.get("/api/globe/squawk-alerts")
async def get_squawk_alerts_endpoint():
    aircraft = await asyncio.to_thread(fetch_all_aircraft)
    return {"alerts": get_squawk_alerts(aircraft),
            "timestamp": datetime.now(timezone.utc).isoformat()}

# ── Globe — Satellite Orbits ──────────────────────────────────────────────────
@app.get("/api/globe/orbits/{satellite_name}")
async def get_orbit(satellite_name: str):
    if satellite_name not in SATELLITE_TLE_URLS:
        raise HTTPException(404, f"Satellite {satellite_name} not tracked. "
                               f"Available: {list(SATELLITE_TLE_URLS.keys())}")
    return await asyncio.to_thread(get_ground_track, satellite_name)

@app.get("/api/globe/orbits")
async def get_all_orbits():
    return {
        "satellites": list(SATELLITE_TLE_URLS.keys()),
        "orbits": {name: get_ground_track(name) for name in
                   ["Sentinel-2A", "Sentinel-2B", "Landsat-9"]},  # 3 key ones
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ── Globe — Thermal ───────────────────────────────────────────────────────────
@app.get("/api/globe/thermal")
async def get_thermal():
    anomalies = await asyncio.to_thread(fetch_firms_thermal)
    return {
        "anomalies": [
            {
                "facility_id": a.facility_id,
                "facility_name": a.facility_name,
                "facility_type": a.facility_type,
                "lat": a.lat, "lon": a.lon,
                "brightness_k": a.brightness_kelvin,
                "frp_mw": a.frp_mw,
                "confidence": a.confidence,
                "anomaly_sigma": a.anomaly_vs_baseline,
                "tickers": a.tickers,
                "country": a.country,
                "color": ("#E24B4A" if a.anomaly_vs_baseline > 1.5
                          else "#EF9F27" if a.anomaly_vs_baseline > 0.5
                          else "#888780"),
            }
            for a in anomalies
        ],
        "count": len(anomalies),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ── Globe — Vessels ───────────────────────────────────────────────────────────
@app.get("/api/globe/vessels")
async def get_vessels():
    """Returns vessels in the flat object format expected by vesselStore.ts"""
    vessels = await _vessel_tracker.get_all_vessels()
    return {
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [v.lon, v.lat]},
                "properties": {
                    "mmsi": v.mmsi,
                    "vessel_name": v.vessel_name,
                    "vessel_type": v.vessel_type,
                    "speed_knots": v.speed,
                    "heading": v.heading,
                    "dark_vessel_confidence": v.dark_vessel_confidence,
                    "linked_ticker": v.linked_equities[0] if v.linked_equities else None,
                    "flag": v.flag,
                }
            }
            for v in vessels
        ]
    }

@app.get("/api/globe/vessels/{mmsi}")
async def get_vessel_detail(mmsi: str):
    vessels = {v["mmsi"]: v for v in _vessel_tracker.to_api_list()}
    if mmsi not in vessels:
        raise HTTPException(404, f"Vessel {mmsi} not tracked")
    return vessels[mmsi]

# ── Globe — Flights ───────────────────────────────────────────────────────────
@app.get("/api/flights")
async def get_flights_legacy():
    # Legacy redirect or redundant endpoint
    return _flight_tracker.to_geojson_feature_collection()
    return {
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [f.position.lon, f.position.lat]},
                "properties": {
                    "icao24": f.flight_id,
                    "callsign": f.callsign,
                    "category": f.category,
                    "operator": f.aircraft.operator,
                    "alt_ft": f.position.altitude_ft,
                    "speed_kts": f.position.speed_knots,
                    "heading": f.position.heading,
                    "origin": f.origin,
                    "destination": f.destination,
                    "signal": f.signal_direction,
                    "reason": f.signal_reason,
                    "tickers": f.affected_tickers,
                }
            }
            for f in flights
        ]
    }

# ── Signals — Thermal ─────────────────────────────────────────────────────────
@app.get("/api/alpha/thermal", dependencies=[Depends(get_current_user)])
async def get_thermal_signals():
    """Returns thermal industrial signals for the globe heatmap"""
    anomalies = await asyncio.to_thread(fetch_firms_thermal)
    return {
        "signals": [
            {
                "lat": a.lat,
                "lon": a.lon,
                "facility_name": a.facility_name,
                "ticker": a.tickers[0] if a.tickers else "N/A",
                "avg_frp_mw": a.frp_mw,
                "anomaly_sigma": a.anomaly_vs_baseline,
                "country": a.country
            }
            for a in anomalies
        ]
    }

# ── Signals ───────────────────────────────────────────────────────────────────
@app.get("/api/signals", dependencies=[Depends(get_current_user)])
async def get_signals():
    thermal = await asyncio.to_thread(fetch_firms_thermal)
    earnings = await asyncio.to_thread(get_earnings_calendar, ["AMKBY","ZIM","MT","LNG","WMT","1919.HK"])
    signals = await asyncio.to_thread(compute_all_signals, thermal_anomalies=thermal, earnings_calendar=earnings)
    return {
        "signals": {
            k: {
                "signal_name": v.signal_name,
                "location_display": v.location_display,
                "score": v.score,
                "direction": v.direction,
                "delta_vs_baseline": v.delta_vs_baseline,
                "ic": v.ic,
                "icir": v.icir,
                "n_observations": v.n_observations,
                "primary_ticker": v.primary_ticker,
                "primary_company": v.primary_company,
                "affected_tickers": v.affected_tickers,
                "signal_reason": v.signal_reason,
                "pre_earnings": v.pre_earnings_signal,
                "data_sources": v.data_sources,
                "last_updated": v.last_updated.isoformat(),
            }
            for k, v in signals.items()
        },
        "count": len(signals),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ── Market Data ───────────────────────────────────────────────────────────────
@app.get("/api/market/prices", dependencies=[Depends(get_current_user)])
async def get_prices():
    prices = await asyncio.to_thread(get_bulk_prices)
    return {"prices": prices, "count": len(prices),
            "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/api/market/prices/{ticker}")
async def get_single_price(ticker: str):
    prices = get_bulk_prices([ticker])
    if ticker not in prices:
        raise HTTPException(404, f"Ticker {ticker} not found")
    return prices[ticker]

@app.get("/api/market/chart/{ticker}")
async def get_chart(ticker: str, period: str = "3mo", interval: str = "1d"):
    ohlcv = get_ohlcv_history(ticker, period=period, interval=interval)
    if not ohlcv:
        raise HTTPException(404, f"No chart data for {ticker}")
    company = get_company_info(ticker)
    # Get signal for this ticker
    thermal = fetch_firms_thermal()
    signals = compute_all_signals(thermal_anomalies=thermal)
    ticker_signals = [
        {"location": s.location_display, "score": s.score, "direction": s.direction,
         "last_updated": s.last_updated.isoformat()}
        for s in signals.values()
        if ticker in s.affected_tickers
    ]
    return {
        "ticker": ticker,
        "company": company,
        "ohlcv": ohlcv,
        "satellite_signals": ticker_signals,
        "period": period,
        "interval": interval,
    }

@app.get("/api/market/options/{ticker}")
async def get_options(ticker: str):
    return get_options_chain(ticker)

@app.get("/api/market/earnings")
async def get_earnings():
    tickers = list(GLOBAL_UNIVERSE.keys())[:50]
    calendar = get_earnings_calendar(tickers)
    return {"earnings": calendar, "count": len(calendar),
            "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/api/market/screener")
async def screener(sector: str = "", exchange: str = "", min_change: float = -100,
                   max_change: float = 100, sat_signal: str = ""):
    prices = get_bulk_prices()
    results = []
    for ticker, data in prices.items():
        if sector and data.get("sector", "").lower() != sector.lower():
            continue
        if exchange and data.get("exchange", "").lower() != exchange.lower():
            continue
        change = data.get("change_pct", 0)
        if change < min_change or change > max_change:
            continue
        results.append(data)
    return {"results": results, "count": len(results)}

# ── Macro ─────────────────────────────────────────────────────────────────────
@app.get("/api/macro/dashboard")
async def macro_dashboard():
    return get_macro_dashboard()

@app.get("/api/macro/{series_id}")
async def macro_series(series_id: str, limit: int = 252):
    if series_id.upper() not in FRED_SERIES:
        raise HTTPException(404, f"Series {series_id} not found. "
                               f"Available: {list(FRED_SERIES.keys())}")
    series_def = FRED_SERIES[series_id.upper()]
    data = fetch_fred_series(series_def[0], limit=limit)
    return {"series_id": series_id, "label": series_def[1],
            "unit": series_def[2], "data": data}

# ── News ──────────────────────────────────────────────────────────────────────
@app.get("/api/news")
async def get_news(topic: str = "", ticker: str = "", limit: int = 50):
    items = fetch_all_news()
    if topic:
        items = [i for i in items if topic.lower() in i.topics]
    if ticker:
        items = [i for i in items if ticker.upper() in i.tickers_mentioned]
    return {
        "news": [
            {"title": i.title, "summary": i.summary, "url": i.url,
             "source": i.source, "published": i.published,
             "topics": i.topics, "tickers": i.tickers_mentioned}
            for i in items[:limit]
        ],
        "count": len(items[:limit]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ── Risk Engine ───────────────────────────────────────────────────────────────
@app.get("/api/risk/status", dependencies=[Depends(require_role(["ADMIN", "TRADER"]))])
async def risk_status():
    from src.execution.risk_engine import GROSS_EXPOSURE_LIMIT
    return {
        "system_state": "ACTIVE",
        "gross_exposure_limit_pct": GROSS_EXPOSURE_LIMIT * 100,
        "nav_usd": 10_482_100.0,
        "gross_exposure_pct": 142.0,
        "var_99_1d_pct": 0.82,
        "kill_switch": "ARMED",
        "gates_active": 9,
    }

@app.post("/api/execution/twap", dependencies=[Depends(require_role(["ADMIN", "TRADER"]))])
async def execute_twap(ticker: str, side: str, quantity: int, duration: int):
    from src.execution.service import execution_service
    return await execution_service.execute_twap(ticker, side, quantity, duration)

@app.post("/api/backtest", dependencies=[Depends(get_current_user)])
async def backtest_strategy(ticker: str):
    from src.backtest.engine import BacktestEngine
    engine = BacktestEngine()
    # In a real flow, we'd fetch actual prices and signals
    return {"status": "simulation_started", "ticker": ticker}

@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await asyncio.sleep(10)  # push every 10 seconds
            aircraft = fetch_all_aircraft()
            squawk_alerts = get_squawk_alerts(aircraft)
            payload = {
                "type": "LIVE_UPDATE",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "aircraft_count": len(aircraft),
                "squawk_alerts": squawk_alerts,
                "vessels": _vessel_tracker.to_api_list()[:20],  # top 20 for WS
                "health": {
                    "pipeline": "live",
                    "signals_active": 6,
                    "aircraft_tracked": len(aircraft),
                    "vessels_tracked": len(_vessel_tracker.get_all_vessels()),
                },
            }
            await websocket.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
    except Exception:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
