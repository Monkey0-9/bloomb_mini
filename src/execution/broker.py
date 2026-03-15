"""Real Alpaca Markets API integration. Paper trading only."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Literal

import httpx


@dataclass
class AccountInfo:
    account_id: str
    status: str
    cash: float
    equity: float
    buying_power: float


@dataclass
class BrokerOrder:
    order_id: str
    ticker: str
    qty: float
    side: str
    status: str
    limit_price: float | None = None
    filled_price: float | None = None


@dataclass
class CancelResult:
    order_id: str
    status: str


@dataclass
class Quote:
    ticker: str
    bid: float
    ask: float
    price: float
    volume: int
    timestamp: str


class AlpacaGateway:
    def __init__(self, env: Literal["paper"] = "paper") -> None:
        # "live" mode is intentionally not supported
        assert env == "paper", "Only paper trading is enabled."
        self.base_url = "https://paper-api.alpaca.markets"
        self.data_url = "https://data.alpaca.markets"
        api_key = os.environ.get("ALPACA_API_KEY", "")
        secret_key = os.environ.get("ALPACA_SECRET_KEY", "")
        if not api_key or not secret_key:
            raise OSError(
                "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in environment. "
                "Register for free at alpaca.markets"
            )
        self._headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key,
        }
        self._client = httpx.Client(headers=self._headers, timeout=30, follow_redirects=True)

    def _request(self, method: str, url: str, **kwargs) -> dict:
        for attempt in range(3):
            resp = self._client.request(method, url, **kwargs)
            if resp.status_code == 429:
                time.sleep(2**attempt * 2)
                continue
            resp.raise_for_status()
            return resp.json()
        raise RuntimeError(f"Request failed after 3 attempts: {url}")

    def get_account(self) -> AccountInfo:
        data = self._request("GET", f"{self.base_url}/v2/account")
        return AccountInfo(
            account_id=data["id"],
            status=data["status"],
            cash=float(data["cash"]),
            equity=float(data["equity"]),
            buying_power=float(data["buying_power"]),
        )

    def place_limit_order(
        self, symbol: str, qty: float, limit_price: float, side: Literal["buy", "sell"]
    ) -> BrokerOrder:
        data = self._request(
            "POST",
            f"{self.base_url}/v2/orders",
            json={
                "symbol": symbol,
                "qty": str(qty),
                "side": side,
                "type": "limit",
                "limit_price": str(limit_price),
                "time_in_force": "day",
            },
        )
        return BrokerOrder(
            order_id=data["id"],
            ticker=data["symbol"],
            qty=float(data["qty"]),
            side=data["side"],
            status=data["status"],
            limit_price=float(data.get("limit_price") or 0),
        )

    def cancel_order(self, order_id: str) -> CancelResult:
        try:
            self._request("DELETE", f"{self.base_url}/v2/orders/{order_id}")
            return CancelResult(order_id=order_id, status="cancelled")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                return CancelResult(order_id=order_id, status="already_filled")
            raise

    def get_positions(self) -> list[dict]:
        return self._request("GET", f"{self.base_url}/v2/positions")

    def get_quote(self, symbol: str) -> Quote:
        data = self._request("GET", f"{self.data_url}/v2/stocks/{symbol}/quotes/latest")
        q = data.get("quote", {})
        return Quote(
            ticker=symbol,
            bid=float(q.get("bp", 0)),
            ask=float(q.get("ap", 0)),
            price=(float(q.get("bp", 0)) + float(q.get("ap", 0))) / 2,
            volume=int(q.get("s", 0)),
            timestamp=q.get("t", ""),
        )
