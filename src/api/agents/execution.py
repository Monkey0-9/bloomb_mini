import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timezone
import yfinance as yf
from src.api.agents.base import BaseAgent

log = logging.getLogger(__name__)

# In-memory portfolio store (simulated paper trading)
_portfolio: dict = {"cash": 100_000.0, "positions": {}}


class ExecutionAgent(BaseAgent):
    """
    Simulated Order Management System (OMS).
    Uses yfinance for live pricing. 100% free, no broker API key needed.
    Operates as a paper-trading engine.
    """

    def __init__(self):
        super().__init__("EXECUTION_OMS")
        self.status = "ACTIVE"
        self.last_sync = datetime.now(timezone.utc)
        log.info("OMS: Paper trading engine initialised (yfinance pricing)")

    async def get_state(self) -> Dict[str, Any]:
        return {
            "cash": round(_portfolio["cash"], 2),
            "positions": _portfolio["positions"],
            "status": "PAPER_TRADING",
            "currency": "USD"
        }

    async def place_order(self, ticker: str, qty: int, side: str) -> Dict[str, Any]:
        """Simulate a market order using the live bid/ask from yfinance."""
        if not ticker:
            return {"error": "Ticker is required"}
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            price = info.last_price or 0.0
        except Exception as e:
            return {"error": f"Price fetch failed: {e}"}

        cost = price * qty
        if side.upper() == "BUY":
            if _portfolio["cash"] < cost:
                return {"error": "Insufficient paper capital"}
            _portfolio["cash"] -= cost
            _portfolio["positions"][ticker] = _portfolio["positions"].get(ticker, 0) + qty
        else:
            held = _portfolio["positions"].get(ticker, 0)
            if held < qty:
                return {"error": f"Only {held} shares held"}
            _portfolio["cash"] += cost
            _portfolio["positions"][ticker] = held - qty

        return {
            "order_id": f"PAPER-{int(datetime.utcnow().timestamp())}",
            "status": "FILLED",
            "ticker": ticker,
            "qty": qty,
            "side": side.upper(),
            "fill_price": round(price, 4),
            "total": round(cost, 2)
        }

    async def process_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task_type == "EXECUTE_TRADE":
            return await self.place_order(
                params.get("ticker", ""),
                params.get("qty", 1),
                params.get("side", "BUY")
            )
        if task_type == "GET_ACCOUNT":
            return await self.get_state()
        return {"error": "Unknown task type"}
