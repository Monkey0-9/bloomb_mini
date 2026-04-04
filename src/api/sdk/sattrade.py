from typing import Any, cast

import requests


class SatTrade:
    """
    The Official SatTrade Python SDK (Institutional).
    Provides programmatic access to Satellite Alpha, Maritime AIS, and Macro Correlation.
    """

    def __init__(self, api_key: str | None = None, base_url: str = "http://localhost:9009"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def get_market_data(self, ticker: str) -> dict[str, Any]:
        """Fetches real-time institutional market data."""
        resp = self.session.get(f"{self.base_url}/api/market/price/{ticker}")
        resp.raise_for_status()
        return cast(dict[str, Any], resp.json())

    def get_signals(self) -> list[dict[str, Any]]:
        """Retrieves global signal conviction matrix."""
        resp = self.session.get(f"{self.base_url}/api/alpha/signals")
        resp.raise_for_status()
        return cast(list[dict[str, Any]], resp.json())

    def get_macro(self, indicator: str = "CPI") -> list[dict[str, Any]]:
        """Fetches macro-satellite correlation data."""
        resp = self.session.get(f"{self.base_url}/api/alpha/macro?indicator={indicator}")
        resp.raise_for_status()
        return cast(list[dict[str, Any]], resp.json())

    def execute_trade(self, ticker: str, qty: int, side: str = "BUY") -> dict[str, Any]:
        """
        Routes an order to the SatTrade OMS.
        WARNING: This executes real trades via the brokerage gateway.
        """
        payload = {"ticker": ticker, "qty": qty, "side": side}
        resp = self.session.post(f"{self.base_url}/api/execution/trade", json=payload)
        resp.raise_for_status()
        return cast(dict[str, Any], resp.json())

    def query_analyst(self, prompt: str) -> dict[str, Any]:
        """Interacts with the SatTrade AI Analyst for NLU intent synthesis."""
        payload = {"prompt": prompt}
        resp = self.session.post(f"{self.base_url}/api/command/route", json=payload)
        resp.raise_for_status()
        return cast(dict[str, Any], resp.json())

if __name__ == "__main__":
    # Example usage
    sdk = SatTrade()
    print("Testing SatTrade SDK Connection...")
    try:
        signals = sdk.get_signals()
        print(f"Retrieved {len(signals)} active alpha signals.")

        analysis = sdk.query_analyst("What is the risk profile for ZIM ships in Suez?")
        print(f"AI Analyst Intent: {analysis['intent']}")

    except Exception as e:
        print(f"SDK Error: {e}")
