# SatTrade Multi-Agent Intelligence (MiroFish-Inspired)

The SatTrade intelligence engine uses a swarm-based multi-agent architecture to simulate global maritime trade and predict disruptions.

## Agent Personas
- **Cautious**: High sensitivity to seismic activity; prioritizes safety and route divergence.
- **Aggressive**: High sensitivity to geopolitical news/insurance spikes; prioritizes schedules but is vulnerable to conflict-based delays.
- **Standard**: Balanced response to all intelligence seeds.
- **Weather-Sensitive**: High sensitivity to marine weather and visibility (Open-Meteo); prioritizes environmental resilience over speed.
- **Economic-Sensitive**: High sensitivity to macroeconomic indicators (FRED); prioritizes route optimization based on inflation and yield signals.

## Intelligence Seeds
Agents dynamically update their internal "health" and "memory" in response to:
- **Thermal Anomalies**: Industrial facility activity (NASA FIRMS).
- **Seismic Events**: Real-time earthquakes (USGS).
- **OSINT/News**: Geopolitical and maritime defense alerts (GDELT).
- **Environment**: Marine weather, visibility, and sea state (Open-Meteo).
- **Macro**: Inflation, yield curves, and VIX (FRED).

## Global Trade Flow Index (GTFI)
The GTFI is an aggregate measure of the health of all active maritime agents. A score of 1.0 represents optimal global flow, while lower scores indicate systemic disruption.
