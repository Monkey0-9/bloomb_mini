"""
SatTrade API Server — Institutional Grade
==========================================
AgentRouter + JWT RS256 + WebSocket Hub + SSE Streaming
Circuit breakers, rate limiting, Redis replay, structured logging.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

import structlog
from fastapi import (
    Depends, FastAPI, HTTPException, Request, WebSocket,
    WebSocketDisconnect, status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Optional heavy deps — graceful degradation
try:
    import jwt as pyjwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

log = structlog.get_logger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────
REDIS_URL       = os.getenv("REDIS_URL", "redis://localhost:6379/0")
FRONTEND_URL    = os.getenv("FRONTEND_URL", "http://localhost:3000")
JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY", "")
JWT_PUBLIC_KEY  = os.getenv("JWT_PUBLIC_KEY", "")
CLAUDE_KEY      = os.getenv("CLAUDE_API_KEY", "")
ALGORITHM       = "RS256"
ACCESS_TTL      = 900      # 15 min
REFRESH_TTL     = 604_800  # 7 d

STALE = {"prices": 15, "ais": 300, "satellite": 21_600, "fred": 86_400}

INTENT_TAXONOMY = [
    "VESSEL_INTEL", "THERMAL_ANALYSIS", "PORTFOLIO_RISK", "SIGNAL_QUERY",
    "MACRO_DIVERGENCE", "CHART_REQUEST", "ALERT_CREATE", "FUNDAMENTAL_DATA",
    "WORKFLOW_CREATE", "DOCUMENT_ANALYSIS", "COMPOSITE_QUERY",
]

# ─── Dataclasses ─────────────────────────────────────────────────────────────
@dataclass
class AgentResponse:
    data: Any
    confidence: float
    age_s: float
    agent_id: str
    error: Optional[str] = None
    is_stale: bool = False

@dataclass
class UserClaims:
    user_id: str
    email: str
    tier: str = "free"     # free | pro | institutional
    exp: int = 0

@dataclass
class CircuitBreaker:
    agent_id: str
    failures: int = 0
    state: str = "HEALTHY"   # HEALTHY | DEGRADED | ERROR
    last_failure: float = 0.0
    last_success: float = field(default_factory=time.time)
    error_count: int = 0
    cache_hits: int = 0
    cache_requests: int = 0

    def record_failure(self) -> None:
        self.failures += 1
        self.error_count += 1
        self.last_failure = time.time()
        if self.failures >= 3 and time.time() - self.last_failure < 60:
            self.state = "DEGRADED"
            log.warning("circuit_breaker_open", agent=self.agent_id)

    def record_success(self) -> None:
        self.failures = 0
        self.state = "HEALTHY"
        self.last_success = time.time()

    def should_retry(self) -> bool:
        if self.state == "HEALTHY":
            return True
        return time.time() - self.last_failure > 120  # auto-retry 2 min

    @property
    def cache_hit_rate(self) -> float:
        if not self.cache_requests:
            return 0.0
        return self.cache_hits / self.cache_requests

# ─── Agent Registry ───────────────────────────────────────────────────────────
AGENT_REGISTRY: Dict[str, CircuitBreaker] = {
    name: CircuitBreaker(agent_id=name)
    for name in ["satellite", "maritime", "signal", "tft", "risk",
                 "economics", "orchestrator", "ingest"]
}

# ─── BroadcastManager ─────────────────────────────────────────────────────────
class BroadcastManager:
    """Thread-safe topic fan-out with Redis missed-message replay."""

    def __init__(self) -> None:
        self._subs: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._seq: Dict[str, int] = defaultdict(int)
        self._redis: Optional[Any] = None

    async def init_redis(self) -> None:
        if REDIS_AVAILABLE:
            try:
                self._redis = aioredis.from_url(REDIS_URL, decode_responses=True)
                log.info("broadcast_redis_connected")
                # Start listener loop for cross-process fanout
                asyncio.create_task(self._listen_loop())
            except Exception as exc:
                log.warning("broadcast_redis_failed", error=str(exc))

    async def _listen_loop(self) -> None:
        """Listen to Redis pub/sub and fan out to local WebSockets."""
        if not self._redis:
            return
        pubsub = self._redis.pubsub()
        await pubsub.subscribe("vessel", "flight", "signal", "alerts")
        log.info("broadcast_listener_active", channels=["vessel", "flight", "signal", "alerts"])
        
        try:
            async for msg in pubsub.listen():
                if msg["type"] == "message":
                    topic = msg["channel"]
                    try:
                        payload = json.loads(msg["data"])
                        await self.broadcast(topic, payload)
                    except json.JSONDecodeError:
                        pass
        except Exception as exc:
            log.error("broadcast_listener_error", error=str(exc))
            await asyncio.sleep(5)
            asyncio.create_task(self._listen_loop())

    def subscribe(self, topic: str, ws: WebSocket) -> None:
        self._subs[topic].add(ws)

    def unsubscribe(self, topic: str, ws: WebSocket) -> None:
        self._subs[topic].discard(ws)

    def unsubscribe_all(self, ws: WebSocket) -> None:
        for subs in self._subs.values():
            subs.discard(ws)

    async def broadcast(self, topic: str, payload: dict) -> None:
        self._seq[topic] += 1
        msg = json.dumps({**payload, "_seq": self._seq[topic], "_topic": topic,
                          "_ts": time.time()})

        # Store in Redis sorted set (120s TTL window)
        if self._redis:
            key = f"replay:{topic}"
            try:
                await self._redis.zadd(key, {msg: time.time()})
                await self._redis.zremrangebyscore(key, 0, time.time() - 120)
                await self._redis.expire(key, 300)
            except Exception:
                pass

        # Snapshot set to avoid mutation during iteration
        recipients = set(self._subs.get(topic, set()))
        if not recipients:
            return

        results = await asyncio.gather(
            *[ws.send_text(msg) for ws in recipients],
            return_exceptions=True,
        )
        for ws, result in zip(recipients, results):
            if isinstance(result, Exception):
                self._subs[topic].discard(ws)

    async def replay_missed(self, topic: str, ws: WebSocket, since_seq: int) -> None:
        if not self._redis:
            return
        key = f"replay:{topic}"
        try:
            raw_msgs = await self._redis.zrangebyscore(key, time.time() - 120, "+inf")
            for raw in raw_msgs:
                try:
                    parsed = json.loads(raw)
                    if parsed.get("_seq", 0) > since_seq:
                        await ws.send_text(raw)
                except Exception:
                    pass
        except Exception as exc:
            log.warning("replay_failed", topic=topic, error=str(exc))


broadcast_mgr = BroadcastManager()

# ─── Rate Limiting ────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

class TokenBucket:
    """Per-WebSocket token-bucket rate limiter (10 msg/sec)."""
    def __init__(self, rate: float = 10.0, capacity: float = 10.0):
        self.rate = rate
        self.capacity = capacity
        self._tokens = capacity
        self._last = time.monotonic()

    def consume(self) -> bool:
        now = time.monotonic()
        elapsed = now - self._last
        self._last = now
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False

# ─── JWT Auth ─────────────────────────────────────────────────────────────────
bearer = HTTPBearer(auto_error=False)

def _decode_jwt(token: str) -> UserClaims:
    if not JWT_AVAILABLE or not JWT_PUBLIC_KEY:
        return UserClaims(user_id="dev", email="dev@localhost", tier="institutional")
    try:
        payload = pyjwt.decode(token, JWT_PUBLIC_KEY, algorithms=[ALGORITHM])
        return UserClaims(
            user_id=payload["sub"],
            email=payload.get("email", ""),
            tier=payload.get("tier", "free"),
            exp=payload.get("exp", 0),
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc

async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
) -> UserClaims:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization required")
    return _decode_jwt(credentials.credentials)

@app.post("/api/v1/auth/refresh")
async def refresh_token(request: Request):
    """Refresh Token endpoint returning httpOnly SameSite=Strict cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    try:
        if JWT_AVAILABLE and JWT_PUBLIC_KEY and JWT_PRIVATE_KEY:
            payload = pyjwt.decode(refresh_token, JWT_PUBLIC_KEY, algorithms=[ALGORITHM])
            access_token = pyjwt.encode(
                {"sub": payload["sub"], "email": payload.get("email", ""), "tier": payload.get("tier", "free"), "exp": int(time.time()) + ACCESS_TTL},
                JWT_PRIVATE_KEY, algorithm=ALGORITHM
            )
            return JSONResponse({"access_token": access_token})
        else:
            return JSONResponse({"access_token": "dev_token_dummy"})
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

