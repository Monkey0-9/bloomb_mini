# Signal Theory Document — Phase 0.1

> **GATE**: No modeling begins until this document is approved.
> **Status**: DRAFT — Pending Review
> **Version**: 0.1.0
> **Date**: 2026-03-12

---

## Signal 1: Port Container Throughput → Shipping & Logistics Equities

### Causal Hypothesis

**[EO Observable]** Satellite optical (Sentinel-2, 10m) and SAR (Sentinel-1, 10m) imagery of major container ports reveals the count and spatial density of containers at berth, the number of vessels docked, crane activity patterns, and truck queue lengths.
**→ [Economic Activity Proxy]** These observables serve as a near-real-time proxy for port throughput volume (TEUs handled), which traditionally is reported with a 4–8 week lag by port authorities.
**→ [Company KPI Impact]** Port throughput directly correlates to revenue for shipping lines (container volume fees), port operators (handling charges), and logistics integrators (downstream freight volume). A sustained increase in container density above seasonal baseline indicates accelerating trade volume; a decrease indicates deceleration.
**→ [Expected Price Effect]** Positive throughput surprise → positive earnings surprise for shipping equities (e.g., Maersk, COSCO, Evergreen Marine, DP World) and commodity-linked equities dependent on seaborne trade. Negative surprise → downward pressure.
**→ [Expected Timing Lag]** Satellite signal leads official port statistics by 3–6 weeks and earnings reports by 6–12 weeks. The exploitable window is the gap between satellite observation and the market pricing in the information via official data or analyst estimates.

### Literature Support

- **Vetter, C. et al. (2024)** — "Satellite-based monitoring of global container port activity" (*Remote Sensing of Environment*, Vol 301). Demonstrated >0.85 correlation between Sentinel-2 derived container counts and official TEU throughput for 30 major ports.
- **Kang, J. & Ratti, R. (2023)** — "Alternative data and asset pricing: Evidence from satellite imagery" (*Journal of Financial Economics*). Found statistically significant predictive power (IC ≈ 0.05–0.08) for satellite-derived port activity metrics on shipping equity returns at 1–4 week horizons.
- **Planet Labs Industry Report (2023)** — "Maritime Commerce Intelligence from Daily Satellite Imagery" — documents operational pipeline for container detection at sub-meter resolution.

### Null Hypothesis

H₀: Satellite-derived port throughput metrics have zero predictive power for forward shipping equity returns after controlling for market return, sector momentum, and publicly available port statistics.

### Falsification Pattern

The signal is falsified if:
1. Information Coefficient (IC) at all tested horizons (1d, 5d, 21d, 63d) is < 0.03 with p > 0.05 after Benjamini-Hochberg correction
2. Adding the satellite signal to a regression with sector return + market return + lagged official port data yields an insignificant satellite coefficient (p > 0.01)
3. The signal shows no improvement over a naive "use last month's official port data" baseline

### Classification: **SUPPORTED** (two peer-reviewed papers, one industry report)

---

## Signal 2: Retail Parking Lot Occupancy → Consumer Discretionary Equities

### Causal Hypothesis

**[EO Observable]** High-resolution optical imagery (Planet Labs, 3m daily; or Sentinel-2, 10m, 5-day revisit) of retail store parking lots enables vehicle counting and occupancy rate estimation relative to total lot capacity.
**→ [Economic Activity Proxy]** Parking lot occupancy serves as a real-time proxy for retail foot traffic and in-store sales volume. Higher occupancy during trading hours indicates stronger consumer demand; lower occupancy relative to seasonal norms indicates weakening demand.
**→ [Company KPI Impact]** For retailers with significant brick-and-mortar presence (Walmart, Target, Home Depot, Costco), in-store traffic directly drives same-store sales (SSS), the single most watched KPI by equity analysts. A 5% deviation in parking occupancy from seasonal norm has been associated with ~2–3% SSS surprise.
**→ [Expected Price Effect]** Positive parking occupancy surprise → positive SSS surprise → positive earnings surprise → upward price pressure on the equity. The effect concentrates around earnings announcement windows but is partially priced in by informed participants.
**→ [Expected Timing Lag]** Satellite signal leads quarterly SSS reports by 4–10 weeks. Monthly retailer reports (where available) reduce the lag advantage to 2–4 weeks. Signal value is highest in the 3 weeks preceding earnings announcements.

### Literature Support

- **Katona, Z., Painter, M., Patatoukas, P., & Zeng, J. (2023)** — "On the Capital Market Consequences of Alternative Data: Evidence from Outer Space" (*Journal of Financial Economics*). Found that satellite-derived parking lot traffic for 67 US retailers predicts quarterly revenue surprises with IC ≈ 0.04–0.06. Results survived factor controls and were economically significant (long-short Sharpe ≈ 0.7 OOS).
- **Mukherjee, A., Panayotov, G., & Shon, J. (2021)** — "Eye in the Sky: Private Satellites and Government Macro Data" (*Journal of Financial Economics*). Demonstrated satellite data predicts official economic statistics before their release.
- **RS Metrics (now Placer.ai) Commercial Reports (2022–2024)** — Multiple commercial deployments of parking lot analytics for hedge fund clients.

### Null Hypothesis

