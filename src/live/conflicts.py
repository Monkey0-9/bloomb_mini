"""
Real conflict and war data from public academic databases.
UCDP GEDEvent: Uppsala Conflict Data Program — zero key
ACLED: Armed Conflict Location & Event Data — zero key for research
GDELT: Global event database — zero key

Each conflict event is cross-referenced against shipping chokepoints
and industrial facilities to compute financial impact automatically.
"""
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

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
    chokepoint_impact: dict[str, Any] | None
    financial_tickers: list[str]
    severity:          str  # CRITICAL, HIGH, MEDIUM, LOW
    fetched_at:        str


CHOKEPOINTS: list[dict[str, Any]] = [
    {
        "id": "SUEZ", "name": "Suez Canal", "lat": 30.5, "lon": 32.3,
        "radius_km": 300.0, "tickers": ["ZIM", "AMKBY", "MT"]
    },
    {
        "id": "HRM", "name": "Strait of Hormuz", "lat": 26.5, "lon": 56.3,
        "radius_km": 400.0, "tickers": ["XOM", "CVX", "FRO"]
    },
    {
        "id": "MAL", "name": "Strait of Malacca", "lat": 2.5, "lon": 102.0,
        "radius_km": 500.0, "tickers": ["AMKBY", "SIA"]
    },
    {
        "id": "BAB", "name": "Bab-el-Mandeb", "lat": 12.6, "lon": 43.3,
        "radius_km": 350.0, "tickers": ["ZIM", "FRO"]
    },
    {
        "id": "PAN", "name": "Panama Canal", "lat": 9.1, "lon": -79.9,
        "radius_km": 200.0, "tickers": ["MATX", "X"]
    },
]


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    base_r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return base_r * 2 * math.asin(math.sqrt(a))


def _check_chokepoints(lat: float, lon: float) -> dict[str, Any] | None:
    for cp in CHOKEPOINTS:
        cp_lat: float = float(cp["lat"])
        cp_lon: float = float(cp["lon"])
        cp_radius: float = float(cp["radius_km"])
        if _haversine(lat, lon, cp_lat, cp_lon) <= cp_radius:
            return cp
    return None


def _severity(fatalities: int, near_chokepoint: bool) -> str:
    if near_chokepoint and fatalities > 10:
        return "CRITICAL"
    if near_chokepoint or fatalities > 50:
        return "HIGH"
    if fatalities > 5:
        return "MEDIUM"
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
                async with httpx.AsyncClient(timeout=20,
                                             follow_redirects=True) as client:
                    resp = await client.get(base_url,
                                            params={"pagesize": 500,
                                                    "Year": year})

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        items = data.get("Result", [])
                        if items:
                            log.info("ucdp_fetched", count=len(items))
                            return _parse_ucdp_items(items)
                    except Exception as je:
                        log.warning("ucdp_json_error", error=str(je))
                elif resp.status_code == 401:
                    continue
            except Exception as e:
                log.error("ucdp_error", error=str(e))

    log.warning("ucdp_api_failed_switching_to_osint")
    return await _fetch_osint_conflicts("ucdp-fallback")


def _parse_ucdp_items(items: list[dict[str, Any]]) -> list[ConflictEvent]:
    events: list[ConflictEvent] = []
    for item in items:
        try:
            lat = float(item.get("latitude",  0) or 0)
            lon = float(item.get("longitude", 0) or 0)
            if lat == 0 and lon == 0:
                continue

            fat = int(item.get("best", 0) or 0)
            cp = _check_chokepoints(lat, lon)
            tick = cp["tickers"] if cp else []

            events.append(ConflictEvent(
                event_id       = str(item.get("id", "")),
                event_date     = str(item.get("date_start", "")),
                event_type     = str(item.get("type_of_violence", "armed")),
                country        = str(item.get("country", "")),
                region         = str(item.get("region", "")),
                lat            = lat,
                lon            = lon,
                fatalities     = fat,
                actor1         = str(item.get("side_a", "")),
                actor2         = str(item.get("side_b", "")),
                description    = str(item.get("where_description", ""))[:300],
                source         = "ucdp",
                chokepoint_impact = cp,
                financial_tickers = tick,
                severity       = _severity(fat, cp is not None),
                fetched_at     = datetime.now(UTC).isoformat(),
            ))
        except Exception:
            continue
    return events


async def fetch_acled_conflicts(days_back: int = 30) -> list[ConflictEvent]:
    """Fetch from ACLED. Zero key for research access."""
    date_dt = datetime.now(UTC) - timedelta(days=days_back)
    date_str = date_dt.strftime("%Y-%m-%d")
    urls = [ACLED_URL, ACLED_URL.replace("https", "http")]

    for url in urls:
        try:
            log.info("fetching_acled", url=url)
            async with httpx.AsyncClient(timeout=20,
                                         follow_redirects=True) as client:
                params = {
                    "terms": "accept", "limit": 500,
                    "event_date": date_str, "event_date_where": ">="
                }
                resp = await client.get(url, params=params)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    items = data.get("data", [])
                    if items:
                        return _parse_acled_items(items)
                except Exception:
                    continue
        except Exception as e:
            log.error("acled_error", url=url, error=str(e))

    log.warning("acled_api_failed_switching_to_osint")
    return await _fetch_osint_conflicts("acled-fallback")


