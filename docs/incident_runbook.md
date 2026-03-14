# Incident Response Runbook — Phase 8.4

> Living document. Versioned in Git alongside codebase.
> Last updated: 2026-03-12

---

## Severity Definitions

| Severity | Description | Response Time | Escalation |
|---|---|---|---|
| **P0** | Kill switch triggered / total pipeline failure / data breach | Immediate | Notify all stakeholders, drop everything |
| **P1** | Signal quality degradation / risk limit breach / SLA violation | 15 minutes | Notify on-call engineer |
| **P2** | Partial data coverage loss / model performance decline | 1 hour | Notify during business hours |
| **P3** | Non-critical warnings / minor metric deviations | Next business day | Track in issue backlog |

---

## Failure Mode: Kill Switch Triggered

| Field | Detail |
|---|---|
| **Detection** | Automated: drawdown > 8%, 3 consecutive pre-trade failures, data outage > 4h, or manual override |
| **Severity** | P0 |
| **Automated Response** | Immediate halt of all signal generation and order submission. All positions frozen. |
| **Human Escalation** | Page on-call engineer + risk officer via PagerDuty |
| **Investigation Steps** | 1. Check audit log for root cause (QLDB) |
| | 2. Review last 24h of signal/risk check events |
| | 3. Verify data pipeline status |
| | 4. Check for market-wide events (flash crash, circuit breaker) |
| **Recovery** | 1. Identify and remediate root cause |
| | 2. Risk officer authorises kill switch reset |
| | 3. Resume with reduced position sizes (50%) for first 5 trading days |
| **RCA Template** | Use `docs/templates/rca_template.md` |
| **Post-Incident Review** | Within 48 hours of resolution |

## Failure Mode: Data Pipeline Outage

| Field | Detail |
|---|---|
| **Detection** | CloudWatch alarm on ECS task failure; no new tiles ingested for > 2h |
| **Severity** | P1 (P0 if during market hours and > 4h) |
| **Automated Response** | Switch to stale-signal mode (reduce position sizes 50%) |
| **Human Escalation** | Notify on-call engineer |
| **Investigation Steps** | 1. Check Copernicus/Planet API status pages |
| | 2. Review ECS task logs in CloudWatch |
| | 3. Check network connectivity (NAT Gateway, security groups) |
| | 4. Verify API credentials haven't expired |
| **Recovery** | 1. Fix API/network issue 2. Re-run ingestor for missed time window 3. Verify tile counts match expected |

## Failure Mode: Model IC Degradation

| Field | Detail |
|---|---|
| **Detection** | IC below historical 10th percentile for 10 consecutive trading days |
| **Severity** | P2 |
| **Automated Response** | Alert via Grafana/SNS. No position size change (yet). |
| **Human Escalation** | Notify research analyst |
| **Investigation Steps** | 1. Check for feature drift (monthly PSI report) |
| | 2. Examine market regime change (VIX, sector rotation) |
| | 3. Review data coverage — did coverage drop? |
| | 4. Check for annotation quality decline |
| **Recovery** | 1. If PSI > 0.2: trigger model retrain 2. If regime change: engage regime gate 3. If data coverage: escalate to pipeline team |

## Failure Mode: Annotation Quality Decline

| Field | Detail |
|---|---|
| **Detection** | Weekly annotation report shows mean IoU < 0.70 |
| **Severity** | P2 |
| **Automated Response** | Pause auto-annotation pipeline; queue tiles for manual review |
| **Human Escalation** | Notify annotation team lead |
| **Investigation Steps** | 1. Identify low-IoU annotators (per-annotator Fleiss' kappa) |
| | 2. Check for class taxonomy ambiguity |
| | 3. Review recent tile characteristics (new geography, season) |
| **Recovery** | 1. Retrain problematic annotators 2. Clarify taxonomy guidelines 3. Re-annotate affected tiles 4. Verify IoU recovery before resuming |

## Failure Mode: SLA Breach (P95 Latency > 6h)

| Field | Detail |
|---|---|
| **Detection** | Prometheus histogram shows p95 > 21,600s (6h) |
| **Severity** | P1 |
| **Automated Response** | Alert; track SLA credit |
| **Human Escalation** | Notify on-call engineer |
| **Investigation Steps** | 1. Identify bottleneck stage (ingest, preprocess, feature, signal) |
| | 2. Check compute scaling (AWS Batch queue depth, ECS task count) |
| | 3. Review data volume — surge in new tiles? |
| | 4. Check for slow API responses from upstream |
| **Recovery** | 1. Scale compute as needed 2. Optimise bottleneck stage 3. If persistent: add dedicated infrastructure |
