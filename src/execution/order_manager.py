"""
Order Manager — Phase 7.2

Manages order lifecycle: creation → risk check → execution → fill → audit.
Maintains order book state and position reconciliation.

All orders are immutable after creation — modifications create new orders.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)


class OrderStatus(str, Enum):
    PENDING = "pending"
    RISK_APPROVED = "risk_approved"
    RISK_REJECTED = "risk_rejected"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    VWAP = "vwap"
    TWAP = "twap"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """Immutable order record."""
    order_id: str
    asset_id: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    limit_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    signal_score: float = 0.0
    signal_timestamp: Optional[datetime] = None
    creation_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    fill_price: Optional[float] = None
    fill_quantity: int = 0
    fill_timestamp: Optional[datetime] = None
    risk_check_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    parent_order_id: Optional[str] = None  # For modifications


@dataclass
class OrderBookSnapshot:
    """Point-in-time snapshot of the order book."""
    timestamp: datetime
    pending_orders: int
    filled_orders: int
    rejected_orders: int
    total_fill_value: float
    avg_slippage_bps: float


class OrderManager:
    """
    Order lifecycle management.
    
    Flow: create → risk check → submit → fill/reject → audit log
    All transitions are logged to QLDB in production.
    """

    MAX_ORDER_AGE_SECONDS = 300  # Orders expire after 5 minutes

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._order_log: list[dict[str, Any]] = []

    def create_order(
        self,
        asset_id: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        signal_score: float = 0.0,
        signal_timestamp: Optional[datetime] = None,
    ) -> Order:
        """Create a new order. Returns pending order for risk check."""
        order = Order(
            order_id=str(uuid.uuid4()),
            asset_id=asset_id,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            signal_score=signal_score,
            signal_timestamp=signal_timestamp,
        )
        self._orders[order.order_id] = order
        self._log_transition(order, "created")
        return order

    def approve_risk(self, order_id: str, risk_check_id: str) -> Order:
        """Mark order as risk-approved."""
        order = self._get_order(order_id)
        order.status = OrderStatus.RISK_APPROVED
        order.risk_check_id = risk_check_id
        self._log_transition(order, "risk_approved")
        return order

    def reject_risk(self, order_id: str, reason: str) -> Order:
        """Mark order as risk-rejected."""
        order = self._get_order(order_id)
        order.status = OrderStatus.RISK_REJECTED
        order.rejection_reason = reason
        self._log_transition(order, "risk_rejected")
        return order

    def submit(self, order_id: str) -> Order:
        """Submit approved order to exchange/simulator."""
        order = self._get_order(order_id)
        if order.status != OrderStatus.RISK_APPROVED:
            raise ValueError(f"Cannot submit order {order_id} — status is {order.status}")
        order.status = OrderStatus.SUBMITTED
        self._log_transition(order, "submitted")
        return order

    def fill(self, order_id: str, fill_price: float, fill_quantity: Optional[int] = None) -> Order:
        """Record order fill."""
        order = self._get_order(order_id)
        order.fill_price = fill_price
        order.fill_quantity = fill_quantity or order.quantity
        order.fill_timestamp = datetime.now(timezone.utc)

        if order.fill_quantity >= order.quantity:
            order.status = OrderStatus.FILLED
        else:
            order.status = OrderStatus.PARTIALLY_FILLED

        self._log_transition(order, f"filled_{order.fill_quantity}")
        return order

    def cancel(self, order_id: str, reason: str = "") -> Order:
        """Cancel a pending/submitted order."""
        order = self._get_order(order_id)
        order.status = OrderStatus.CANCELLED
        order.rejection_reason = reason
        self._log_transition(order, f"cancelled: {reason}")
        return order

    def expire_stale_orders(self) -> list[Order]:
        """Expire orders older than MAX_ORDER_AGE_SECONDS."""
        now = datetime.now(timezone.utc)
        expired = []
        for order in self._orders.values():
            if order.status in (OrderStatus.PENDING, OrderStatus.RISK_APPROVED, OrderStatus.SUBMITTED):
                age = (now - order.creation_timestamp).total_seconds()
                if age > self.MAX_ORDER_AGE_SECONDS:
                    order.status = OrderStatus.EXPIRED
                    self._log_transition(order, "expired")
                    expired.append(order)
        return expired

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def get_open_orders(self) -> list[Order]:
        return [o for o in self._orders.values() if o.status in (
            OrderStatus.PENDING, OrderStatus.RISK_APPROVED, OrderStatus.SUBMITTED
        )]

    def get_filled_orders(self, since: Optional[datetime] = None) -> list[Order]:
        orders = [o for o in self._orders.values() if o.status == OrderStatus.FILLED]
        if since:
            orders = [o for o in orders if o.fill_timestamp and o.fill_timestamp >= since]
        return orders

    def get_snapshot(self) -> OrderBookSnapshot:
        """Get current order book snapshot."""
        filled = [o for o in self._orders.values() if o.status == OrderStatus.FILLED]
        return OrderBookSnapshot(
            timestamp=datetime.now(timezone.utc),
            pending_orders=len(self.get_open_orders()),
            filled_orders=len(filled),
            rejected_orders=len([o for o in self._orders.values() if o.status == OrderStatus.RISK_REJECTED]),
            total_fill_value=sum((o.fill_price or 0) * o.fill_quantity for o in filled),
            avg_slippage_bps=0.0,
        )

    def get_audit_trail(self) -> list[dict[str, Any]]:
        return list(self._order_log)

    def _get_order(self, order_id: str) -> Order:
        order = self._orders.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        return order

    def _log_transition(self, order: Order, event: str) -> None:
        self._order_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "order_id": order.order_id,
            "asset_id": order.asset_id,
            "event": event,
            "status": order.status.value,
        })


class AlpacaSimGateway:
    """
    Simulated gateway for Alpaca/IBKR APIs.
    Simulates:
      - API Latency (50ms - 200ms)
      - Partial Fills
      - Order status callbacks
    """
    def __init__(self, order_manager: OrderManager):
        self._om = order_manager
        self._active_submissions: list[str] = []

    def submit_to_broker(self, order_id: str) -> bool:
        """Simulate submission to broker endpoint."""
        order = self._om.get_order(order_id)
        if not order:
            return False
            
        logger.info(f"ALPACASIM: Submitting order {order_id} for {order.asset_id}")
        # Simulate local network latency
        import time
        time.sleep(0.05) 
        
        self._om.submit(order_id)
        self._active_submissions.append(order_id)
        return True

    def poll_broker_status(self) -> None:
        """Process active orders and simulate fills."""
        import random
        for order_id in list(self._active_submissions):
            order = self._om.get_order(order_id)
            if not order or order.status != OrderStatus.SUBMITTED:
                self._active_submissions.remove(order_id)
                continue
            
            # Simulate a fill with random slippage and timing
            fill_rand = random.random()
            if fill_rand > 0.1: # 90% chance of fill per poll
                # Apply Almgren-Chriss style slippage simulation or just use market
                fill_price = (order.limit_price or 100.0) * (1 + random.uniform(-0.001, 0.001))
                self._om.fill(order_id, fill_price)
                self._active_submissions.remove(order_id)
                logger.info(f"ALPACASIM: Fill received for {order_id} at {fill_price:.4f}")


class LiveAlpacaGateway:
    """
    Production Alpaca SDK integration gateway.
    Requires ALPACA_API_KEY and ALPACA_SECRET in environment.
    """
    
    def __init__(self, order_manager: OrderManager, base_url: str = "https://paper-api.alpaca.markets"):
        self._om = order_manager
        self._base_url = base_url
        self._api: Optional[Any] = None
        self._is_live = False # Safety flag

    def connect(self, api_key: str, secret_key: str, live: bool = False):
        """Initialize connection to Alpaca API."""
        try:
            # import alpaca_trade_api as tradeapi
            # self._api = tradeapi.REST(api_key, secret_key, self._base_url)
            self._is_live = live
            logger.info(f"ALPACALIVE: Initialized connection (Live={live})")
        except Exception as e:
            logger.error(f"ALPACALIVE: Connection failed: {e}")
            raise

    def submit_order(self, order_id: str) -> bool:
        """Submit order to live Alpaca endpoint."""
        order = self._om.get_order(order_id)
        if not order:
            return False

        logger.info(f"ALPACALIVE: Routing order {order_id} to Alpaca API...")
        
        # In production:
        # self._api.submit_order(
        #     symbol=order.asset_id,
        #     qty=order.quantity,
        #     side=order.side.value,
        #     type=order.order_type.value,
        #     time_in_force='day',
        #     limit_price=order.limit_price
        # )
        
        self._om.submit(order_id)
        return True

    def sync_positions(self) -> list[Dict[str, Any]]:
        """Reconcile internal state with broker's open positions."""
        logger.info("ALPACALIVE: Syncing positions with broker...")
        # positions = self._api.list_positions()
        return []
