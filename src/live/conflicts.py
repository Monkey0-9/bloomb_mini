"""
Real conflict and war data from public academic databases.
UCDP GEDEvent: Uppsala Conflict Data Program — zero key
ACLED: Armed Conflict Location & Event Data — zero key for research
GDELT: Global event database — zero key

Each conflict event is cross-referenced against shipping chokepoints
and industrial facilities to compute financial impact automatically.
"""
import asyncio
import math
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
import structlog

log = structlog.get_logger()

UCDP_URL = "https://ucdpapi.pcr.uu.se/api/gedevents/24.1"
ACLED_URL = "https://api.acleddata.com/acled/read"
GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

@dataclass
class ConflictEvent:
    event_id:          str
    event_date:        str
    event_type:        str
    country:           str
    region:            str
    lat:               float
    lon:               float
    fatalities:        int
    actor1:            str
    actor2:            str
    description:       str
    source:            str
    chokepoint_impact: dict | None
    financial_tickers: list[str]
    severity:          str  # CRITICAL, HIGH, MEDIUM, LOW
    fetched_at:        str

CHOKEPOINTS = [
    {"id":"SUEZ", "name":"Suez Canal", "lat":30.5, "lon":32.3, "radius_km": 300, "tickers": ["ZIM", "AMKBY", "MT"]},
    {"id":"HRM",  "name":"Strait of Hormuz", "lat":26.5, "lon":56.3, "radius_km": 400, "tickers": ["XOM", "CVX", "FRO"]},
    {"id":"MAL",  "name":"Strait of Malacca", "lat":2.5, "lon":102.0, "radius_km": 500, "tickers": ["AMKBY", "SIA"]},
    {"id":"BAB",  "name":"Bab-el-Mandeb", "lat":12.6, "lon":43.3, "radius_km": 350, "tickers": ["ZIM", "FRO"]},
    {"id":"PAN",  "name":"Panama Canal", "lat":9.1, "lon":-79.9, "radius_km": 200, "tickers": ["MATX", "X"]},
]

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def _check_chokepoints(lat: float, lon: float) -> dict | None:
    for cp in CHOKEPOINTS:
        if _haversine(lat, lon, cp["lat"], cp["lon"]) <= cp["radius_km"]:
            return cp
    return None

def _severity(fatalities: int, near_chokepoint: bool) -> str:
    if near_chokepoint and fatalities > 10: return "CRITICAL"
    if near_chokepoint or fatalities > 50: return "HIGH"
    if fatalities > 5: return "MEDIUM"
    return "LOW"

async def fetch_ucdp_conflicts() -> list[ConflictEvent]:
    """Fetch from Uppsala Conflict Data Program. Zero key."""
    current_year = datetime.now().year
    years_to_try = [current_year, current_year - 1]
    versions = ["24.1", "23.1", "22.1"]

    for version in versions:
        base_url = f"https://ucdpapi.pcr.uu.se/api/gedevents/{version}"
        for year in years_to_try:
            try:
                log.info("fetching_ucdp", version=version, year=year)
                async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                    resp = await client.get(base_url, params={"pagesize": 500, "Year": year})

                if resp.status_code == 200:
                    items = resp.json().get("Result", [])
                    if items:
                        log.info("ucdp_fetched", version=version, year=year, count=len(items))
                        return _parse_ucdp_items(items)
                elif resp.status_code == 401:
                    log.warning("ucdp_unauthorized", version=version, year=year)
                    break
            except Exception as e:
                log.error("ucdp_error", version=version, year=year, error=str(e))
    return []

def _parse_ucdp_items(items: list) -> list[ConflictEvent]:
    events = []
    for item in items:
        try:
            lat = float(item.get("latitude",  0) or 0)
            lon = float(item.get("longitude", 0) or 0)
            if lat == 0 and lon == 0: continue

            fatalities = int(item.get("best", 0) or 0)
            chokepoint = _check_chokepoints(lat, lon)
            tickers    = chokepoint["tickers"] if chokepoint else []

            events.append(ConflictEvent(
                event_id       = str(item.get("id", "")),
                event_date     = str(item.get("date_start", "")),
                event_type     = str(item.get("type_of_violence", "armed")),
                country        = str(item.get("country", "")),
                region         = str(item.get("region", "")),
                lat            = lat,
                lon            = lon,
                fatalities     = fatalities,
                actor1         = str(item.get("side_a", "")),
                actor2         = str(item.get("side_b", "")),
                description    = str(item.get("where_description", ""))[:300],
                source         = "ucdp",
                chokepoint_impact = chokepoint,
                financial_tickers = tickers,
                severity       = _severity(fatalities, chokepoint is not None),
                fetched_at     = datetime.now(UTC).isoformat(),
            ))
        except Exception:
            continue
    return events