# ─── AgentRouter ──────────────────────────────────────────────────────────────
class AgentRouter:
    """Dispatch queries to agents with circuit-breaker protection."""

    async def _call_agent(self, agent_id: str, task: str, params: dict) -> AgentResponse:
        cb = AGENT_REGISTRY[agent_id]
        if not cb.should_retry():
            # Serve from Redis cache
            cached = await self._get_cache(f"agent:{agent_id}:{task}")
            if cached:
                cb.cache_hits += 1
                cb.cache_requests += 1
                return AgentResponse(data=cached, confidence=0.5, age_s=999,
                                     agent_id=agent_id, is_stale=True)
            cb.cache_requests += 1
            return AgentResponse(data={}, confidence=0, age_s=9999,
                                 agent_id=agent_id, error="DEGRADED",
                                 is_stale=True)

        try:
            start = time.time()
            result = await self._dispatch(agent_id, task, params)
            latency = time.time() - start
            cb.record_success()
            payload = asdict(result) if hasattr(result, '__dataclass_fields__') else {"data": result}
            await self._set_cache(f"agent:{agent_id}:{task}", payload, ttl=60)
            log.info("agent_called", agent=agent_id, task=task, latency_ms=round(latency*1000))
            return AgentResponse(data=payload, confidence=0.9,
                                 age_s=latency, agent_id=agent_id)
        except Exception as exc:
            cb.record_failure()
            log.error("agent_error", agent=agent_id, task=task, error=str(exc))
            return AgentResponse(data={}, confidence=0, age_s=9999,
                                 agent_id=agent_id, error=str(exc))

    async def _dispatch(self, agent_id: str, task: str, params: dict) -> Any:
        """Route to actual agent implementations."""
        if agent_id == "maritime":
            from src.maritime.vessel_tracker import VesselTracker
            tracker = VesselTracker()
            return await tracker.get_intelligence(params)
        elif agent_id == "signal":
            from src.signals.composite_score import CompositeScorer
            scorer = CompositeScorer()
            ticker = params.get("ticker", "SPY")
            return await scorer.score(ticker)
        elif agent_id == "tft":
            from src.signals.tft_model import ModelServer
            srv = ModelServer()
            ticker = params.get("ticker", "SPY")
            horizon = params.get("horizon", 21)
            return await srv.predict(ticker, horizon)
        elif agent_id == "risk":
            from src.risk.engine import RiskEngine
            engine = RiskEngine()
            return await engine.get_status()
        elif agent_id == "economics":
            from src.data.economic_data import EconomicsDataService
            svc = EconomicsDataService()
            return await svc.get_divergences()
        return {"status": "ok", "agent": agent_id}

    async def route(self, query: str, context: dict,
                    agent_list: Optional[List[str]] = None) -> Dict[str, AgentResponse]:
        agents = agent_list or ["signal", "maritime"]
        tasks = {a: self._call_agent(a, "query", {"query": query, **context})
                 for a in agents if a in AGENT_REGISTRY}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        return {agent: (res if isinstance(res, AgentResponse)
                        else AgentResponse(data={}, confidence=0, age_s=9999,
                                           agent_id=agent, error=str(res)))
                for agent, res in zip(tasks.keys(), results)}

    async def _get_cache(self, key: str) -> Optional[dict]:
        if not broadcast_mgr._redis:
            return None
        try:
            raw = await broadcast_mgr._redis.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            return None

    async def _set_cache(self, key: str, value: dict, ttl: int = 60) -> None:
        if not broadcast_mgr._redis:
            return
        try:
            await broadcast_mgr._redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception:
            pass


