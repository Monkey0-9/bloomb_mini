# Operational Response Protocol: High Signal Dependency

## Alert Trigger
**Threshold**: Single signal type accounts for > 60% of total portfolio P&L (computed via `SignalAttributor`).

## Mandatory Response Actions
When the 60% dependency threshold is breached, the following actions MUST be taken within 4 hours:

1.  **Risk Escalation**: Notify the Chief Risk Officer (CRO) and Investment Committee (IC).
2.  **Position Reduction**: Reduce the gross exposure of the dominant signal by 50% immediately to prevent idiosyncratic signal failure.
3.  **Dependency Analysis**: Research analyst must verify if the dependency is due to a macro regime shift or a data quality artifact in the dominant sensor (e.g., seasonal cloud-free window for Optical).
4.  **Strategy Suspension**: If the dependency exceeds 80% for 3 consecutive trading days, the entire signal generation for that asset class must be suspended until a secondary independent signal (e.g., SAR vs Optical) validates the trend.

## Documentation
Every high-dependency alert and the subsequent action taken must be recorded in the `compliance_audit_log` with an `operator_id` and a `justification_hash`.
