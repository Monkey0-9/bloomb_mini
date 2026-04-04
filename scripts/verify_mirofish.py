import asyncio
import os
from src.intelligence.mirofish_agent import agent

async def verify():
    print("--- MiroFish Market Forecast Verification ---")
    # Simulate a requirement
    req = "Predict impacts on Energy (XOM) and Shipping (ZIM) given the current Red Sea tensions."
    
    # We use the deterministic fallback if no API key is provided, 
    # but we test the orchestration logic.
    result = await agent.generate_forecast(req)
    
    print(f"Status: {result['status']}")
    print(f"GTFI: {result['gtfi']}")
    print(f"Confidence: {result['confidence']}%")
    print("\nREPORT PREVIEW:")
    print(result['report'][:500] + "...")
    
    if result['status'] in ['success', 'partial_success']:
        print("\n[VERIFICATION PASSED]")
    else:
        print("\n[VERIFICATION FAILED]")

if __name__ == "__main__":
    asyncio.run(verify())
