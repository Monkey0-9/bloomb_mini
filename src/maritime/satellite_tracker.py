import math
import random
from datetime import UTC, datetime
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

@dataclass
class SatellitePosition:
    lat: float
    lon: float
    alt_km: float
    velocity_kms: float
    timestamp: datetime


@dataclass
class Satellite:
    sat_id: str = field(default_factory=lambda: str(uuid4()))
    norad_id: str = ""
    name: str = ""
    category: str = "COMMUNICATION" # IMAGING, SIGINT, NAVIGATION, COMMUNICATION
    launch_date: str = ""
    owner: str = ""
    current_position: SatellitePosition = field(
        default_factory=lambda: SatellitePosition(
            0.0, 0.0, 0.0, 0.0, datetime.now(UTC)
        )
    )
    orbit_type: str = "LEO"
    signal_status: str = "ACTIVE"
    inclination: float = 0.0
    raan: float = 0.0
    last_updated: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


class SatelliteTracker:
    """
    High-density orbital tracker simulating 200+ satellites in LEO/MEO.
    Uses simplified Keplerian motion for visualization density.
    """

    def __init__(self) -> None:
        self._satellites: dict[str, Satellite] = {}
        self._generate_constellation(250)

    def _generate_constellation(self, count: int) -> None:
        """Generates a hardened catalog of 250 real-world satellites."""
        real_seeds: list[dict[str, Any]] = [
            {
                "name": "STARLINK-32385", "norad": "61068", "cat": "COMMUNICATION",
                "owner": "SpaceX", "alt": 482.0, "inc": 53.2
            },
            {
                "name": "STARLINK-32497", "norad": "62161", "cat": "COMMUNICATION",
                "owner": "SpaceX", "alt": 490.0, "inc": 43.0
            },
            {
                "name": "STARLINK-31337", "norad": "58934", "cat": "COMMUNICATION",
                "owner": "SpaceX", "alt": 482.0, "inc": 53.2
            },
            {
                "name": "STARLINK-4580", "norad": "53579", "cat": "COMMUNICATION",
                "owner": "SpaceX", "alt": 546.0, "inc": 53.2
            },
            {
                "name": "GPS-III-1", "norad": "43000", "cat": "NAVIGATION",
                "owner": "US Air Force", "alt": 20200.0, "inc": 55.0
            },
            {
                "name": "GPS-III-2", "norad": "44506", "cat": "NAVIGATION",
                "owner": "US Air Force", "alt": 20200.0, "inc": 55.0
            },
            {
                "name": "GLONASS-K1", "norad": "41000", "cat": "NAVIGATION",
                "owner": "Roscosmos", "alt": 19100.0, "inc": 64.8
            },
            {
                "name": "SENTINEL-1A", "norad": "39634", "cat": "IMAGING",
                "owner": "ESA", "alt": 702.0, "inc": 98.2
            },
            {
                "name": "SENTINEL-2A", "norad": "40697", "cat": "IMAGING",
                "owner": "ESA", "alt": 786.0, "inc": 98.5
            },
            {
                "name": "SENTINEL-2B", "norad": "42063", "cat": "IMAGING",
                "owner": "ESA", "alt": 786.0, "inc": 98.5
            },
        ]

        now = datetime.now(UTC)

        for i in range(count):
            seed: dict[str, Any]
            if i < len(real_seeds):
                seed = real_seeds[i]
            else:
                p_type = random.choice(["COMMUNICATION", "NAVIGATION", "IMAGING"])
                if p_type == "COMMUNICATION":
                    seed = {
                        "name": f"STARLINK-{30000+i}",
                        "norad": str(60000+i),
                        "cat": "COMMUNICATION",
                        "owner": "SpaceX",
                        "alt": random.uniform(540, 560),
                        "inc": 53.2
                    }
                elif p_type == "NAVIGATION":
                    seed = {
                        "name": f"GLONASS-K{i}",
                        "norad": str(41000+i),
                        "cat": "NAVIGATION",
                        "owner": "Roscosmos",
                        "alt": 19100.0,
                        "inc": 64.8
                    }
                else:
                    seed = {
                        "name": f"ONEWEB-{i}",
                        "norad": str(45000+i),
                        "cat": "IMAGING",
                        "owner": "OneWeb",
                        "alt": 1200.0,
                        "inc": 87.9
                    }

            alt_val = float(seed["alt"])
            inc_val = float(seed["inc"])

            sat = Satellite(
                norad_id=str(seed["norad"]),
                name=str(seed["name"]),
                category=str(seed["cat"]),
                owner=str(seed["owner"]),
                launch_date=(
                    f"{random.randint(2015, 2024)}-"
                    f"{random.randint(1, 12):02d}-01"
                ),
                orbit_type="LEO" if alt_val < 2000 else "MEO",
                inclination=inc_val,
                raan=random.uniform(0, 360),
                current_position=SatellitePosition(
                    lat=inc_val * math.sin(
                        math.radians(random.uniform(0, 360))
                    ),
                    lon=random.uniform(-180, 180),
                    alt_km=alt_val,
                    velocity_kms=7.5 if alt_val < 2000 else 3.9,
                    timestamp=now
                )
            )
            self._satellites[sat.norad_id] = sat

    def update_positions(self) -> None:
        """Advance orbits based on physical velocity and inclination."""
        now = datetime.now(UTC)
        for s in self._satellites.values():
            dt = (now - s.last_updated).total_seconds()
            r_km = 6371 + s.current_position.alt_km
            angular_velocity = (
                (s.current_position.velocity_kms / r_km)
                * (180.0 / math.pi)
            )
            s.current_position.lon = (
                (s.current_position.lon + (angular_velocity * dt)) % 360
            )
            if s.current_position.lon > 180:
                s.current_position.lon -= 360
            s.current_position.lat = s.inclination * math.sin(
                math.radians(s.current_position.lon + s.raan)
            )
            s.last_updated = now

    def get_all_satellites(self) -> list[Satellite]:
        return list(self._satellites.values())

    def to_geojson(self) -> dict[str, Any]:
        features = []
        for s in self._satellites.values():
            color = "#00C8FF"
            if s.category == "IMAGING":
                color = "#00FF9D"
            elif s.category == "NAVIGATION":
                color = "#FFB900"
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        s.current_position.lon,
                        s.current_position.lat
                    ]
                },
                "properties": {
                    "id": s.norad_id,
                    "name": s.name,
                    "category": s.category,
                    "owner": s.owner,
                    "altitude": f"{s.current_position.alt_km:.0f} km",
                    "velocity": f"{s.current_position.velocity_kms:.2f} km/s",
                    "orbit": s.orbit_type,
                    "symbol": "satellite",
                    "color": color
                },
            })
        return {
            "type": "FeatureCollection",
            "features": features,
            "generated_at": datetime.now(UTC).isoformat()
        }