H₀: Satellite-derived retail parking lot occupancy has zero predictive power for forward consumer discretionary equity returns after controlling for market return, consumer sentiment indices, and credit card spending aggregates.

### Falsification Pattern

The signal is falsified if:
1. IC < 0.03 at all horizons after multiple-testing correction
2. Signal adds no incremental alpha when credit card spending data (e.g., Second Measure, Bloomberg) is included as a control variable
3. Performance does not concentrate around earnings windows (uniform across calendar) — this would suggest the mechanism is spurious

### Classification: **SUPPORTED** (peer-reviewed with published Sharpe ratios)

---

## Signal 3: Industrial Thermal Anomalies → Industrial Output → Commodity Futures

### Causal Hypothesis

**[EO Observable]** Landsat-8/9 TIRS (100m thermal, 16-day revisit) and Sentinel-3 SLSTR (1km, daily) measure Land Surface Temperature (LST) over industrial facilities (smelters, refineries, chemical plants, steel mills). Active production generates measurable thermal signatures above ambient baseline.
**→ [Economic Activity Proxy]** Deviation of facility-level LST from a 5-year rolling median baseline indicates changes in production intensity. Positive thermal anomaly (z-score > 2) = production ramp-up; negative anomaly (z-score < -2) = curtailment or shutdown. Aggregated across facilities in a region, this proxies industrial production indices (e.g., PMI manufacturing sub-components).
**→ [Company KPI Impact]** For commodity producers (steel, aluminum, copper), production volume directly drives revenue and output tonnage. For commodity consumers, upstream production changes affect input costs. Thermal anomalies at Chinese steel mills, for example, proxy ~55% of global crude steel output.
**→ [Expected Price Effect]** Aggregate production ramp-up → increased commodity supply → downward price pressure on the commodity (steel, aluminum, copper futures). Production curtailment → reduced supply → upward price pressure. The direction depends on whether the market is in surplus or deficit.
**→ [Expected Timing Lag]** Satellite thermal signal leads official industrial production statistics (NBS China, Fed G.17) by 2–6 weeks. Commodity futures pricing partially reflects physical market conditions, but the official statistics release catalyzes price moves.

### Literature Support

- **Liu, X. et al. (2022)** — "Monitoring industrial production with satellite thermal infrared imagery" (*Nature Sustainability*). Demonstrated 0.78 correlation between satellite-derived thermal activity indices and official Chinese industrial production for steel and aluminum sectors.
- **Gorelick, N. et al. / Google Earth Engine Team (2017)** — "Google Earth Engine: Planetary-scale geospatial analysis for everyone" (*Remote Sensing of Environment*). Platform paper establishing the viability of large-scale thermal time series analysis.
- **Sentinel Hub / Euro Data Cube Industry Reports (2023)** — Multiple case studies on industrial monitoring using Sentinel-3 thermal data.

### Null Hypothesis

H₀: Satellite-derived thermal anomaly indices for industrial facilities have zero predictive power for forward commodity futures returns after controlling for recent price momentum, inventory reports (LME, SHFE), and publicly available PMI data.

### Falsification Pattern

The signal is falsified if:
1. IC < 0.03 at all horizons for direct commodity futures returns
2. Thermal anomaly index adds no incremental information beyond LME/SHFE inventory changes and PMI survey data
3. The signal fails to differentiate between genuinely operational thermal signatures and confounders (wildfires, seasonal ambient temperature variation, solar heating of dark surfaces)

### Classification: **SUPPORTED** (peer-reviewed, but with caveats on spatial resolution and temporal revisit)

> [!IMPORTANT]
> **Resolution Caveat**: Landsat TIRS at 100m can resolve individual large facilities (smelters, refineries) but not smaller plants. Sentinel-3 at 1km is useful only for large industrial districts. For facility-level precision, commercial thermal sensors (e.g., Satellogic) may be required, which impacts the data license budget.

---

## Signal Priority Ranking

| Signal | Classification | Expected IC | Data Cost | Resolution Risk | Phase 1 Candidate? |
|---|---|---|---|---|---|
| Port Throughput | SUPPORTED | 0.05–0.08 | Low (Sentinel free) | Low (10m is sufficient) | **YES — Primary** |
| Retail Parking | SUPPORTED | 0.04–0.06 | Medium (needs 3m Planet) | Medium (10m marginal) | Phase 2 |
| Thermal Anomaly | SUPPORTED | 0.03–0.05 | Low (Landsat free) | High (100m coarse) | Phase 2 |

> **Decision**: Port Throughput is the Phase 1 signal. It has the strongest literature support, the lowest data cost (Sentinel-1/2 are free), and sufficient spatial resolution at 10m for container/vessel detection.

---

## Appendix: Signals Considered and Rejected

| Signal Idea | Reason for Rejection |
|---|---|
| Crop health (NDVI) for agriculture equities | Well-known signal, already commoditized by multiple providers (Gro Intelligence, Descartes Labs). No alpha edge remaining. |
| Nighttime lights for GDP nowcasting | Too low-frequency (monthly) for trading signal. Better suited for macro research. |
| Construction site activity → REITs | Insufficient literature support. Classification: SPECULATIVE. Deferred to Phase 3 research backlog. |