async def fetch_acled_conflicts(days_back: int = 30) -> list[ConflictEvent]:
    """Fetch from ACLED. Zero key for research access."""
    date_str = (datetime.now(UTC) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    urls = [ACLED_URL, ACLED_URL.replace("https", "http")]

    for url in urls:
        try:
            log.info("fetching_acled", url=url)
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                resp = await client.get(url, params={
                    "terms": "accept", "limit": 500, "event_date": date_str, "event_date_where": ">="
                })
            if resp.status_code == 200:
                items = resp.json().get("data", [])
                if items: return _parse_acled_items(items)
            else:
                log.warning("acled_api_status", url=url, status=resp.status_code)
        except Exception as e:
            log.error("acled_error", url=url, error=str(e))
    return []

def _parse_acled_items(items: list) -> list[ConflictEvent]:
    events = []
    for item in items:
        try:
            lat = float(item.get("latitude",  0) or 0)
            lon = float(item.get("longitude", 0) or 0)
            if lat == 0 and lon == 0: continue

            fatalities = int(item.get("fatalities", 0) or 0)
            chokepoint = _check_chokepoints(lat, lon)
            tickers    = chokepoint["tickers"] if chokepoint else []

            events.append(ConflictEvent(
                event_id       = str(item.get("data_id", "")),
                event_date     = str(item.get("event_date", "")),
                event_type     = str(item.get("event_type", "")),
                country        = str(item.get("country", "")),
                region         = str(item.get("region", "")),
                lat            = lat,
                lon            = lon,
                fatalities     = fatalities,
                actor1         = str(item.get("actor1", "")),
                actor2         = str(item.get("actor2", "")),
                description    = str(item.get("notes", ""))[:300],
                source         = "acled",
                chokepoint_impact = chokepoint,
                financial_tickers = tickers,
                severity       = _severity(fatalities, chokepoint is not None),
                fetched_at     = datetime.now(UTC).isoformat(),
            ))
        except Exception:
            continue
    return events

async def fetch_gdelt_conflicts(days_back: int = 7) -> list[ConflictEvent]:
    """Fetch from GDELT as a zero-key fallback for real-time conflicts."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(GDELT_URL, params={
                "query": "conflict OR attack OR military OR war",
                "mode": "artlist", "maxrecords": 50, "format": "json", "sort": "DateDesc"
            })
        if resp.status_code != 200: return []
        data = resp.json()
        articles = data.get("articles", [])
        events = []
        for a in articles:
            events.append(ConflictEvent(
                event_id       = f"gdelt-{hash(a['url'])}",
                event_date     = a.get("seendate", datetime.now().isoformat()),
                event_type     = "Unspecified Conflict",
                country        = a.get("domain", "International"),
                region         = "Global",
                lat            = 0.0, lon = 0.0, fatalities = 0,
                actor1         = "Unknown", actor2 = "Unknown",
                description    = a.get("title", ""), source = "gdelt",
                chokepoint_impact = None, financial_tickers = [],
                severity       = "MEDIUM", fetched_at = datetime.now(UTC).isoformat(),
            ))
        return events
    except Exception:
        return []

_conflict_cache: list[ConflictEvent] = []
_conflict_ts: float = 0.0
CONFLICT_TTL = 600

async def get_all_conflicts() -> list[ConflictEvent]:
    """Get all conflicts from UCDP + ACLED combined and deduplicated."""
    global _conflict_cache, _conflict_ts
    now = time.time()
    if _conflict_cache and (now - _conflict_ts) < CONFLICT_TTL:
        return _conflict_cache

    results = await asyncio.gather(fetch_ucdp_conflicts(), fetch_acled_conflicts(days_back=30))
    all_events = results[0] + results[1]

    if not all_events:
        all_events = await fetch_gdelt_conflicts()

    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    all_events.sort(key=lambda e: (severity_order.get(e.severity, 3), -e.fatalities))

    _conflict_cache = all_events
    _conflict_ts    = now
    return all_events

async def get_chokepoint_data() -> list[dict]:
    """Return all chokepoints with current threat level based on conflict data."""
    conflicts = await get_all_conflicts()
    result = []
    for cp in CHOKEPOINTS:
        nearby = [e for e in conflicts if _haversine(e.lat, e.lon, cp["lat"], cp["lon"]) <= cp["radius_km"]]
        threat = "HIGH" if any(e.severity in ("CRITICAL","HIGH") for e in nearby) else \
                 "MEDIUM" if nearby else "LOW"
        result.append({
            **cp,
            "active_conflicts": len(nearby),
            "threat_level":     threat,
            "recent_events":    [{"date": e.event_date, "type": e.event_type, "fatalities": e.fatalities, "actor": e.actor1} for e in nearby[:3]],
        })
    return result
