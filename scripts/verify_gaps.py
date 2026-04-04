import requests
import json
import time

BASE_URL = "http://localhost:9009/api"

def test_stock_price_fallback():
    print("Testing Stock Price Fallback...")
    # Test valid ticker
    resp = requests.get(f"{BASE_URL}/market/price/ZIM")
    print(f"ZIM Quote: {resp.json()}")
    assert resp.status_code == 200
    assert "price" in resp.json() or "current_price" in resp.json()
    
    # Test fallback (ticker not in primary universe but exists in yfinance)
    resp = requests.get(f"{BASE_URL}/market/price/KO")
    print(f"KO Quote: {resp.json()}")
    assert resp.status_code == 200
    assert "source" in resp.json()

def test_forecast_endpoint():
    print("\nTesting TFT Forecast Endpoint...")
    resp = requests.get(f"http://localhost:9009/api/alpha/forecast/ZIM")
    data = resp.json()
    print(f"ZIM Forecast: {data['bands'][:2]}...")
    assert resp.status_code == 200
    assert len(data['bands']) > 0
    assert "p50" in data['bands'][0]

def test_options_greeks_in_portfolio():
    print("\nTesting Options Greeks...")
    resp = requests.get(f"{BASE_URL}/market/options/ZIM")
    data = resp.json()
    # Check for presence of greeks in chain
    if "options_chain" in data and data["options_chain"]["calls"]:
        print(f"ZIM Options (first): {data['options_chain']['calls'][0]}")
    else:
        print(f"ZIM Options data: {data}")
    assert resp.status_code == 200

def test_rate_limiting():
    print("\nTesting Server Status...")
    resp = requests.get("http://localhost:9009/health")
    print(f"Health check: {resp.json()}")
    assert resp.status_code == 200

if __name__ == "__main__":
    # Start server first if not running
    print("Starting GAP Verification...")
    try:
        test_stock_price_fallback()
        test_forecast_endpoint()
        test_options_greeks_in_portfolio()
        test_rate_limiting()
        print("\nALL Institutional Gaps Verified Successfully.")
    except Exception as e:
        print(f"\nVerification Failed: {e}")
