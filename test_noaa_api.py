import httpx
import json

def test():
    bbox = "-118.80,33.40,-117.80,33.90" # LA
    url = "https://api.coast.noaa.gov/query/v1.0/ais/vessels"
    try:
        resp = httpx.get(url, params={"bbox": bbox, "limit": 5, "output": "json"}, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(json.dumps(resp.json(), indent=2)[:500])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()