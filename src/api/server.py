"""
SatTrade High-Performance API Server.
Connects the Global Intelligence Engine to the Frontend.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.intelligence.engine import GlobalIntelligenceEngine
from src.free_data import aircraft, quakes, orbits, market, macro, news

app = FastAPI(title="SatTrade Intelligence API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = GlobalIntelligenceEngine()

@app.get("/")
def health_check():
    return {"status": "operational", "engine": "GlobalIntelligenceEngine V2"}

@app.get("/api/intelligence/thermal")
async def get_thermal():
    """Thermal anomalies from NASA FIRMS."""
    return await engine.get_thermal_signals()

@app.get("/api/intelligence/aircraft")
async def get_aircraft():
    """Live military/cargo tracking from OpenSky."""
    return await aircraft.get_live_aircraft()

@app.get("/api/intelligence/seismic")
async def get_seismic():
    """Live USGS earthquakes map."""
    return await quakes.get_latest_quakes()

@app.get("/api/intelligence/orbits")
async def get_orbits():
    """Live satellite propagation from Celestrak."""
    return await orbits.get_live_orbits()

@app.get("/api/market/snapshot")
async def get_snapshot(tickers: str):
    """Real-time bulk prices via yfinance."""
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    return await market.get_market_snapshot(ticker_list)

@app.get("/api/market/chart/{ticker}")
async def get_chart(ticker: str, period: str = "3mo"):
    """Historical OHLCV for re-charts."""
    df = market.get_ohlcv_history(ticker, period)
    return df.reset_index().to_dict(orient="records")

@app.get("/api/macro/{series}")
async def get_macro(series: str):
    """FRED macro data (VIX, Oil, Yields)."""
    return await macro.get_macro_data(series)

@app.get("/api/news/{category}")
async def get_news(category: str):
    """RSS / GDELT intelligence feed."""
    if category.upper() == "GLOBAL":
        return await news.query_gdelt("maritime defense finance")
    return await news.get_rss_news(category)

# Live WebSocket for Aircraft Alerts
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Periodically scan for emergencies and broadcast
            aircraft_data = await aircraft.get_live_aircraft()
            emergencies = [a for a in aircraft_data if a.is_emergency]
            if emergencies:
                await manager.broadcast({"type": "SQUAWK_EMERGENCY", "data": emergencies})
            await websocket.receive_text() # keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
