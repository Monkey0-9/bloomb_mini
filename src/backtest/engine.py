from typing import Any, Dict, List
import pandas as pd
import structlog

log = structlog.get_logger()

class BacktestEngine:
    """
    Simulates trading strategies against historical data.
    """
    def __init__(self) -> None:
        self.log = log.bind(component="backtest_engine")

    def run_simulation(self, ticker: str, signals: List[dict], prices: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs a simulation of a strategy based on provided signals.
        """
        initial_capital = 100_000
        capital = initial_capital
        position = 0
        trades = []
        
        for i, row in prices.iterrows():
            # Match signal to date if possible, here simplified
            day_signal = [s for s in signals if s["date"] == i.strftime("%Y-%m-%d")]
            if day_signal:
                score = day_signal[0].get("score", 0)
                if score > 0.8 and position == 0:
                    # Buy
                    position = capital / row["Close"]
                    capital = 0
                    trades.append({"date": i, "side": "BUY", "price": row["Close"]})
                elif score < 0.2 and position > 0:
                    # Sell
                    capital = position * row["Close"]
                    position = 0
                    trades.append({"date": i, "side": "SELL", "price": row["Close"]})
                    
        final_value = capital + (position * prices.iloc[-1]["Close"] if position > 0 else 0)
        return {
            "pnl": final_value - initial_capital,
            "return_pct": ((final_value / initial_capital) - 1) * 100,
            "trade_count": len(trades)
        }
