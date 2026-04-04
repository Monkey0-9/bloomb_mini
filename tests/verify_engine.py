import asyncio
import logging
from src.intelligence.engine import GlobalIntelligenceEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    engine = GlobalIntelligenceEngine()
    
    print("\n" + "="*50)
    print("SATTRADE GLOBAL INTELLIGENCE ENGINE VERIFICATION")
    print("="*50)

    try:
        print("\n[1] Testing Aircraft Tracking...")
        aircraft = await engine.get_global_aircraft()
        print(f"Found {len(aircraft)} aircraft.")
        if aircraft:
            print(f"Sample: {aircraft[0].callsign} ({aircraft[0].category}) at {aircraft[0].lat}, {aircraft[0].lon}")

        print("\n[2] Testing Thermal Discovery...")
        thermal = await engine.get_global_thermal()
        print(f"Discovered {len(thermal)} industrial hotspots.")
        if thermal:
            print(f"Sample: {thermal[0].facility_name} ({thermal[0].sector}) - Signal: {thermal[0].signal} ({thermal[0].anomaly_sigma} sigma)")

        print("\n[3] Testing Earthquake Intelligence...")
        quakes = await engine.get_global_earthquakes()
        print(f"Detected {len(quakes)} recent significant earthquakes.")
        if quakes:
            print(f"Sample: Mag {quakes[0].magnitude} at {quakes[0].place}")

        print("\n[4] Testing Conflict Intelligence...")
        conflicts = await engine.get_global_conflicts()
        print(f"Tracked {len(conflicts)} recent conflict events.")
        if conflicts:
            print(f"Sample: {conflicts[0].actor1} in {conflicts[0].country} - Fatalities: {conflicts[0].fatalities}")

        print("\n[5] Testing Satellite Orbits...")
        sats = await engine.get_global_satellites()
        print(f"Propagating {len(sats)} satellite orbits.")
        if sats:
            print(f"Sample: {sats[0].name} at {sats[0].lat}, {sats[0].lon}")

        print("\n[6] Testing News Feed...")
        from src.live.news import get_all_news
        news = await get_all_news()
        print(f"Aggregated {len(news)} news articles.")
        if news:
            print(f"Sample: {news[0].source}: {news[0].title[:60]}... Tickers: {news[0].tickers}")

        print("\n[7] Testing Unified World Report...")
        report = await engine.get_world_intelligence_report()
        print(f"Unified Threat Score: {report.threat_score}")
        print(f"Total Signals Generated: {len(report.signals)}")

        print("\nVERIFICATION COMPLETE: ALL SYSTEMS NOMINAL.")
    except Exception as e:
        print(f"\nVERIFICATION FAILED: {e}")
        logger.exception("Engine failure")

if __name__ == "__main__":
    asyncio.run(main())
