"""
Earnings Calendar — yfinance-powered upcoming earnings tracker.
Correlates satellite signal strength with upcoming earnings events
to produce the satellite-vs-earnings alpha overlay.
"""

import pandas as pd
import yfinance as yf

# Core tickers linked to maritime/satellite signals
TRACKED_TICKERS = [
    # Shipping & Maritime
    "ZIM", "MATX", "SBLK", "GOGL", "EGLE", "CTRM", "DAC", "NMM",
    # Steel & Metals (linked to blast furnace thermal signals)
    "MT", "STLD", "NUE", "CLF", "X", "SCCO", "FCX",
    # Energy / LNG / Oil (linked to refinery thermal signals)
    "LNG", "CQP", "SRE", "SHELL", "BP", "XOM", "CVX", "TTE",
    # Port & Logistics (linked to vessel density signals)
    "FDX", "UPS", "DPSGY", "XPO", "CHRW",
    # Commodities ETFs
    "DJP", "GSG", "DBC",
    # Agricultural (Grain bulk carriers)
    "ADM", "BG", "INGR",
]


def get_upcoming_earnings(tickers: list[str] | None = None) -> list[dict]:
    """
    Fetch upcoming earnings dates for all tracked tickers.
    Returns a list sorted by earnings date ascending.
    """
    tickers = tickers or TRACKED_TICKERS
    results = []

    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            cal = t.calendar
            if not cal:
                continue

            # calendar can be a dict or DataFrame depending on yfinance version
            if isinstance(cal, dict):
                dates = cal.get("Earnings Date", [])
                if dates:
                    results.append({
                        "ticker": ticker,
                        "earnings_date": dates[0].isoformat() if hasattr(dates[0], "isoformat") else str(dates[0]),
                        "eps_estimate": cal.get("Earnings Average"),
                        "eps_low": cal.get("Earnings Low"),
                        "eps_high": cal.get("Earnings High"),
                        "revenue_estimate": cal.get("Revenue Average"),
                    })
            elif isinstance(cal, pd.DataFrame):
                if "Earnings Date" in cal.index:
                    date_val = cal.loc["Earnings Date"].values[0]
                    results.append({
                        "ticker": ticker,
                        "earnings_date": str(date_val),
                        "eps_estimate": None,
                        "eps_low": None,
                        "eps_high": None,
                        "revenue_estimate": None,
                    })
        except Exception:
            continue

    # Sort by earnings date ascending (soonest first)
    results.sort(key=lambda x: x.get("earnings_date", "9999-12-31"))
    return results


def get_earnings_with_satellite_signal(satellite_signals: dict | None = None) -> list[dict]:
    """
    Join upcoming earnings with satellite/vessel signal data
    to produce the full alpha overlay.
    """
    upcoming = get_upcoming_earnings()

    # If no signals provided, try to fetch live ones (demo fallback)
    if satellite_signals is None:
        try:
            from src.maritime.flight_tracker import FlightTracker
            from src.maritime.vessel_tracker import VesselTracker
            from src.signals.engine import SignalEngine
            se = SignalEngine(VesselTracker(), FlightTracker())
            live_signals = se.get_live_signals()
            # Mapping live signals to ticker-indexed dictionary
            satellite_signals = {}
            for sig in live_signals.values():
                for t in sig["tickers"]:
                    satellite_signals[t] = {
                        "signal": sig["direction"],
                        "reason": sig["description"],
                        "score": sig["score"]
                    }
        except ImportError:
            satellite_signals = {}

    enriched = []
    for item in upcoming:
        ticker = item["ticker"]
        sat = satellite_signals.get(ticker, {})
        item["satellite_signal"] = sat.get("signal", "NEUTRAL")
        item["satellite_reason"] = sat.get("reason", "Scanning baseline...")
        item["satellite_score"] = sat.get("score", 50)
        item["alpha_opportunity"] = sat.get("signal") in ("BULLISH", "BEARISH")

        # Priority 2 Gap: Earnings Surprise Probability
        # If signal is BULLISH and score > 70, high probability of upside surprise
        score = item["satellite_score"]
        if item["satellite_signal"] == "BULLISH":
            item["surprise_probability"] = 0.5 + (score / 200) # 0.5 to 1.0
        elif item["satellite_signal"] == "BEARISH":
            item["surprise_probability"] = -(0.5 + (score / 200)) # -0.5 to -1.0
        else:
            item["surprise_probability"] = 0.0

        enriched.append(item)

    return enriched
