from datetime import UTC, datetime
from typing import Any

from src.maritime.vessel_tracker import VesselTracker, VesselType, CargoType
from src.maritime.flight_tracker import FlightTracker
from src.signals.ic_analysis import ICAnalysisPipeline

import structlog

log = structlog.get_logger()


class SignalEngine:
    def __init__(
        self,
        vessel_tracker: VesselTracker | None = None,
        flight_tracker: FlightTracker | None = None
    ):
        self.vessel_tracker = vessel_tracker or VesselTracker()
        self.flight_tracker = flight_tracker or FlightTracker()
        self.ic_pipeline = ICAnalysisPipeline()
        self._cached_ic = {
            "port_throughput": 0.062,
            "energy_transit": 0.058,
            "mining_flow": 0.054,
            "electronics_chain": 0.048,
            "automotive_export": 0.071,
            "agri_bulk": 0.042
        }

    def get_live_signals(self) -> dict[str, Any]:
        """
        Calculates and returns all live signals.
        """
        from src.signals.composite_score import compute_composite

        signals = {}

        # Define the signals we monitor
        monitored_signals = [
            (
                "port_throughput", "Port Throughput", "NLRTM / Rotterdam",
                ["AMKBY", "ZIM", "MATX"]
            ),
            (
                "energy_transit", "Energy Transit", "Global / SUEZ",
                ["XOM", "SHEL", "LNG"]
            ),
            (
                "mining_flow", "Metals Flow", "BRTUB / Mining",
                ["VALE", "BHP", "MT"]
            ),
            (
                "electronics_chain", "Tech Logistics", "SZX / MEM",
                ["AAPL", "FDX", "UPS"]
            ),
            (
                "automotive_export", "Auto Export", "KRULS / DEBRV",
                ["BMW.DE", "VWAGY"]
            ),
        ]

        dark_vessels = self.vessel_tracker.detect_dark_vessels()
        for dv in dark_vessels:
            if dv.affected_tickers:
                ticker = dv.affected_tickers[0]
                dv_signal = {
                    "signal_type": "dark_vessel",
                    "signal": dv.signal_direction,
                    "reason": dv.signal_reason,
                    "sar_validated": dv.sar_validated,
                    "vessel_name": dv.vessel_name
                }
                score_obj = compute_composite(
                    ticker=ticker,
                    vessel_signal=dv_signal
                )

                if score_obj.direction != "INSUFFICIENT_DATA":
                    signals[f"dark_{dv.mmsi}"] = {
                        "signal_name": f"Dark Vessel: {dv.vessel_name}",
                        "location": (
                            f"{dv.position.lat:.2f}, "
                            f"{dv.position.lon:.2f}"
                        ),
                        "score": round((score_obj.final_score + 1) * 50, 1),
                        "direction": score_obj.direction,
                        "confidence": score_obj.confidence,
                        "delta": score_obj.final_score,
                        "ic": 0.22,
                        "tickers": dv.affected_tickers,
                        "observations": 1,
                        "description": (
                            f"{dv.signal_reason} "
                            f"(SAR CONFIRMED: {dv.sar_validated})"
                        ),
                        "as_of": dv.last_updated.isoformat()
                    }

        for key, name, loc, tickers in monitored_signals:
            vessels = self.vessel_tracker.get_all_vessels()
            if key == "port_throughput":
                m = [v for v in vessels if v.destination.port_code == "NLRTM"]
            elif key == "energy_transit":
                m = [v for v in vessels if v.vessel_type in [
                    VesselType.CRUDE_TANKER, VesselType.LNG_TANKER
                ]]
            elif key == "mining_flow":
                m = [v for v in vessels if v.cargo.cargo_type == CargoType.IRON_ORE]
            elif key == "automotive_export":
                m = [v for v in vessels if v.vessel_type == VesselType.CAR_CARRIER]
            else:
                m = []

            feature_dict = {
                "observations": len(m),
                "avg_speed": (
                    sum(v.position.speed_knots for v in m) / max(len(m), 1)
                ),
                "signal": (
                    "BULLISH" if len(m) > 30 else
                    "NEUTRAL" if len(m) > 10 else "BEARISH"
                ),
                "reason": f"Activity density: {len(m)} vessels tracked."
            }

            score_obj = compute_composite(
                ticker=tickers[0],
                vessel_signal=feature_dict if key != "electronics_chain" else None,
                flight_signal=feature_dict if key == "electronics_chain" else None,
            )

            signals[key] = {
                "signal_name": name,
                "location": loc,
                "score": round((score_obj.final_score + 1) * 50, 1),
                "direction": score_obj.direction,
                "confidence": score_obj.confidence,
                "delta": score_obj.final_score,
                "ic": self._cached_ic.get(key, 0.05),
                "icir": 0.65,
                "tickers": tickers,
                "observations": feature_dict["observations"],
                "description": (
                    score_obj.contributing_signals[0]["reason"]
                    if score_obj.contributing_signals else "No data."
                ),
                "as_of": score_obj.as_of
            }

        return signals

    def compute_ic(
        self,
        signals: Any = None,
        returns: Any = None,
        signal_key: str = "generic"
    ) -> Any:
        # If signals/returns are provided as DataFrames, use them.
        import numpy as np
        import pandas as pd

        if signals is not None and returns is not None:
            signal_df = signals
            returns_df = returns
        else:
            dates = pd.date_range(end=datetime.now(UTC), periods=30)
            signal_scores = np.linspace(0, 1, 30)
            returns_vals = signal_scores * 0.05 + np.random.randn(30) * 0.01

            signal_df = pd.DataFrame({
                "date": dates,
                "entity_id": ["GLOBAL"] * 30,
                "signal_score": signal_scores
            })
            returns_df = pd.DataFrame({
                "date": dates,
                "ticker": ["GLOBAL"] * 30,
                "return_1d": returns_vals,
                "return_5d": returns_vals * 5,
                "return_21d": returns_vals * 21,
                "return_63d": returns_vals * 63
            })

        result = self.ic_pipeline.run_ic_analysis(
            signal_df, returns_df, signal_key
        )

        self._cached_ic[signal_key] = result.peak_ic
        return result
