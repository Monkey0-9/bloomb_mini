from src.live.quakes import get_latest_quakes
import structlog
import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def test():
    print("Fetching latest quakes...")
    quakes = get_latest_quakes()
    for q in quakes[:5]:
        print(f"M{q.mag} - {q.place} ({q.ts})")

if __name__ == "__main__":
    test()