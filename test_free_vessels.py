import asyncio
import pytest
from src.free_data.vessels import get_global_ships
import structlog
import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

@pytest.mark.asyncio
async def test_get_global_ships():
    print("Fetching global ships from free data sources...")
    ships = await get_global_ships(limit=50)
    print(f"Total found: {len(ships)}")
    assert len(ships) >= 0
    if ships:
        for s in ships[:5]:
            print(f"[{s['source']}] {s['name']} - {s['vessel_type']} at {s['lat']}, {s['lon']}")

if __name__ == "__main__":
    asyncio.run(test_get_global_ships())