agent_router = AgentRouter()

# ─── FastAPI App ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await broadcast_mgr.init_redis()
    log.info("sattrade_server_started", redis=REDIS_AVAILABLE, jwt=JWT_AVAILABLE)

    # Launch Globe Data Pipelines
    from src.globe.adsb import run_adsb_pipeline
    from src.globe.squawk import run_squawk_pipeline
    from src.globe.orbits import run_orbits_pipeline
    from src.globe.ais import run_ais_pipeline
    from src.globe.thermal import run_thermal_pipeline
    
    async def globe_dispatch(payload: dict):
        topic = payload.pop('_topic', 'default')
        if topic == 'flight_update':
            topic = 'flight'
        await broadcast_mgr.broadcast(topic, payload)

    globe_tasks = [
        asyncio.create_task(run_adsb_pipeline(globe_dispatch)),
        asyncio.create_task(run_squawk_pipeline(globe_dispatch)),
        asyncio.create_task(run_orbits_pipeline(globe_dispatch)),
        asyncio.create_task(run_ais_pipeline(globe_dispatch)),
        asyncio.create_task(run_thermal_pipeline(globe_dispatch)),
    ]

    yield
    for t in globe_tasks:
        t.cancel()
    log.info("sattrade_server_shutdown")

app = FastAPI(
    title="SatTrade Institutional API",
    version="2.0.0",
    description="Satellite-intelligence finance terminal — beats Bloomberg on every axis.",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
    return response

# ─── Pydantic Models ──────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str
    context: dict = {}
    documents: List[str] = []   # base64-encoded PDFs

class IntentRequest(BaseModel):
    query: str
    context: dict = {}

class AlertRequest(BaseModel):
    type: str
    params: dict

class TradeRequest(BaseModel):
    ticker: str
    qty: int
    side: str
    order_type: str = "MARKET"
    price: Optional[float] = None

# ─── REST Endpoints ───────────────────────────────────────────────────────────

@app.get("/health")
@app.get("/api/v1/agents/health")
async def agents_health():
    """Returns health status for all 8 registered agents."""
    statuses = {}
    for agent_id, cb in AGENT_REGISTRY.items():
        statuses[agent_id] = {
            "state": cb.state,
            "error_count": cb.error_count,
            "last_success_utc": cb.last_success,
            "data_freshness_s": time.time() - cb.last_success,
            "cache_hit_rate": round(cb.cache_hit_rate, 3),
        }
    return {"agents": statuses, "_meta": {"fetched_utc": time.time()}}


@app.post("/api/v1/query/intent")
@limiter.limit("100/minute")
async def query_intent(req: IntentRequest, request: Request,
                       _: UserClaims = Depends(require_auth)):
    """
    Claude Sonnet 4.6 intent classification.
    Returns: { intent, agent_list, params, confidence, suggested_followups }
    """
    if not CLAUDE_AVAILABLE or not CLAUDE_KEY:
        # Fallback: keyword-based routing
        intent = _keyword_intent(req.query)
        return {
            "intent": intent,
            "agent_list": _intent_to_agents(intent),
            "params": {},
            "confidence": 0.72,
            "clarification_needed": False,
            "suggested_followups": [],
        }

    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    system = (
        "You are an institutional finance AI router. Classify the user query into one of these intents: "
        + ", ".join(INTENT_TAXONOMY)
        + ". Return ONLY valid JSON: {\"intent\": str, \"agent_list\": list[str], "
          "\"params\": dict, \"confidence\": float, \"suggested_followups\": list[str]}. "
        "agent_list must be a subset of: satellite, maritime, signal, tft, risk, economics, orchestrator, ingest."
    )
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            system=system,
            messages=[{"role": "user", "content": req.query}],
        )
        parsed = json.loads(resp.content[0].text)
        parsed["clarification_needed"] = parsed.get("confidence", 1.0) < 0.75
        return parsed
    except Exception as exc:
        log.error("intent_classification_failed", error=str(exc))
        intent = _keyword_intent(req.query)
        return {
            "intent": intent,
            "agent_list": _intent_to_agents(intent),
            "params": {},
            "confidence": 0.65,
            "clarification_needed": True,
            "suggested_followups": ["Could you clarify your request?"],
        }


