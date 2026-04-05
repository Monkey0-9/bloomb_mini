import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.live.news import get_all_news
from src.live.thermal import get_global_thermal
from src.live.vessels import get_all_vessels
from src.live.aircraft import fetch_aircraft
from src.live.market import get_prices

async def test_sources():
    print("Testing News Source...")
    news = await get_all_news()
    print(f"  News count: {len(news)}")
    if news:
        print(f"  Sample: {news[0].title}")

    print("\nTesting Thermal Source...")
    thermal = await get_global_thermal()
    print(f"  Thermal count: {len(thermal)}")
    if thermal:
        print(f"  Sample: {thermal[0].facility_name}")

    print("\nTesting Vessel Source...")
    vessels = get_all_vessels()
    print(f"  Vessel count: {len(vessels)}")

    print("\nTesting Aircraft Source...")
    aircraft = fetch_aircraft()
    print(f"  Aircraft count: {len(aircraft)}")

    print("\nTesting Market Source...")
    prices = get_prices()
    print(f"  Prices count: {len(prices)}")
    if prices:
        print(f"  Sample: AAPL at {prices.get('AAPL', {}).price}")

if __name__ == "__main__":
    asyncio.run(test_sources())
