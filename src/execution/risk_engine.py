# Legacy risk engine redirect to ensure tests pass
from src.risk.engine import RiskEngine

GROSS_EXPOSURE_LIMIT = 1.50

def get_risk_engine() -> RiskEngine:
    return RiskEngine()
