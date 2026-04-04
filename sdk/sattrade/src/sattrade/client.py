import requests
import pandas as pd
import json
import websocket
import threading
from typing import List, Dict, Optional, Union, Any

class Terminal:
    """The SatTrade Terminal SDK for Quantitative Analysts."""
    
    def __init__(self, api_base: str = "http://localhost:9009", token: Optional[str] = None):
        self.api_base = api_base.rstrip('/')
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            
    def get_signals(self, ticker: Optional[str] = None) -> pd.DataFrame:
        """Fetch live industrial intelligence signals."""
        url = f"{self.api_base}/api/alpha/signals"
        if ticker:
            url += f"?ticker={ticker}"
        
        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame(data.get("signals", []))
    
    def get_composite(self, ticker: str) -> Dict[str, Any]:
        """Fetch the multi-modal composite score for a symbol."""
        url = f"{self.api_base}/api/alpha/composite?ticker={ticker}"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()
    
    def get_vessels(self, bbox: Optional[List[float]] = None) -> pd.DataFrame:
        """Fetch live maritime tracking data."""
        url = f"{self.api_base}/api/maritime/vessels"
        resp = self.session.get(url)
        resp.raise_for_status()
        return pd.DataFrame(resp.json())
    
    def get_forecast(self, ticker: str) -> pd.DataFrame:
        """Fetch Temporal Fusion Transformer (TFT) quantile forecasts."""
        url = f"{self.api_base}/api/alpha/forecast/{ticker}"
        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame(data.get("bands", []))

    def stream(self, topics: List[str], callback):
        """Subscribe to real-time telemetry feeds via WebSocket."""
        ws_url = f"{self.api_base.replace('http', 'ws')}/ws"
        if self.token:
            ws_url += f"?token={self.token}"

        def on_message(ws, message):
            data = json.loads(message)
            callback(data)

        def on_open(ws):
            ws.send(json.dumps({
                "action": "subscribe",
                "topics": topics
            }))

        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_open=on_open
        )
        
        thread = threading.Thread(target=ws.run_forever)
        thread.daemon = True
        thread.start()
        return ws
