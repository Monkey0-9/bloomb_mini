from __future__ import annotations

import json
import asyncio
import traceback
from typing import Any

import requests

# Emergency squawk codes
EMERGENCY_SQUAWKS: dict[str, str] = {
    "7700": "GENERAL EMERGENCY",
    "7600": "RADIO FAILURE",
    "7500": "HIJACK / UNLAWFUL INTERFERENCE",
}


def check_emergency_squawks() -> list[dict[str, Any]]:
    """Poll OpenSky globally and filter only for emergency squawks."""
    try:
        response = requests.get("https://opensky-network.org/api/states/all", timeout=10)
        response.raise_for_status()
        data = response.json()

        vectors = data.get("states", [])
        alerts: list[dict[str, Any]] = []
        for v in vectors:
            squawk = str(v[14]).strip() if v[14] else ""
            if squawk in EMERGENCY_SQUAWKS:
                icao24 = str(v[0]).strip().lower()
                callsign = str(v[1]).strip().upper() if v[1] else "UNKNOWN"
                longitude = float(v[5]) if v[5] else 0.0
                latitude = float(v[6]) if v[6] else 0.0
                altitude = float(v[7]) if v[7] else 0.0

                alerts.append(
                    {
                        "id": f"squawk-{icao24}",
                        "callsign": callsign,
                        "squawk": squawk,
                        "type": EMERGENCY_SQUAWKS[squawk],
                        "lat": latitude,
                        "lon": longitude,
                        "alt": altitude,
                    }
                )
        return alerts
    except Exception as e:
        print(f"[SQUAWK] Error fetching OpenSky Data: {e}")
        return []


async def run_squawk_pipeline(update_callback: Any) -> None:
    """Async loop that polls OpenSky for emergencies every 15 seconds."""
    print("[SQUAWK] Starting Emergency monitor...")
    seen_alerts: set[str] = set()

    while True:
        try:
            alerts = check_emergency_squawks()
            for al in alerts:
                incident_key = f"{al['id']}-{al['squawk']}"
                if incident_key not in seen_alerts:
                    print(
                        f"[SQUAWK] 🚨 EMERGENCY DETECTED: {al['callsign']} "
                        f"SQUAWK {al['squawk']} ({al['type']})"
                    )
                    seen_alerts.add(incident_key)
                    await update_callback(
                        {
                            "_topic": "alerts",
                            "level": "CRITICAL",
                            "emitter": "OPENSKY_SQUAWK_MONITOR",
                            "data": al,
                        }
                    )
        except Exception:
            traceback.print_exc()

        await asyncio.sleep(15)


if __name__ == "__main__":
    res = check_emergency_squawks()
    print(f"Found {len(res)} current emergency squawks globally.")
    if res:
        print(json.dumps(res, indent=2))
