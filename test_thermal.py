import asyncio
from src.live.thermal import get_global_thermal
import structlog
import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def test():
    print("Fetching top 10 thermal anomalies...")
    clusters = await get_global_thermal(top_n=10)
    for c in clusters:
        print(f"[{c.signal}] {c.facility_name} ({c.country}): {c.anomaly_sigma} sigma")

if __name__ == "__main__":
    asyncio.run(test())
