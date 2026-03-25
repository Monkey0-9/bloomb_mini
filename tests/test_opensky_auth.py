
import asyncio
import os
import httpx
from dotenv import load_dotenv

async def test_opensky():
    load_dotenv()
    user = os.getenv("OPENSKY_USERNAME")
    pw = os.getenv("OPENSKY_PASSWORD")
    
    print(f"Testing OpenSky with User: {user}")
    
    url = "https://opensky-network.org/api/states/all"
    auth = httpx.BasicAuth(user, pw) if user and pw else None
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.get(url, auth=auth)
            print(f"Status Code: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                states = data.get('states', [])
                print(f"Successfully fetched {len(states) if states else 0} states.")
            else:
                print(f"Error: {r.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_opensky())