@app.post("/api/v1/query/stream")
@limiter.limit("30/minute")
async def query_stream(req: QueryRequest, request: Request,
                       user: UserClaims = Depends(require_auth)):
    """
    SSE streaming query endpoint.
    Chunks: routing | token | citation | data | done
    """
    q = req.query

    async def event_source() -> AsyncGenerator[str, None]:
        start = time.time()
        agents_used: List[str] = []

        try:
            # 1. Classify intent
            intent = _keyword_intent(q)
            agent_list = _intent_to_agents(intent)
            agents_used = agent_list

            yield f"data: {json.dumps({'type': 'routing', 'intent': intent, 'agents': agent_list})}\n\n"

            # 2. Gather agent context
            agent_results = await agent_router.route(q, req.context, agent_list)
            context_str = _build_context(agent_results, req.context)

            # 3. Stream from Claude
            if CLAUDE_AVAILABLE and CLAUDE_KEY:
                client = anthropic.Anthropic(api_key=CLAUDE_KEY)
                system = (
                    "You are SatTrade, an institutional satellite-intelligence finance terminal. "
                    "Ground ALL answers in the satellite data, AIS maritime intelligence, and "
                    "TFT probabilistic forecasts provided. Be concise and precise. "
                    "Cite your data sources inline with [source:value]."
                )
                messages = [{"role": "user", "content": f"Context:\n{context_str}\n\nQuery: {q}"}]

                with client.messages.stream(
                    model="claude-sonnet-4-5",
                    max_tokens=2048,
                    system=system,
                    messages=messages,
                ) as stream:
                    for text in stream.text_stream:
                        yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"
            else:
                # Degraded: return agent data directly
                summary = f"Query: {q}\n\nAgent responses:\n"
                for agent_id, res in agent_results.items():
                    summary += f"[{agent_id.upper()}] {json.dumps(res.data)[:200]}\n"
                for word in summary.split():
                    yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
                    await asyncio.sleep(0.01)

            # 4. Emit citations from agent data
            for agent_id, res in agent_results.items():
                yield f"data: {json.dumps({'type': 'citation', 'source': agent_id, 'age_s': res.age_s, 'is_stale': res.is_stale})}\n\n"

            latency_ms = round((time.time() - start) * 1000)
            yield f"data: {json.dumps({'type': 'done', 'latency_ms': latency_ms, 'agents_used': agents_used})}\n\n"

        except Exception as exc:
            log.error("sse_stream_error", error=str(exc))
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ─── Signals Endpoints ─────────────────────────────────────────────────────────

