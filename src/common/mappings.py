"""
Facility-to-Ticker Proxy Mapping — Phase 9

Maps specific satellite-monitored facilities (Ports, Tesla Plants, Walmart lots)
to tradeable equity tickers or sector ETFs.
"""

# Facility to Company Database (Bloomberg/FactSet Revere Proxy Tier)
FACILITY_TICKER_MAP = {
    "port_of_long_beach": ["MATX", "DSX", "BDRY"], # Shipping/Dry Bulk proxies
    "port_of_singapore": ["ZIM", "GLNG"],
    "tesla_shanghai_gigafactory": ["TSLA"],
    "retail_parking_lots_global": ["WMT", "TGT", "COST"],
    "industrial_thermal_cluster_ruhr": ["BAS.DE", "SIE.DE"],
}

def get_tickers_for_facility(facility_id: str) -> list[str]:
    """
    Return the list of tickers whose supply chain is proxied by the facility.
    """
    return FACILITY_TICKER_MAP.get(facility_id.lower(), [])

def get_economic_weight(facility_id: str, ticker: str) -> float:
    """
    Calculates the 'relevance score' of a facility to a company's revenue.
    Placeholder for Revere Supply Chain data.
    """
    # Assuming 1.0 for primary plants, 0.2 for general ports
    if "port" in facility_id:
        return 0.15
    return 1.0
