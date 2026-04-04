import httpx
import json

def check_api():
    base_url = "http://localhost:9009"
    endpoints = [
        "/health",
        "/api/aircraft",
        "/api/vessels",
        "/api/satellites",
        "/api/thermal",
        "/api/news",
        "/api/macro",
        "/api/portfolio",
        "/api/insider",
        "/api/darkpool",
        "/api/workflows"
    ]
    
    for ep in endpoints:
        try:
            print(f"Checking {ep}...")
            resp = httpx.get(f"{base_url}{ep}", timeout=30.0)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    keys = list(data.keys())
                    print(f"  Keys: {keys}")
                    if 'count' in data: print(f"  Count: {data['count']}")
                    if 'vessels' in data: print(f"  Vessels: {len(data['vessels'])}")
                    if 'satellites' in data: print(f"  Satellites: {len(data['satellites'])}")
                    if 'news' in data: print(f"  News: {len(data['news'])}")
                elif isinstance(data, list):
                    print(f"  Length: {len(data)}")
            else:
                print(f"  Error: {resp.text[:100]}")
        except Exception as e:
            print(f"  Failed: {e}")

if __name__ == "__main__":
    check_api()