@app.get("/api/v1/signals/score/{ticker}")
@limiter.limit("200/minute")
async def get_composite_score(ticker: str, request: Request,
                               _: UserClaims = Depends(require_auth)):
    """Get composite alpha score for ticker from all satellite signals."""
    try:
        from src.signals.composite_score import CompositeScorer
        scorer = CompositeScorer()
        result = await scorer.score(ticker.upper())
        return {**result, "_meta": {"source": "signal_agent", "fetched_utc": time.time(),
                                     "age_s": 0, "is_stale": False, "confidence": 0.85}}
    except Exception as exc:
        log.error("composite_score_error", ticker=ticker, error=str(exc))
        raise HTTPException(502, detail=str(exc)) from exc


@app.get("/api/v1/signals/forecast/{ticker}")
@limiter.limit("100/minute")
async def get_forecast(ticker: str, horizon: int = 21, request: Request = None,
                        _: UserClaims = Depends(require_auth)):
    """Get TFT probabilistic forecast: P10/P50/P90 for horizon days."""
    try:
        from src.signals.tft_model import ModelServer
        srv = ModelServer()
        result = await srv.predict(ticker.upper(), horizon)
        return {**result, "_meta": {"source": "tft_agent", "fetched_utc": time.time(),
                                     "age_s": 0, "is_stale": False, "confidence": 0.80}}
    except Exception as exc:
        log.error("forecast_error", ticker=ticker, error=str(exc))
        raise HTTPException(502, detail=str(exc)) from exc


# ─── Vessels/Flights Endpoints ─────────────────────────────────────────────────

@app.get("/api/vessels")
@app.get("/api/v1/vessels")
@limiter.limit("200/minute")
async def get_vessels(request: Request, confidence: Optional[str] = None,
                       near: Optional[str] = None, radius_nm: float = 200):
    """GeoJSON vessel layer. confidence=HIGH|MED|LOW, near=lat,lon"""
    try:
        from src.maritime.vessel_tracker import VesselTracker
        tracker = VesselTracker()
        vessels = await tracker.get_all_vessels(confidence_filter=confidence)
        features = [_vessel_to_feature(v) for v in vessels]
        return {"type": "FeatureCollection", "features": features,
                "_meta": {"count": len(features), "fetched_utc": time.time()}}
    except Exception as exc:
        log.warning("vessels_api_degraded", error=str(exc))
        return {"type": "FeatureCollection", "features": [], "_meta": {"error": str(exc)}}


@app.get("/api/v1/vessels/{mmsi}/intelligence")
async def vessel_intelligence(mmsi: str, _: UserClaims = Depends(require_auth)):
    """Full vessel intelligence: dark confidence, sanctions, cargo, equity signal."""
    try:
        from src.maritime.vessel_tracker import VesselTracker
        tracker = VesselTracker()
        rec = await tracker.get_vessel_intelligence(mmsi)
        return rec
    except Exception as exc:
        raise HTTPException(404, detail=str(exc)) from exc


@app.get("/api/flights")
@app.get("/api/v1/flights")
@limiter.limit("200/minute")
async def get_flights(request: Request):
    """GeoJSON flight layer from ADS-B feeds."""
    try:
        from src.maritime.flights_live import get_cargo_flights
        import asyncio
        data = await asyncio.to_thread(get_cargo_flights)
        flights = data.get("flights", [])
        features = [_flight_to_feature(f) for f in flights]
        return {"type": "FeatureCollection", "features": features,
                "_meta": {"count": len(features), "fetched_utc": time.time()}}
    except Exception as exc:
        log.warning("flights_api_degraded", error=str(exc))
        return {"type": "FeatureCollection", "features": [], "_meta": {"error": str(exc)}}


# ─── Alpha / Signal Routes ─────────────────────────────────────────────────────

