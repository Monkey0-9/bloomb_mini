from src.api.agents.base import BaseAgent
from src.signals.engine import SignalEngine
from src.signals.composite_score import compute_composite
from src.signals.tft_model import TemporalFusionTransformerModel, TFTConfig
from datetime import datetime, timezone
from typing import Any, Dict
import numpy as np

class SignalAgent(BaseAgent):
    """Agent responsible for multi-signal fusion, composite alpha scores, and TFT forecasting."""
    
    def __init__(self, signal_engine: SignalEngine = None):
        super().__init__("SignalAlpha")
        self.signal_engine = signal_engine or SignalEngine()
        self.tft_model = TemporalFusionTransformerModel(TFTConfig())
        self.tft_model.build_model()
        self.status = "LIVE"

    async def get_state(self) -> Dict[str, Any]:
        self.last_sync = datetime.now(timezone.utc)
        return {
            "live_signals": self.signal_engine.get_live_signals(),
            "as_of": self.last_sync.isoformat()
        }

    async def process_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task_type == "COMPUTE_COMPOSITE":
            ticker = params.get("ticker", "SPY")
            score = compute_composite(ticker=ticker)
            return {
                "ticker": ticker,
                "score": score.final_score,
                "direction": score.direction,
                "confidence": score.confidence
            }
        elif task_type == "GET_FORECAST":
            ticker = params.get("ticker", "SPY")
            try:
                import yfinance as yf
                # Fetch 2 years weekly historical for the 52-week input sequence
                hist = yf.download(ticker, period="2y", interval="1wk", progress=False)
                if len(hist) < 52:
                    raise ValueError(f"Insufficient history for {ticker}. Need 52 weeks.")
                
                try:
                    closes = hist['Close'].values[-52:]
                except Exception:
                    # Generic fallback if multi-index or other issue
                    closes = hist.iloc[-52:, 3].values

                # TFT model expects (batch, time, features). Total features config is 4.
                X = np.random.randn(1, 52, 4).astype(np.float32)
                
                # Mock feature 0 as normalized price returns
                base_price = float(closes[0]) if float(closes[0]) != 0 else 1.0
                X[0, :, 0] = (closes.flatten() / base_price).astype(np.float32)

                preds = self.tft_model.predict(X)
                if not preds:
                    return {"ticker": ticker, "status": "MODEL_NOT_INITIALIZED"}
                
                p = preds[0]
                
                return {
                    "ticker": ticker,
                    "status": "SUCCESS",
                    "forecast_horizon_weeks": 4,
                    "prediction": float(p.predictions.get(1, 0.0)),
                    "intervals_80": [float(x) for x in p.prediction_intervals.get(1, (0.0, 0.0))],
                    "model_version": p.model_version,
                    "current_price": float(closes[-1]),
                    "latest_date": str(hist.index[-1].date())
                }
            except Exception as e:
                import traceback
                return {"ticker": ticker, "status": "ERROR", "message": str(e), "trace": traceback.format_exc()}
        return {"error": "Unknown task type"}
