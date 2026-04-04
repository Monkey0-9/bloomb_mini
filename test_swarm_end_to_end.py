import asyncio
import pytest
from src.intelligence.swarm import run_swarm_simulation
import structlog
import logging
import sys
import json

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

@pytest.mark.asyncio
async def test_run_swarm_simulation():
    print("Running Swarm Simulation End-to-End...")
    result = await run_swarm_simulation()
    print("\n--- SIMULATION RESULT ---")
    print(f"GTFI Score: {result['gtfi_score']}")
    print(f"Total Agents: {result['total_agents']}")
    print(f"Impaired Agents: {result['impaired_agents']}")
    print("\nTop Predictions:")
    for p in result['predictions'][:3]:
        print(f"- [{p['action']}] {p.get('ticker') or p.get('region')} (Conf: {p['confidence']}%)")
        print(f"  {p['prediction']}")
    assert "gtfi_score" in result

if __name__ == "__main__":
    asyncio.run(test_run_swarm_simulation())