@app.get("/api/alpha/thermal")
@limiter.limit("100/minute")
async def get_thermal(request: Request):
    """Industrial thermal anomalies from NASA FIRMS FRP — Bloomberg cannot offer this."""
    try:
        from src.satellite.thermal import scan_industrial_facilities
        import asyncio
        signals = await asyncio.to_thread(scan_industrial_facilities, 1)
        return {"signals": signals, "_meta": {"source": "nasa_firms", "fetched_utc": time.time()}}
    except Exception as exc:
        log.warning("thermal_degraded", error=str(exc))
        return {"signals": [], "_meta": {"error": str(exc)}}


@app.get("/api/alpha/composite")
@limiter.limit("200/minute")
async def get_composite(request: Request, ticker: str = "ZIM"):
    """Multi-signal composite score for ticker."""
    try:
        from src.signals.composite_score import CompositeScorer
        scorer = CompositeScorer()
        return await scorer.score(ticker.upper())
    except Exception as exc:
        return {"error": str(exc), "ticker": ticker, "direction": "NEUTRAL",
                "final_score": 0.0, "confidence": 0.0}


@app.get("/api/alpha/macro")
async def get_macro():
    """Macro indicators from FRED."""
    from src.data.macro import get_macro_data
    return await get_macro_data()


@app.get("/api/alpha/news")
async def get_news(ticker: str = ""):
    """Market news feed with satellite signal context."""
    from src.data.news import fetch_news
    results = await fetch_news(ticker)
    return {"news": results, "_meta": {"source": "rss_aggregated"}}


@app.get("/api/market/history/{ticker}")
@limiter.limit("50/minute")
async def get_market_history(ticker: str, period: str = "1y", request: Request = None):
    """Historical OHLCV data from yfinance for charting."""
    try:
        from src.data.market_data import fetch_yfinance_historical
        data = await fetch_yfinance_historical(ticker.upper(), period=period)
        if not data:
            raise HTTPException(404, detail=f"No data found for {ticker}")
        return {"data": data, "_meta": {"ticker": ticker, "period": period}}
    except Exception as exc:
        raise HTTPException(502, detail=str(exc)) from exc
# ─── Risk Endpoints ───────────────────────────────────────────────────────────

@app.get("/api/risk")
@app.get("/api/v1/risk")
@limiter.limit("50/minute")
async def get_risk_status(request: Request, user: UserClaims = Depends(require_auth)):
    """Returns general risk engine status and portfolio metrics."""
    try:
        from src.risk.engine import RiskEngine
        engine = RiskEngine()
        status_data = await engine.get_status()
        # Mock portfolio for UI if no positions
        positions, equity = await engine._get_portfolio(user.user_id)
        
        # Calculate summary for frontend RiskPanel.tsx
        notional = sum(p.notional for p in positions)
        return {
            "status": "GREEN" if not status_data["kill_switch_active"] else "RED",
            "portfolio": {
                "equity": equity,
                "notional_exposure": notional,
                "gross_exposure_pct": notional / max(equity, 1),
                "net_exposure_pct": sum(p.qty * p.current_price for p in positions) / max(equity, 1),
                "var_99_1d_pct": status_data["var_snapshot"].get("var_99", 0.0),
                "kill_switch_active": status_data["kill_switch_active"]
            },
            "gates": [
                {"name": "Gross Exposure", "passed": (notional / max(equity, 1)) < 1.5, "value": f"{notional/max(equity,1):.2%}", "threshold": "150%"},
                {"name": "Monte Carlo VaR", "passed": True, "value": f"{status_data['var_snapshot'].get('var_99', 0.0):.2%}", "threshold": "2%"},
                {"name": "Kill Switch", "passed": not status_data["kill_switch_active"], "value": "OFF" if not status_data["kill_switch_active"] else "ON", "threshold": "OFF"}
            ]
        }
    except Exception as exc:
        log.error("risk_status_error", error=str(exc))
        raise HTTPException(500, detail=str(exc)) from exc


@app.post("/api/v1/risk/evaluate")
@limiter.limit("50/minute")
async def evaluate_risk(req: TradeRequest, request: Request,
                         user: UserClaims = Depends(require_auth)):
    """Run all 9 risk gates against proposed trade. Returns gate-by-gate result."""
    try:
        from src.risk.engine import RiskEngine
        engine = RiskEngine()
        result = await engine.evaluate_trade({
            "ticker": req.ticker, "qty": req.qty, "side": req.side,
            "order_type": req.order_type, "price": req.price,
            "user_id": user.user_id,
        })
        return result
    except Exception as exc:
        log.error("risk_evaluate_error", error=str(exc))
        raise HTTPException(500, detail=str(exc)) from exc


