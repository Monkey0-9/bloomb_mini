# Runbook: Signal Failure SOP (Confident but Wrong)

> **Status**: ACTIVE
> **Owner**: Quant Team / On-Call Ops

## Scenario Definition
The signal model generates a "High Confidence" (90th percentile) trade recommendation, but the market moves sharply in the opposite direction, potentially due to:
1.  **Regime Shift**: Sudden macro event invalidating historical satellite correlation.
2.  **Data Poisoning**: Systematic error in imagery (e.g., thermal lens flare).
3.  **Adversarial Activity**: Fake object decoys (common in geopolitical SAR).

## Detection Criteria
- Signal Confidence > 0.8
- Asset 1-day Return < -3.0% (for Longs) or > +3.0% (for Shorts)
- Zero news catalysts detected in news wire (idiosyncratic model failure)

## Immediate Actions
1.  **Halt Auto-Execution**: Set `live_trading_permitted = False` in `config/constraints.yaml`.
2.  **Verify Lineage**: Call `src/features/lineage.py` to identify which feature hash drove the signal.
3.  **Manual Image Review**: Pull raw `.tif` files from the WORM storage for the facility in question.
4.  **Halt Ticker**: Block the specific ticker in `src/execution/risk_engine.py` blocklist.

## Resolution
- If **Infrastructure Failure**: Fix pipeline and resume.
- If **Model Failure**: Tag as "Outlier" and trigger the `ModelRollbackManager` to revert to KGS.

## Post-Mortem
Every "Confident but Wrong" event must be recorded in the `audit_report.md` with:
- Feature hashes involved.
- Root cause (Geospatial vs Macro).
- Updated IC threshold for the specific regime.
