import asyncio
import pytest
from src.live.vessels import get_all_vessels
import structlog
import logging
import sys

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def test_get_all_vessels():
    print("Fetching vessels for zone 8 (Houston/Gulf)...")
    vessels = get_all_vessels(zones=[8])
    print(f"Found {len(vessels)} vessels.")
    assert isinstance(vessels, dict)

if __name__ == "__main__":
    test_get_all_vessels()