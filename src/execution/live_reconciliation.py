"""
Daily Open Position Reconciliation — Phase 10

Verifies that the internal ledger and broker matching engine agree.
Halts trading if any discrepancy is found.
"""

import logging
from typing import Dict
from src.execution.broker_connect import LiveBrokerGateway

logger = logging.getLogger(__name__)

class ReconciliationEngine:
    """
    Compares Internal Ledger vs Broker API.
    """
    
    def __init__(self, broker_gateway: LiveBrokerGateway):
        self.gateway = broker_gateway

    def reconcile(self, internal_ledger: Dict[str, float]) -> bool:
        """
        Main reconciliation loop.
        """
        logger.info("Starting Daily Open Position Reconciliation...")
        broker_positions = self.gateway.get_positions()
        
        # Check for symbols in internal but not in broker
        for symbol, qty in internal_ledger.items():
            broker_qty = broker_positions.get(symbol, 0.0)
            if abs(qty - broker_qty) > 0.0001:
                logger.error(f"RECONCILIATION FAILURE: {symbol} | Internal: {qty} | Broker: {broker_qty}")
                return False

        # Check for symbols in broker but not in internal
        for symbol, qty in broker_positions.items():
            if symbol not in internal_ledger:
                logger.error(f"RECONCILIATION FAILURE: Unexpected position in broker for {symbol} | Qty: {qty}")
                return False

        logger.info("Reconciliation SUCCESS. Ledgers are in sync.")
        return True
