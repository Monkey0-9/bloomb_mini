import asyncio
import pytest
from src.intelligence.swarm import run_swarm_simulation

@pytest.mark.async_io
async def test_swarm_simulation_logic():
    """
    Test the swarm simulation logic end-to-end.
    Ensures that the GTFI is calculated and predictions are generated.
    """
    results = await run_swarm_simulation()
    
    assert "gtfi" in results
    assert "predictions" in results
    assert "regional_hotspots" in results
    
    print(f"\nFinal GTFI: {results['gtfi']}")
    print(f"Predictions Count: {len(results['predictions'])}")
    
    # Verify that predictions have the expected structure
    for p in results['predictions']:
        assert "ticker" in p
        assert "prediction" in p
        assert "confidence" in p
        assert "action" in p
        assert "divergence_score" in p

if __name__ == "__main__":
    asyncio.run(test_swarm_simulation_logic())
