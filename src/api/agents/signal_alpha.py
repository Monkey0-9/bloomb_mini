from datetime import UTC, datetime
from typing import Any

import numpy as np

from src.api.agents.base import BaseAgent
from src.signals.composite_score import get_signal_engine
from src.signals.tft_model import get_tft_server


class SignalAgent(BaseAgent):
    """
    Agent responsible for multi-signal fusion, composite alpha scores, 
    and high-performance TFT forecasting.
    """

    def __init__(self):
        super().__init__("signals")
        self.signal_engine = get_signal_engine()
        self.tft_server = get_tft_server()
        self.status = "LIVE"

    async def get_state(self) -> dict[str, Any]:
        self.last_sync = datetime.now(UTC)
        return {
            "status": self.status,
            "as_of": self.last_sync.isoformat(),
            "global_weights": self.signal_engine._optimizer.get_dynamic_weights()
        }

    async def process_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        if task_type == "COMPUTE_COMPOSITE":
            ticker = params.get("ticker", "SPY")
            signals = params.get("signals", [])
            score = await self.signal_engine.compute_composite(ticker=ticker, signals=signals)
            return {
                "ticker": ticker,
                "score": score.final_score,
                "direction": score.direction,
                "confidence": score.confidence,
                "regime": score.regime,
                "signals": score.contributing_signals
            }

        elif task_type == "GET_FORECAST":
            ticker = params.get("ticker", "SPY")
            history = params.get("history")

            if history is None:
                # Mock high-fidelity history for demonstration if not provided
                history = np.random.randn(52, 10).astype(np.float32)
            else:
                history = np.array(history).astype(np.float32)

            try:
                pred = await self.tft_server.get_forecast(ticker, history)

                # Format for frontend bands expectation
                bands = []
                for i in range(len(pred.predictions)):
                    bands.append({
                        "time": i + 1,
                        "p10": pred.prediction_intervals[0][i],
                        "p50": pred.predictions[i],
                        "p90": pred.prediction_intervals[1][i]
                    })

                return {
                    "ticker": ticker,
                    "status": "SUCCESS",
                    "forecast": pred.predictions,
                    "intervals": pred.prediction_intervals,
                    "bands": bands,
                    "model_version": pred.model_version
                }
            except Exception as e:
                self.log.error("forecast_failed", ticker=ticker, error=str(e))
                return {"error": str(e), "ticker": ticker, "status": "ERROR"}

        return {"error": "Unknown task type"}