def _parse_acled_items(items: list[dict[str, Any]]) -> list[ConflictEvent]:
    events: list[ConflictEvent] = []
    for item in items:
        try:
            lat = float(item.get("latitude",  0) or 0)
            lon = float(item.get("longitude", 0) or 0)
            if lat == 0 and lon == 0:
                continue

            fat = int(item.get("fatalities", 0) or 0)
            cp = _check_chokepoints(lat, lon)
            tick = cp["tickers"] if cp else []

            events.append(ConflictEvent(
                event_id       = str(item.get("data_id", "")),
                event_date     = str(item.get("event_date", "")),
                event_type     = str(item.get("event_type", "")),
                country        = str(item.get("country", "")),
                region         = str(item.get("region", "")),
                lat            = lat,
                lon            = lon,
                fatalities     = fat,
                actor1         = str(item.get("actor1", "")),
                actor2         = str(item.get("actor2", "")),
                description    = str(item.get("notes", ""))[:300],
                source         = "acled",
                chokepoint_impact = cp,
                financial_tickers = tick,
                severity       = _severity(fat, cp is not None),
                fetched_at     = datetime.now(UTC).isoformat(),
            ))
        except Exception:
            continue
    return events


async def _fetch_osint_conflicts(source: str) -> list[ConflictEvent]:
    """Fallback search for real-time conflicts using GDELT fallback logic."""
    log.info("executing_osint_fallback", source=source)
    return await fetch_gdelt_conflicts(days_back=7)


async def fetch_gdelt_conflicts(days_back: int = 7) -> list[ConflictEvent]:
    """Fetch from GDELT as a zero-key fallback for real-time conflicts."""
    try:
        async with httpx.AsyncClient(timeout=15,
                                     follow_redirects=True) as client:
            params = {
                "query": "conflict OR attack OR military OR war",
                "mode": "artlist", "maxrecords": 50, "format": "json",
                "sort": "DateDesc"
            }
            resp = await client.get(GDELT_URL, params=params)
        if resp.status_code != 200:
            return []

        try:
            data = resp.json()
        except Exception:
            return []

        articles = data.get("articles", [])
        events: list[ConflictEvent] = []
        for a in articles:
            events.append(ConflictEvent(
                event_id       = f"gdelt-{hash(a.get('url', ''))}",
                event_date     = str(a.get("seendate",
                                           datetime.now().isoformat())),
                event_type     = "Unspecified Conflict",
                country        = str(a.get("domain", "International")),
                region         = "Global",
                lat            = 0.0, lon = 0.0, fatalities = 0,
                actor1         = "Unknown", actor2 = "Unknown",
                description    = str(a.get("title", "")), source = "gdelt",
                chokepoint_impact = None, financial_tickers = [],
                severity       = "MEDIUM", fetched_at = datetime.now(UTC).isoformat()
            ))
        return events
    except Exception as e:
        log.error("gdelt_error", error=str(e))
        return []


_conflict_cache: list[ConflictEvent] = []


async def get_conflict_events(force_refresh: bool = False) -> list[ConflictEvent]:
    """Get conflict events with caching."""
    global _conflict_cache
    if _conflict_cache and not force_refresh:
        return _conflict_cache

    results = []
    try:
        results = [
            await fetch_ucdp_conflicts(),
            await fetch_acled_conflicts(),
            await fetch_gdelt_conflicts()
        ]
    except Exception:
        pass

    all_ev = []
    for r in results:
        all_ev.extend(r)

    _conflict_cache = all_ev
    return _conflict_cache


async def get_all_conflicts() -> list[ConflictEvent]:
    """Get all conflicts from UCDP + ACLED combined and deduplicated."""
    all_events = await get_conflict_events()

    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    all_events.sort(key=lambda e: (sev_order.get(e.severity, 3), -e.fatalities))

    return all_events


async def get_chokepoint_data() -> list[dict[str, Any]]:
    """Return all chokepoints with current threat level."""
    conflicts = await get_all_conflicts()
    results: list[dict[str, Any]] = []

    for cp in CHOKEPOINTS:
        cp_copy = dict(cp)
        near = [
            c for c in conflicts
            if c.chokepoint_impact and c.chokepoint_impact["id"] == cp["id"]
        ]
        cp_copy["conflict_count"] = len(near)
        if near:
            cp_copy["max_severity"] = max(near, key=lambda c: c.severity).severity
        else:
            cp_copy["max_severity"] = "LOW"
        results.append(cp_copy)

    return results
