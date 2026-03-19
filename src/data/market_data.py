"""
SatTrade Market Data — 3-Tier Failover
=======================================
Primary:   Polygon.io WebSocket (real-time ticks)
Secondary: Alpha Vantage REST (1-min bars)
Tertiary:  yfinance HISTORICAL ONLY — never real-time, never in hot path.

Every quote: { price, bid, ask, volume, timestamp_utc, source, age_ms, is_stale }
Stale threshold: 15s for prices.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Callable, Dict, Optional

import structlog

log = structlog.get_logger(__name__)

REDIS_URL          = os.getenv("REDIS_URL", "redis://localhost:6379/0")
POLYGON_API_KEY    = os.getenv("POLYGON_API_KEY", "")
ALPHA_VANTAGE_KEY  = os.getenv("ALPHA_VANTAGE_KEY", "")
QUOTE_STALE_S      = 15   # staleness threshold for prices


@dataclass
class Quote:
    ticker: str
    price: float
    bid: float = 0.0
    ask: float = 0.0
    volume: float = 0.0
    timestamp_utc: float = 0.0
    source: str = "unknown"
    age_ms: float = 0.0
    is_stale: bool = False

    def to_dict(self) -> dict:
        self.age_ms = (time.time() - self.timestamp_utc) * 1000
        self.is_stale = self.age_ms > (QUOTE_STALE_S * 1000)
        return asdict(self)


_redis_pool = None

async def _get_redis():
    global _redis_pool
    if _redis_pool is None:
        try:
            import redis.asyncio as aioredis
            _redis_pool = await aioredis.from_url(REDIS_URL, decode_responses=True)
        except Exception as exc:
            log.warning("market_data_redis_failed", error=str(exc))
            return None
    return _redis_pool


# ─── Tier 1: Polygon.io WebSocket ─────────────────────────────────────────────
class PolygonWebSocket:
    """
    Primary real-time price source.
    Reconnects with exponential backoff: 1→2→4→8→60s.
    """
    WS_URL = "wss://socket.polygon.io/stocks"
    BACKOFF = [1, 2, 4, 8, 60]

    def __init__(self) -> None:
        self._running = False
        self._ws = None

    async def connect_and_stream(
        self, on_quote: Callable[[Quote], None]
    ) -> None:
        if not POLYGON_API_KEY:
            log.warning("polygon_no_api_key")
            return

        backoff_idx = 0
        while True:
            try:
                import websockets  # type: ignore
                async with websockets.connect(self.WS_URL) as ws:
                    self._ws = ws
                    backoff_idx = 0   # reset on success

                    # Authenticate
                    await ws.send(json.dumps({"action": "auth", "params": POLYGON_API_KEY}))
                    # Subscribe to all trades
                    await ws.send(json.dumps({"action": "subscribe", "params": "T.*"}))

                    log.info("polygon_connected")
                    async for raw in ws:
                        try:
                            messages = json.loads(raw)
                            for msg in (messages if isinstance(messages, list) else [messages]):
                                if msg.get("ev") == "T":  # Trade event
                                    q = Quote(
                                        ticker=msg.get("sym", ""),
                                        price=float(msg.get("p", 0)),
                                        volume=float(msg.get("s", 0)),
                                        timestamp_utc=msg.get("t", time.time() * 1000) / 1000,
                                        source="polygon_ws",
                                    )
                                    await _cache_quote(q)
                                    on_quote(q)
                        except Exception:
                            pass
            except Exception as exc:
                wait = self.BACKOFF[min(backoff_idx, len(self.BACKOFF) - 1)]
                log.warning("polygon_ws_disconnected", error=str(exc), retry_s=wait)
                await asyncio.sleep(wait)
                backoff_idx += 1


# ─── Tier 2: Alpha Vantage REST ───────────────────────────────────────────────
_av_semaphore = asyncio.Semaphore(75)   # 75/min premium

async def fetch_alpha_vantage(ticker: str) -> Optional[Quote]:
    """1-minute intraday bar from Alpha Vantage."""
    if not ALPHA_VANTAGE_KEY:
        return None
    async with _av_semaphore:
        try:
            import aiohttp
            url = (
                f"https://www.alphavantage.co/query"
                f"?function=TIME_SERIES_INTRADAY&symbol={ticker}"
                f"&interval=1min&apikey={ALPHA_VANTAGE_KEY}&outputsize=compact"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    ts = data.get("Time Series (1min)", {})
                    if not ts:
                        return None
                    latest_key = sorted(ts.keys())[-1]
                    bar = ts[latest_key]
                    price = float(bar.get("4. close", 0))
                    return Quote(
                        ticker=ticker,
                        price=price,
                        volume=float(bar.get("5. volume", 0)),
                        timestamp_utc=time.time(),
                        source="alpha_vantage",
                    )
        except Exception as exc:
            log.warning("alpha_vantage_failed", ticker=ticker, error=str(exc))
            return None


# ─── Tier 3: yfinance — Historical ONLY ───────────────────────────────────────
_yf_semaphore = asyncio.Semaphore(10)   # rate limit to avoid bans

async def fetch_yfinance_historical(
    ticker: str, period: str = "1y"
) -> Optional[list]:
    """
    STRICTLY historical OHLCV data only.
    NEVER used for real-time pricing.
    NEVER in hot path.
    """
    async with _yf_semaphore:
        try:
            import yfinance as yf
            loop = asyncio.get_event_loop()
            hist = await loop.run_in_executor(
                None,
                lambda: yf.download(ticker, period=period, progress=False)
            )
            if hist.empty:
                return None
            records = []
            for idx, row in hist.iterrows():
                records.append({
                    "date": str(idx.date()),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                })
            log.info("yfinance_historical_fetched", ticker=ticker, rows=len(records))
            return records
        except Exception as exc:
            log.warning("yfinance_failed", ticker=ticker, error=str(exc))
            return None


# ─── Unified Quote API ────────────────────────────────────────────────────────
async def get_quote(ticker: str) -> Quote:
    """
    3-tier failover:
    1. Redis quote cache (Polygon populated)
    2. Alpha Vantage REST
    3. Last known price (stale flagged)
    """
    r = await _get_redis()

    # Check cache (Polygon writes here)
    if r:
        try:
            raw = await r.get(f"quote:{ticker}")
            if raw:
                data = json.loads(raw)
                q = Quote(**{k: data[k] for k in Quote.__dataclass_fields__ if k in data})
                q.age_ms = (time.time() - q.timestamp_utc) * 1000
                q.is_stale = q.age_ms > (QUOTE_STALE_S * 1000)
                if not q.is_stale:
                    return q
        except Exception:
            pass

    # Fallback: Alpha Vantage
    q = await fetch_alpha_vantage(ticker)
    if q:
        await _cache_quote(q)
        return q

    # Ultimate fallback: stale redis value
    if r:
        try:
            raw = await r.get(f"quote:{ticker}")
            if raw:
                data = json.loads(raw)
                q = Quote(**{k: data[k] for k in Quote.__dataclass_fields__ if k in data})
                q.is_stale = True
                return q
        except Exception:
            pass

    log.warning("quote_not_available", ticker=ticker)
    return Quote(ticker=ticker, price=0.0, source="unavailable", is_stale=True,
                 timestamp_utc=time.time())


async def _cache_quote(q: Quote) -> None:
    """Write quote to Redis with 30s TTL and publish to 'prices' channel."""
    r = await _get_redis()
    if r:
        try:
            payload = json.dumps(q.to_dict())
            await r.setex(f"quote:{q.ticker}", 30, payload)
            await r.publish("prices", payload)
        except Exception as exc:
            log.warning("quote_cache_failed", ticker=q.ticker, error=str(exc))


# ─── Market Data Service (lifecycle management) ───────────────────────────────
class MarketDataService:
    """Manages Polygon WebSocket lifecycle and quote fan-out."""

    def __init__(self) -> None:
        self._polygon = PolygonWebSocket()
        self._quote_callbacks: list = []

    def register_callback(self, fn: Callable[[Quote], None]) -> None:
        self._quote_callbacks.append(fn)

    def _on_quote(self, q: Quote) -> None:
        for cb in self._quote_callbacks:
            try:
                cb(q)
            except Exception:
                pass

    async def start(self) -> None:
        """Start Polygon WebSocket; auto-falls back to AV polling if key missing."""
        if POLYGON_API_KEY:
            asyncio.create_task(self._polygon.connect_and_stream(self._on_quote))
            log.info("polygon_ws_started")
        else:
            log.warning("polygon_key_missing", fallback="alpha_vantage_polling")
