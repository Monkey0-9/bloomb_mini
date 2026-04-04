from src.live.aircraft import fetch_aircraft
import structlog
import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def test():
    print("Fetching aircraft...")
    aircraft = fetch_aircraft()
    print(f"Total: {len(aircraft)}")
    for a in aircraft[:5]:
        print(f"[{a.category}] {a.callsign} ({a.country}): {a.alt_ft}ft")

if __name__ == "__main__":
    test()