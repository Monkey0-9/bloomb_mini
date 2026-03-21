import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Ingestion & Tools
from src.globe.adsb import fetch_all_aircraft, get_squawk_alerts
from src.globe.orbits import get_ground_track, SATELLITE_TLE_URLS
from src.globe.thermal import fetch_firms_thermal
from src.data.market_data import (get_bulk_prices, get_ohlcv_history,
                                   get_company_info, get_options_chain,
                                   get_earnings_calendar, GLOBAL_UNIVERSE)
from src.data.macro import get_macro_dashboard, fetch_fred_series, FRED_SERIES
from src.data.news import fetch_all_news
from src.signals.composite_scorer import compute_all_signals
from src.common.trackers import vessel_tracker, flight_tracker
from src.scheduler.jobs import start_scheduler

# Core Services
from src.api.auth import get_current_user, require_role
from src.api.monitoring import metrics_middleware, metrics_endpoint, tracing_middleware
from src.api.orchestrator import Orchestrator
from src.api.agents.thermal import ThermalAgent
from src.api.agents.news import NewsAgent
from src.api.agents.analyst import AnalystAgent
from src.api.agents.maritime import MaritimeAgent
from src.api.agents.macro import MacroAgent
from src.api.agents.risk import RiskAgent
from src.api.agents.execution import ExecutionAgent
from src.api.agents.flight import FlightAgent
from src.api.agents.satellite import SatelliteAgent
from src.api.routes import alpha, market, execution, portfolio, command
from src.risk.engine import RiskEngine

# Elite Broadcast Tier
from src.api.broadcast import broadcast_manager
from src.api.ticker import run_ticker

# Rate Limiter for Top 0.1% protection
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    # Initialize SQLite tables if they don't exist
    from src.db.session import init_db
    await init_db()
    
    # Start the AIS maritime pipeline (Live AISStream.io)
    from src.globe.ais import run_ais_pipeline
    asyncio.create_task(run_ais_pipeline(lambda x: None)) # Populates fleet_state

    # Start the central live broadcast ticker (One producer, many consumers)
    asyncio.create_task(run_ticker())
    start_scheduler()
    yield

app = FastAPI(title="SatTrade Intelligence Terminal", version="2.0.0", lifespan=lifespan)
app.state.limiter = limiter

# Initialize and register Orchestrator
_orchestrator = Orchestrator()
_orchestrator.register_agent(ThermalAgent())
_orchestrator.register_agent(NewsAgent())
_orchestrator.register_agent(AnalystAgent())
_orchestrator.register_agent(MaritimeAgent())
_orchestrator.register_agent(MacroAgent())
_orchestrator.register_agent(RiskAgent())
_orchestrator.register_agent(ExecutionAgent())
_orchestrator.register_agent(FlightAgent())
_orchestrator.register_agent(SatelliteAgent())

app.state.orchestrator = _orchestrator

# Include Routers
app.include_router(alpha.router)
app.include_router(market.router)
app.include_router(execution.router)
app.include_router(portfolio.router)
app.include_router(command.router)

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurable CORS
ALLOWED_HOSTS = os.getenv("TRUSTED_ORIGINS", "http://localhost:3000,http://localhost:5173")
TRUSTED_ORIGINS = ALLOWED_HOSTS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=TRUSTED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.middleware("http")
async def add_metrics(request: Request, call_next: Any) -> Any:
    return await metrics_middleware(request, call_next)

@app.middleware("http")
async def add_tracing(request: Request, call_next: Any) -> Any:
    return await tracing_middleware(request, call_next)

@app.on_event("startup")
async def startup_event():
    start_scheduler()
    import structlog
    log = structlog.get_logger()
    log.info("startup_complete", host="0.0.0.0", port=8000)

@app.get("/metrics")
async def metrics() -> Any:
    return metrics_endpoint()

# Singletons
_risk_engine = RiskEngine()

connected_clients: list[WebSocket] = []

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health() -> dict[str, Any]:
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

# ── Globe — Orbits ────────────────────────────────────────────────────────────
@app.get("/api/globe/orbits")
async def get_orbits() -> dict[str, Any]:
    orbits = {name: get_ground_track(name) for name in SATELLITE_TLE_URLS.keys()}
    return {
        "satellites": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [o["current_position"]["lon"], o["current_position"]["lat"]] if o.get("current_position") else [0,0]},
                    "properties": {
                        "id": name,
                        "name": name,
                        "category": "EO",
                        "owner": "ESA/USGS",
                        "altitude": "786km",
                        "velocity": "7.5km/s",
                        "orbit": "SSO",
                        "symbol": "🛰️",
                        "color": "#00FF41"
                    }
                }
                for name, o in orbits.items()
            ]
        }
    }

# ── Globe — Thermal ───────────────────────────────────────────────────────────
@app.get("/api/globe/thermal")
async def get_thermal() -> dict[str, Any]:
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
async def get_vessels() -> dict[str, Any]:
    """Returns vessels in the flat object format expected by vesselStore.ts"""
    vessels = await vessel_tracker.get_all_vessels()
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
async def get_vessel_detail(mmsi: str) -> Any:
    vessels_list = await vessel_tracker.get_all_vessels()
    vessels = {v.mmsi: v for v in vessels_list}
    if mmsi not in vessels:
        raise HTTPException(404, f"Vessel {mmsi} not tracked")
    return vessels[mmsi]

# ── Globe — Flights ───────────────────────────────────────────────────────────
@app.get("/api/flights")
async def get_flights_legacy() -> Any:
    # Legacy redirect or redundant endpoint
    return flight_tracker.to_geojson_feature_collection()

# ── Signals — Thermal ─────────────────────────────────────────────────────────
@app.get("/api/alpha/thermal")
async def get_thermal_signals() -> dict[str, Any]:
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
@app.get("/api/signals")
async def get_signals() -> dict[str, Any]:
    thermal = await asyncio.to_thread(fetch_firms_thermal)
    earnings = await asyncio.to_thread(get_earnings_calendar, ["AMKBY","ZIM","MT","LNG","WMT","1919.HK"])
    signals = await asyncio.to_thread(compute_all_signals, thermal_anomalies=thermal, earnings_calendar=earnings)
    return {"signals": signals}

# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
