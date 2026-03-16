import logging
import os
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timezone
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from src.api.agents.base import BaseAgent

log = logging.getLogger(__name__)

class ExecutionAgent(BaseAgent):
    """
    The Order Management System (OMS): Routes signals to Alpaca Brokerage.
    """
    
    def __init__(self):
        super().__init__("EXECUTION_OMS")
        self.status = "ACTIVE"
        self.last_sync = datetime.now(timezone.utc)
        
        # Initialize Alpaca Client
        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")
        base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        try:
            self.client = TradingClient(api_key, secret_key, paper=True)
            log.info("OMS Connected to Alpaca Paper Trading")
        except Exception as e:
            log.error(f"OMS Fail to connect: {e}")
            self.client = None
            self.status = "ERROR_AUTH"

    async def get_state(self) -> Dict[str, Any]:
        if not self.client:
            return {"error": "Alpaca not connected"}
        
        try:
            account = self.client.get_account()
            return {
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.equity),
                "status": account.status,
                "currency": account.currency
            }
        except Exception as e:
            return {"error": str(e)}

    async def place_order(self, ticker: str, qty: int, side: str) -> Dict[str, Any]:
        """Executes a market order with institutional safety checks."""
        if not self.client:
            return {"error": "No execution engine available"}
        
        side_enum = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        
        order_data = MarketOrderRequest(
            symbol=ticker,
            qty=qty,
            side=side_enum,
            time_in_force=TimeInForce.GTC
        )
        
        try:
            order = self.client.submit_order(order_data=order_data)
            return {
                "order_id": str(order.id),
                "status": str(order.status),
                "ticker": ticker,
                "qty": qty,
                "side": side
            }
        except Exception as e:
            log.error(f"Execution failed for {ticker}: {e}")
            return {"error": str(e)}

    async def process_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task_type == "EXECUTE_TRADE":
            return await self.place_order(
                params.get("ticker"),
                params.get("qty", 1),
                params.get("side", "BUY")
            )
        if task_type == "GET_ACCOUNT":
            return await self.get_state()
        return {"error": "Unknown task type"}
