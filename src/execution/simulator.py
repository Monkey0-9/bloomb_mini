"""
Paper Trading Simulator — Phase 7.1

Simulated execution engine for the paper/shadow trading phase.
Operates on live signals against real market data but places
no actual orders. All "trades" are logged to the audit trail.

SLA: satellite acquisition → tradeable signal ≤ 6 hours (P95).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

from src.execution.position_sizing import PositionTarget
from src.execution.risk_engine import RiskEngine, PortfolioPosition, PreTradeCheckResult

logger = logging.getLogger(__name__)


@dataclass
class SimulatedOrder:
    """A simulated paper trade."""
    order_id: str
    asset_id: str
    side: str  # "buy" or "sell"
    quantity: int
    price: float
    fill_price: float
    slippage_bps: float
    commission: float
    timestamp_utc: datetime
    signal_timestamp: datetime
    signal_to_trade_latency_s: float
    risk_check_passed: bool
    pre_trade_result: Optional[PreTradeCheckResult] = None


@dataclass
class SimulatedPortfolio:
    """Current state of the paper portfolio."""
    cash: float
    positions: dict[str, PortfolioPosition] = field(default_factory=dict)
    nav: float = 0.0
    nav_history: list[float] = field(default_factory=list)
    trade_history: list[SimulatedOrder] = field(default_factory=list)
    pnl_daily: list[float] = field(default_factory=list)
    start_nav: float = 10_000_000.0

    def update_nav(self, market_prices: dict[str, float]) -> float:
        """Recalculate NAV based on current market prices."""
        position_value = sum(
            pos.quantity * market_prices.get(pos.asset_id, pos.current_price)
            for pos in self.positions.values()
        )
        self.nav = self.cash + position_value
        self.nav_history.append(self.nav)
        return self.nav

    def get_daily_return(self) -> float:
        if len(self.nav_history) < 2:
            return 0.0
        return (self.nav_history[-1] - self.nav_history[-2]) / self.nav_history[-2]

    def get_positions_list(self) -> list[PortfolioPosition]:
        return list(self.positions.values())


class PaperTradingSimulator:
    """
    Paper trading engine for shadow-running the strategy against live data.
    
    Every simulated trade passes through the full risk engine.
    Slippage model: spread (5 bps) + market impact (sqrt model).
    """

    DEFAULT_SPREAD_BPS = 5.0
    DEFAULT_COMMISSION_BPS = 3.0
    MARKET_IMPACT_COEFF = 0.1  # Almgren-Chriss constant

    def __init__(
        self,
        initial_nav: float = 10_000_000.0,
        risk_engine: Optional[RiskEngine] = None,
    ) -> None:
        self._risk_engine = risk_engine or RiskEngine()
        self._portfolio = SimulatedPortfolio(
            cash=initial_nav,
            nav=initial_nav,
            start_nav=initial_nav,
        )
        self._portfolio.nav_history.append(initial_nav)

    @property
    def portfolio(self) -> SimulatedPortfolio:
        return self._portfolio

    def execute_targets(
        self,
        targets: list[PositionTarget],
        market_prices: dict[str, float],
        market_adtv: dict[str, float],
        asset_sectors: dict[str, str],
        asset_countries: dict[str, str],
        signal_timestamp: datetime,
        current_time: Optional[datetime] = None,
    ) -> list[SimulatedOrder]:
        """
        Execute position targets through the paper trading engine.
        All orders pass through pre-trade risk checks.
        """
        now = current_time or datetime.now(timezone.utc)
        orders: list[SimulatedOrder] = []

        for target in targets:
            price = market_prices.get(target.asset_id, 0)
            if price <= 0:
                logger.warning(f"No market price for {target.asset_id} — skipping")
                continue

            # Determine order side and quantity
            current_pos = self._portfolio.positions.get(target.asset_id)
            current_qty = current_pos.quantity if current_pos else 0
            delta_qty = target.target_shares - current_qty

            if delta_qty == 0:
                continue

            side = "buy" if delta_qty > 0 else "sell"
            abs_qty = abs(delta_qty)

            # Run pre-trade risk checks
            latency = (now - signal_timestamp).total_seconds()

            # Build current positions for risk check
            positions_list = self._portfolio.get_positions_list()
            # Update/add the position metadata for risk checking
            if current_pos is None and target.asset_id in market_prices:
                # New position — create temporary for risk check
                temp_pos = PortfolioPosition(
                    asset_id=target.asset_id,
                    quantity=0,
                    market_value=0,
                    gics_sector=asset_sectors.get(target.asset_id, "Unknown"),
                    country=asset_countries.get(target.asset_id, "US"),
                    adtv_30d=market_adtv.get(target.asset_id, 1_000_000),
                    current_price=price,
                )
                positions_list.append(temp_pos)

            risk_result = self._risk_engine.run_pretrade_checks(
                asset_id=target.asset_id,
                proposed_quantity=abs_qty,
                proposed_price=price,
                signal_age_seconds=int(latency),
                current_positions=positions_list,
            )

            if not risk_result.all_passed:
                logger.warning(
                    f"PAPER TRADE BLOCKED: {target.asset_id} — {risk_result.block_reason}"
                )
                orders.append(SimulatedOrder(
                    order_id=risk_result.order_id,
                    asset_id=target.asset_id,
                    side=side,
                    quantity=abs_qty,
                    price=price,
                    fill_price=0,
                    slippage_bps=0,
                    commission=0,
                    timestamp_utc=now,
                    signal_timestamp=signal_timestamp,
                    signal_to_trade_latency_s=latency,
                    risk_check_passed=False,
                    pre_trade_result=risk_result,
                ))
                continue

            # Compute execution price with slippage
            fill_price, slippage_bps = self._simulate_execution(
                price, abs_qty, market_adtv.get(target.asset_id, 1_000_000), side,
            )

            commission = abs_qty * fill_price * self.DEFAULT_COMMISSION_BPS / 10000

            # Update portfolio
            if side == "buy":
                self._portfolio.cash -= abs_qty * fill_price + commission
            else:
                self._portfolio.cash += abs_qty * fill_price - commission

            # Update position
            new_qty = current_qty + delta_qty
            if abs(new_qty) < 1:
                self._portfolio.positions.pop(target.asset_id, None)
            else:
                self._portfolio.positions[target.asset_id] = PortfolioPosition(
                    asset_id=target.asset_id,
                    quantity=new_qty,
                    market_value=abs(new_qty) * price,
                    gics_sector=asset_sectors.get(target.asset_id, "Unknown"),
                    country=asset_countries.get(target.asset_id, "US"),
                    adtv_30d=market_adtv.get(target.asset_id, 1_000_000),
                    current_price=price,
                )

            order = SimulatedOrder(
                order_id=str(uuid.uuid4()),
                asset_id=target.asset_id,
                side=side,
                quantity=abs_qty,
                price=price,
                fill_price=fill_price,
                slippage_bps=slippage_bps,
                commission=commission,
                timestamp_utc=now,
                signal_timestamp=signal_timestamp,
                signal_to_trade_latency_s=latency,
                risk_check_passed=True,
                pre_trade_result=risk_result,
            )
            orders.append(order)
            self._portfolio.trade_history.append(order)

            logger.info(
                f"PAPER TRADE: {side.upper()} {abs_qty} {target.asset_id} "
                f"@ {fill_price:.2f} (slippage {slippage_bps:.1f}bps, "
                f"latency {latency:.0f}s)"
            )

        # Update NAV
        self._portfolio.update_nav(market_prices)
        daily_ret = self._portfolio.get_daily_return()
        self._portfolio.pnl_daily.append(daily_ret)

        return orders

    def _simulate_execution(
        self,
        price: float,
        quantity: int,
        adtv: float,
        side: str,
    ) -> tuple[float, float]:
        """
        Simulate execution with spread + market impact.
        
        Market impact: Almgren-Chriss square-root model.
        Impact = σ × coeff × √(quantity / ADTV)
        """
        # Spread
        spread_impact = price * self.DEFAULT_SPREAD_BPS / 10000

        # Market impact (square-root model)
        participation = quantity / adtv if adtv > 0 else 0.1
        daily_vol = price * 0.02  # Assume 2% daily vol
        market_impact = daily_vol * self.MARKET_IMPACT_COEFF * np.sqrt(participation)

        total_slippage = spread_impact + market_impact
        slippage_bps = total_slippage / price * 10000

        if side == "buy":
            fill_price = price + total_slippage
        else:
            fill_price = price - total_slippage

        return fill_price, slippage_bps

    def get_performance_summary(self) -> dict[str, Any]:
        """Get portfolio performance summary."""
        nav_arr = np.array(self._portfolio.nav_history)
        if len(nav_arr) < 2:
            return {"status": "insufficient_data"}

        returns = np.diff(nav_arr) / nav_arr[:-1]
        sharpe = float(np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0

        cum = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cum)
        dd = (peak - cum) / peak
        max_dd = float(np.max(dd)) * 100

        return {
            "current_nav": float(self._portfolio.nav),
            "starting_nav": float(self._portfolio.start_nav),
            "total_return_pct": (self._portfolio.nav / self._portfolio.start_nav - 1) * 100,
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": max_dd,
            "total_trades": len(self._portfolio.trade_history),
            "blocked_trades": sum(1 for o in self._portfolio.trade_history if not o.risk_check_passed),
            "avg_slippage_bps": float(np.mean([o.slippage_bps for o in self._portfolio.trade_history if o.risk_check_passed])) if self._portfolio.trade_history else 0,
        }
