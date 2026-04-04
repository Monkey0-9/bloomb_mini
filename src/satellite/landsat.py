"""
USGS Landsat Scene Search — Free, no API key required.
Uses the USGS Earth Explorer JSON API to search for available
Landsat 8/9 scenes over industrial target areas.

Use cases:
- Secondary optical verification alongside Sentinel-2
- Cloud-free fallback imagery
- Long historical archive (1972-present) for baseline comparison
"""
from datetime import UTC, datetime, timedelta

import httpx

# USGS Machine-to-Machine (M2M) API
USGS_M2M_BASE = "https://m2m.cr.usgs.gov/api/api/json/stable"

# Key industrial areas to monitor via Landsat
LANDSAT_TARGETS = {
    "rotterdam_port": {
        "lat": 51.9225, "lon": 4.4792, "radius_km": 25,
        "name": "Port of Rotterdam Industrial Zone",
        "tickers": ["SHELL", "BP", "VOPAK.AS"],
    },
    "dunkirk_steel": {
        "lat": 51.033, "lon": 2.360, "radius_km": 10,
        "name": "ArcelorMittal Dunkirk Steelworks",
        "tickers": ["MT"],
    },
    "duisburg_steel": {
        "lat": 51.499, "lon": 6.769, "radius_km": 15,
        "name": "ThyssenKrupp Duisburg Steel Complex",
        "tickers": ["TKAMY"],
    },
    "sabine_pass_lng": {
        "lat": 29.726, "lon": -93.879, "radius_km": 10,
        "name": "Sabine Pass LNG Terminal",
        "tickers": ["LNG", "CQP"],
    },
    "singapore_refinery_cluster": {
        "lat": 1.292, "lon": 103.723, "radius_km": 20,
        "name": "Jurong Island Refinery & Petrochemical Complex",
        "tickers": ["EQNR", "TTE"],
    },
}


def search_landsat_scenes(
    target_key: str,
    max_cloud_cover: int = 30,
    days_back: int = 30,
) -> dict:
    """
    Search for recent Landsat 8/9 scenes over a target location.
    Uses the USGS EarthExplorer WRS-2 path/row lookup (public, no auth).

    Returns available scene metadata — actual download requires USGS M2M auth
    which is free to register at: https://ers.cr.usgs.gov/register
    """
    target = LANDSAT_TARGETS.get(target_key)
    if not target:
        return {"error": f"Unknown target: {target_key}"}

    lat, lon = target["lat"], target["lon"]
    date_end = datetime.now(UTC)
    date_start = date_end - timedelta(days=days_back)

    # Use USGS EarthExplorer public scene search (no auth needed for search)
    try:
        resp = httpx.get(
            "https://earthexplorer.usgs.gov/inventory/json/v/1.5.0/search",
            params={
                "jsonRequest": str({
                    "datasetName": "LANDSAT_OT_C2_L2",
                    "spatialFilter": {
                        "filterType": "mbr",
                        "lowerLeft": {"latitude": lat - 0.5, "longitude": lon - 0.5},
                        "upperRight": {"latitude": lat + 0.5, "longitude": lon + 0.5},
                    },
                    "temporalFilter": {
                        "startDate": date_start.strftime("%Y-%m-%d"),
                        "endDate": date_end.strftime("%Y-%m-%d"),
                    },
                    "maxCloudCover": max_cloud_cover,
                    "maxResults": 10,
                })
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        scenes = data.get("data", {}).get("results", [])
        return {
            "target_key": target_key,
            "target_name": target["name"],
            "lat": lat,
            "lon": lon,
            "tickers": target["tickers"],
            "scenes_found": len(scenes),
            "scenes": [
                {
                    "scene_id": s.get("displayId"),
                    "date": s.get("acquisitionDate"),
                    "cloud_cover": s.get("cloudCover"),
                    "path": s.get("wrsPath"),
                    "row": s.get("wrsRow"),
                    "thumbnail": s.get("browse", [{}])[0].get("thumbnailPath") if s.get("browse") else None,
                }
                for s in scenes
            ],
            "as_of": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        # Fallback: Return target metadata without live scene results
        return {
            "target_key": target_key,
            "target_name": target["name"],
            "lat": lat,
            "lon": lon,
            "tickers": target["tickers"],
            "scenes_found": 0,
            "scenes": [],
            "note": f"Live scene search requires USGS EarthExplorer auth — register free at ers.cr.usgs.gov. Error: {e}",
            "as_of": datetime.now(UTC).isoformat(),
        }


def get_all_landsat_coverage() -> list[dict]:
    """Get available Landsat coverage summary for all tracked industrial targets."""
    return [
        {
            "target_key": key,
            "target_name": meta["name"],
            "lat": meta["lat"],
            "lon": meta["lon"],
            "tickers": meta["tickers"],
            "revisit_days": 16,   # Landsat revisit cycle
            "resolution_m": 30,   # Landsat 30m pixel resolution
            "bands_available": ["B2 Blue", "B3 Green", "B4 Red", "B5 NIR", "B6 SWIR1", "B7 SWIR2", "B10 Thermal"],
            "archive_start": "1972",
        }
        for key, meta in LANDSAT_TARGETS.items()
    ]