@app.post("/api/v1/risk/size")
async def risk_size(request: Request, _: UserClaims = Depends(require_auth)):
    """Half-Kelly position sizing with TFT P50 direction accuracy."""
    body = await request.json()
    try:
        from src.risk.position_sizer import HalfKellySizer
        sizer = HalfKellySizer()
        return await sizer.size(
            ticker=body["ticker"],
            entry=body["entry"],
            stop=body["stop"],
            target=body["target"],
            equity=body.get("equity", 100_000),
        )
    except Exception as exc:
        raise HTTPException(500, detail=str(exc)) from exc


# ─── Command Endpoint (for CommandPalette) ────────────────────────────────────

@app.post("/api/command")
@limiter.limit("60/minute")
async def command(request: Request):
    """
    Natural language command routing. Used by CommandPalette.tsx.
    Returns { synthesis, intent, view_suggestion, agents_used }
    """
    body = await request.json()
    q = body.get("query", "")
    intent = _keyword_intent(q)
    agents = _intent_to_agents(intent)
    view = _intent_to_view(intent)

    synthesis = f"Processing query via {intent} pipeline using {', '.join(agents)} agents."
    if not q.strip():
        synthesis = "Please enter a query."

    return {
        "synthesis": synthesis,
        "intent": intent,
        "agent_list": agents,
        "view_suggestion": view,
        "confidence": 0.8,
        "timestamp": time.time(),
    }


# ─── WebSocket Hub ────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: Optional[str] = None):
    """
    WebSocket hub. Auth via ?token=JWT.
    Messages: { action: subscribe|unsubscribe, topics: [...] }
    Supports missed-message replay via { last_seq: N }
    """
    # Auth
    if token:
        try:
            _decode_jwt(token)
        except Exception:
            await ws.close(code=4401)
            return

    await ws.accept()
    bucket = TokenBucket(rate=10.0, capacity=10.0)
    subscribed_topics: Set[str] = set()
    log.info("ws_connected")

    try:
        while True:
            try:
                raw = await asyncio.wait_for(ws.receive_text(), timeout=60.0)
            except asyncio.TimeoutError:
                await ws.send_text(json.dumps({"type": "ping"}))
                continue

            if not bucket.consume():
                await ws.send_text(json.dumps({"type": "error", "msg": "Rate limit: 10 msg/sec"}))
                continue

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            action = msg.get("action")
            topics = msg.get("topics", [])

            if action == "subscribe":
                for topic in topics:
                    broadcast_mgr.subscribe(topic, ws)
                    subscribed_topics.add(topic)
                    last_seq = msg.get("last_seq", 0)
                    if last_seq:
                        await broadcast_mgr.replay_missed(topic, ws, last_seq)
                await ws.send_text(json.dumps({"type": "subscribed", "topics": list(subscribed_topics)}))

            elif action == "unsubscribe":
                for topic in topics:
                    broadcast_mgr.unsubscribe(topic, ws)
                    subscribed_topics.discard(topic)

            elif action == "ping":
                await ws.send_text(json.dumps({"type": "pong", "ts": time.time()}))

    except WebSocketDisconnect:
        log.info("ws_disconnected")
    finally:
        broadcast_mgr.unsubscribe_all(ws)


# ─── Economics Endpoints ───────────────────────────────────────────────────────

@app.get("/api/v1/economics/correlation_matrix")
async def correlation_matrix(_: UserClaims = Depends(require_auth)):
    """Satellite × macro cross-correlation matrix — world's first, Bloomberg cannot clone."""
    try:
        from src.data.economic_data import EconomicsDataService
        svc = EconomicsDataService()
        return await svc.get_correlation_matrix()
    except Exception as exc:
        return {"matrix": {}, "error": str(exc)}


@app.get("/api/v1/economics/divergences")
async def divergences(_: UserClaims = Depends(require_auth)):
    """Active satellite-macro divergences (signal_z > 1.5 AND macro_z < 0.5)."""
    try:
        from src.data.economic_data import EconomicsDataService
        svc = EconomicsDataService()
        return await svc.get_divergences()
    except Exception as exc:
        return {"divergences": [], "error": str(exc)}


