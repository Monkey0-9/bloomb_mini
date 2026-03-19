from src.api.agents.base import BaseAgent
from src.signals.composite_score import get_signal_engine
from src.signals.tft_model import get_tft_server
from datetime import datetime, timezone
from typing import Any, Dict, List
import numpy as np

class SignalAgent(BaseAgent):
    """
    Agent responsible for multi-signal fusion, composite alpha scores, 
    and high-performance TFT forecasting.
    """
    
    def __init__(self):
        super().__init__("SignalAlpha")
        self.signal_engine = get_signal_engine()
        self.tft_server = get_tft_server()
        self.status = "LIVE"

    async def get_state(self) -> Dict[str, Any]:
        self.last_sync = datetime.now(timezone.utc)
        return {
            "status": self.status,
            "as_of": self.last_sync.isoformat(),
            "global_weights": self.signal_engine.optimizer.get_dynamic_weights()
        }

    async def process_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task_type == "COMPUTE_COMPOSITE":
            ticker = params.get("ticker", "SPY")
            signals = params.get("signals", [])
            score = self.signal_engine.compute_composite(ticker=ticker, signals=signals)
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
            
            pred = await self.tft_server.get_forecast(ticker, history)
            
            return {
                "ticker": ticker,
                "status": "SUCCESS",
                "forecast": pred.predictions,
                "intervals": pred.prediction_intervals,
                "model_version": pred.model_version
            }

        return {"error": "Unknown task type"}
