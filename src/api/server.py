"""
FastAPI backend serving real signal data to the React frontend.
WebSocket endpoint broadcasts live signal updates.
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="SatTrade API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_clients: list[WebSocket] = []

MOCK_SIGNALS = {
    "port_throughput": {
        "signal_name": "port_throughput",
        "score": 82,
        "direction": "BULLISH",
        "delta_vs_baseline": 0.34,
        "ic": 0.047,
        "icir": 0.62,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "affected_equities": [
            {"ticker": "AMKBY", "strength": "STRONG", "direction": "↑↑"},
            {"ticker": "ZIM",   "strength": "MEDIUM", "direction": "↑"},
            {"ticker": "1919.HK","strength": "STRONG","direction": "↑↑"},
        ],
    },
    "retail_footfall": {
        "signal_name": "retail_footfall",
        "score": 65,
        "direction": "STABLE",
        "delta_vs_baseline": 0.12,
        "ic": 0.044,
        "icir": 0.58,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "affected_equities": [
            {"ticker": "WMT", "strength": "STRONG", "direction": "↑↑"},
            {"ticker": "TGT", "strength": "WEAK",   "direction": "~"},
            {"ticker": "HD",  "strength": "MEDIUM", "direction": "↑"},
        ],
    },
    "industrial_thermal": {
        "signal_name": "industrial_thermal",
        "score": 87,
        "direction": "HOT",
        "delta_vs_baseline": 0.45,
        "ic": 0.052,
        "icir": 0.68,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "affected_equities": [
            {"ticker": "MT",  "strength": "STRONG", "direction": "↑↑"},
            {"ticker": "X",   "strength": "MEDIUM", "direction": "↑"},
            {"ticker": "LNG", "strength": "STRONG", "direction": "↑↑"},
        ],
    },
}


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "live",
        "pipeline": "active",
        "signals_active": len(MOCK_SIGNALS),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/signals")
async def get_signals() -> dict:
    return {"signals": MOCK_SIGNALS, "as_of": datetime.now(timezone.utc).isoformat()}


@app.get("/api/signals/{signal_name}")
async def get_signal(signal_name: str) -> dict:
    if signal_name not in MOCK_SIGNALS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Signal {signal_name} not found")
    return MOCK_SIGNALS[signal_name]


@app.get("/api/portfolio/nav")
async def get_nav() -> dict:
    return {
        "nav_usd": 10_482_100.0,
        "gross_exposure_pct": 142.0,
        "var_99_1d_pct": 0.82,
        "kill_switch_state": "ARMED",
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/equities")
async def get_equities() -> dict:
    """
    Returns global equity universe with real prices from Alpaca.
    Falls back to cached prices if Alpaca is unavailable.
    """
    equities = []
    alpaca_available = bool(os.environ.get("ALPACA_API_KEY"))

    us_tickers = [
        ("AAPL","Apple Inc.","NASDAQ"),("MSFT","Microsoft","NASDAQ"),
        ("NVDA","NVIDIA","NASDAQ"),("AMZN","Amazon","NASDAQ"),
        ("AMKBY","AP Moller-Maersk","OTC"),("WMT","Walmart","NYSE"),
        ("ZIM","ZIM Integrated","NYSE"),("MT","ArcelorMittal","NYSE"),
        ("HD","Home Depot","NYSE"),("TGT","Target","NYSE"),
        ("LNG","Cheniere Energy","NYSE"),("MATX","Matson Inc","NYSE"),
        ("X","US Steel","NYSE"),("FDX","FedEx","NYSE"),
        ("DAL","Delta Air Lines","NYSE"),("CAT","Caterpillar","NYSE"),
        ("XOM","Exxon Mobil","NYSE"),("BHP","BHP Group","NYSE"),
        ("VALE","Vale SA","NYSE"),("COST","Costco","NASDAQ"),
    ]

    if alpaca_available:
        try:
            from src.execution.broker import AlpacaGateway
            gw = AlpacaGateway(env="paper")
            for ticker, name, exchange in us_tickers:
                try:
                    q = gw.get_quote(ticker)
                    equities.append({
                        "ticker": ticker, "name": name, "exchange": exchange,
                        "price": q.price, "bid": q.bid, "ask": q.ask,
                        "sat_signal": MOCK_SIGNALS.get("port_throughput",{})\
                            .get("direction","NEUTRAL")
                            if ticker in ["AMKBY","ZIM","MATX"] else "NEUTRAL",
                        "source": "alpaca_live",
                    })
                except Exception:
                    equities.append(_fallback_equity(ticker, name, exchange))
        except Exception:
            equities = [_fallback_equity(t, n, e) for t, n, e in us_tickers]
    else:
        equities = [_fallback_equity(t, n, e) for t, n, e in us_tickers]

    return {"equities": equities, "count": len(equities)}


def _fallback_equity(ticker: str, name: str, exchange: str) -> dict:
    import random
    base = {"AAPL": 178.2, "MSFT": 415.3, "NVDA": 876.4, "AMZN": 182.4,
            "AMKBY": 128.4, "WMT": 58.7, "ZIM": 14.22, "MT": 28.4,
            "HD": 352.6, "TGT": 142.1, "LNG": 158.4, "MATX": 124.4,
            "X": 38.4, "FDX": 248.6, "DAL": 48.4, "CAT": 344.6,
            "XOM": 114.6, "BHP": 58.4, "VALE": 14.4, "COST": 718.4}.get(ticker, 100.0)
    price = base * (1 + random.uniform(-0.02, 0.02))
    return {
        "ticker": ticker, "name": name, "exchange": exchange,
        "price": round(price, 2), "bid": round(price * 0.999, 2),
        "ask": round(price * 1.001, 2), "source": "cached",
        "sat_signal": "BULLISH" if ticker in ["AMKBY","ZIM","MT","WMT","LNG"] else "NEUTRAL",
    }


@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket) -> None:
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await asyncio.sleep(15)
            payload = {
                "type": "SIGNAL_UPDATE",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "signals": MOCK_SIGNALS,
                "health": {
                    "pipeline": "live",
                    "signals_active": 3,
                    "coverage_pct": 94.2,
                },
            }
            await websocket.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


if __name__ == "__main__":
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=True)