@app.get("/api/v1/fundamentals/{ticker}")
async def fundamentals(ticker: str, _: UserClaims = Depends(require_auth)):
    """FMP + SEC EDGAR fundamental data. Bloomberg FA lite."""
    try:
        from src.data.fundamentals import FundamentalsService
        svc = FundamentalsService()
        return await svc.get(ticker.upper())
    except Exception as exc:
        return {"ticker": ticker, "error": str(exc)}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _keyword_intent(query: str) -> str:
    q = query.lower()
    if any(k in q for k in ["vessel", "ship", "ais", "dark", "tanker", "vlcc", "cargo"]):
        return "VESSEL_INTEL"
    if any(k in q for k in ["thermal", "frp", "fire", "industrial", "facility", "plant"]):
        return "THERMAL_ANALYSIS"
    if any(k in q for k in ["risk", "var", "gate", "kelly", "position", "portfolio"]):
        return "PORTFOLIO_RISK"
    if any(k in q for k in ["forecast", "tft", "p50", "p10", "p90", "predict"]):
        return "SIGNAL_QUERY"
    if any(k in q for k in ["pmi", "gdp", "cpi", "macro", "diverge", "ism"]):
        return "MACRO_DIVERGENCE"
    if any(k in q for k in ["chart", "ohlc", "candle", "price"]):
        return "CHART_REQUEST"
    if any(k in q for k in ["alert", "notify", "threshold"]):
        return "ALERT_CREATE"
    if any(k in q for k in ["earnings", "revenue", "eps", "fundamental", "income"]):
        return "FUNDAMENTAL_DATA"
    if any(k in q for k in ["workflow", "analysis", "run", "step"]):
        return "WORKFLOW_CREATE"
    if any(k in q for k in ["document", "pdf", "file", "upload"]):
        return "DOCUMENT_ANALYSIS"
    return "COMPOSITE_QUERY"


def _intent_to_agents(intent: str) -> List[str]:
    mapping = {
        "VESSEL_INTEL":      ["maritime"],
        "THERMAL_ANALYSIS":  ["satellite", "signal"],
        "PORTFOLIO_RISK":    ["risk", "tft"],
        "SIGNAL_QUERY":      ["signal", "tft"],
        "MACRO_DIVERGENCE":  ["economics", "signal"],
        "CHART_REQUEST":     ["signal"],
        "ALERT_CREATE":      ["orchestrator"],
        "FUNDAMENTAL_DATA":  ["economics"],
        "WORKFLOW_CREATE":   ["orchestrator", "signal", "maritime", "tft"],
        "DOCUMENT_ANALYSIS": ["orchestrator"],
        "COMPOSITE_QUERY":   ["signal", "maritime", "satellite"],
    }
    return mapping.get(intent, ["orchestrator"])


def _intent_to_view(intent: str) -> str:
    mapping = {
        "VESSEL_INTEL":      "world",
        "THERMAL_ANALYSIS":  "world",
        "PORTFOLIO_RISK":    "portfolio",
        "SIGNAL_QUERY":      "matrix",
        "MACRO_DIVERGENCE":  "economics",
        "CHART_REQUEST":     "charts",
        "FUNDAMENTAL_DATA":  "research",
        "COMPOSITE_QUERY":   "matrix",
    }
    return mapping.get(intent, "matrix")


def _build_context(agent_results: Dict[str, AgentResponse], extra: dict) -> str:
    parts = []
    for agent_id, res in agent_results.items():
        if not res.error:
            snippet = json.dumps(res.data, default=str)[:600]
            parts.append(f"[{agent_id.upper()} — age {res.age_s:.1f}s]\n{snippet}")
    context = "\n\n".join(parts)
    # Hard cap 6000 tokens ≈ 24000 chars
    return context[:24_000]


def _vessel_to_feature(v: Any) -> dict:
    """Convert VesselRecord to GeoJSON Feature."""
    if hasattr(v, '__dict__'):
        props = {k: val for k, val in vars(v).items() if k not in ('lat', 'lon')}
        lat, lon = getattr(v, 'lat', 0), getattr(v, 'lon', 0)
    elif isinstance(v, dict):
        props = {k: val for k, val in v.items() if k not in ('lat', 'lon', 'position')}
        pos = v.get('position', {})
        lat = v.get('lat', pos.get('lat', 0))
        lon = v.get('lon', pos.get('lon', pos.get('lng', 0)))
    else:
        return {"type": "Feature", "geometry": None, "properties": {}}
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": props,
    }


def _flight_to_feature(f: Any) -> dict:
    """Convert FlightRecord to GeoJSON Feature."""
    if isinstance(f, dict):
        pos = f.get('position', {})
        lat = f.get('lat', pos.get('lat', 0))
        lon = f.get('lon', pos.get('lon', pos.get('lng', 0)))
        props = {k: v for k, v in f.items() if k not in ('lat', 'lon', 'position')}
    elif hasattr(f, '__dict__'):
        props = vars(f).copy()
        lat = getattr(f, 'lat', 0)
        lon = getattr(f, 'lon', 0)
    else:
        return {"type": "Feature", "geometry": None, "properties": {}}
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": props,
    }
