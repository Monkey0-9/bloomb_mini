# SatTrade Python SDK

The institutional-grade quantitative interface for Satellite, Maritime, and Aviation intelligence.

## Installation
```bash
pip install ./sdk/sattrade
```

## Quickstart

```python
from sattrade import Terminal

# Initialize client
tl = Terminal(api_base="http://localhost:9009")

# Fetch bullish signals
signals = tl.get_signals(ticker="ZIM")
print(signals.head())

# Fetch TFT forecast quantile bands
df = tl.get_forecast("FDX")
print(df)

# Real-time telemetry stream
def on_telemetry(msg):
    print(f"TELEMETRY: {msg}")

tl.stream(topics=["vessel", "signal"], callback=on_telemetry)
```
