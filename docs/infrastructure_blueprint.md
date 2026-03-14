# Infrastructure Blueprint — Phase 0.3

> **GATE**: Architecture must be reviewed for single points of failure before implementation.
> **Status**: DRAFT — Pending Review
> **Version**: 0.1.0
> **Date**: 2026-03-12

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SATELLITE TRADE PLATFORM                             │
│                                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌────────────┐  │
│  │  DATA LAKE   │    │ FEATURE STORE │    │   MODEL     │    │  SIGNAL    │  │
│  │  (S3)        │───▶│  (Feast)      │───▶│  REGISTRY   │───▶│  BUS       │  │
│  │              │    │              │    │  (MLflow)   │    │  (Kafka)   │  │
│  │  raw/        │    │              │    │              │    │            │  │
│  │  processed/  │    │  point-in-   │    │  STAGING →   │    │  signal.   │  │
│  │  features/   │    │  time joins  │    │  PRODUCTION  │    │  scored    │  │
│  └──────┬───────┘    └──────────────┘    └─────────────┘    └─────┬──────┘  │
│         │                                                         │         │
│         │   ┌──────────────────┐                                  │         │
│         │   │  PREPROCESSING   │                                  ▼         │
│         └──▶│  (ECS/Batch)     │    ┌─────────────┐    ┌──────────────────┐ │
│             │                  │    │  EXECUTION   │◀───│  RISK ENGINE     │ │
│             │  optical_pipe    │    │  SIMULATOR   │    │                  │ │
│             │  sar_pipe        │    │              │    │  pre-trade       │ │
│             │  thermal_pipe    │    │  paper trade │    │  real-time       │ │
│             └──────────────────┘    │  engine      │    │  kill-switch     │ │
│                                     └──────┬──────┘    └──────────────────┘ │
│                                            │                                │
│                                            ▼                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    MONITORING & AUDIT LAYER                         │    │
│  │  Grafana │ CloudWatch │ QLDB (audit log) │ SNS (alerts)            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Service Mapping

### Data Layer

| Component | AWS Service | Purpose | Redundancy |
|---|---|---|---|
| Raw Data Lake | **S3** (`s3://sattrade-raw-{env}`) | Immutable raw satellite tiles | Versioning enabled, cross-AZ |
| Processed Data | **S3** (`s3://sattrade-processed-{env}`) | Preprocessed chips (COG format) | Same |
| Feature Data | **S3** (`s3://sattrade-features-{env}`) | Materialized feature tables | Same |
| Metadata Catalog | **RDS PostgreSQL** (db.t3.medium) | Tile catalog, licensing FKs | Multi-AZ standby |
| Event Bus | **MSK (Managed Kafka)** (kafka.t3.small, 3 brokers) | `raw.tiles`, `processed.tiles`, `signals.scored` | 3-broker cluster, replication factor 3 |

### Compute Layer

| Component | AWS Service | Purpose | Scaling |
|---|---|---|---|
| ETL Ingestors | **ECS Fargate** | Satellite API polling, tile download, validation | Auto-scale 1–5 tasks |
| Preprocessing | **AWS Batch** (Spot instances) | Optical/SAR/thermal pipelines | Batch queue, c5.2xlarge spot |
| Model Training | **SageMaker** (ml.g5.xlarge) | YOLOv8, Siamese U-Net, TFT training | On-demand during training |
| Model Inference | **ECS Fargate** (2 vCPU, 8GB) | Batch inference on new tiles | Auto-scale 1–3 tasks |
| Signal Scoring | **Lambda** | Score → normalise → risk check → emit | Concurrency 100 |
| Backtesting | **EC2** (r5.2xlarge) | Walk-forward, bootstrap validation | On-demand |

### ML/Feature Layer

| Component | Service | Purpose |
|---|---|---|
| Feature Store | **Feast** (self-hosted on ECS) | Point-in-time feature retrieval, as-of joins |
| Model Registry | **MLflow** (self-hosted on ECS + RDS) | Model versioning, A/B staging |
| Experiment Tracking | **MLflow** | Hyperparameters, metrics, artifacts |
| Annotation Tool | **Label Studio** (self-hosted on ECS) | Image annotation with COCO JSON export |

### Execution & Risk Layer

| Component | Service | Purpose |
|---|---|---|
| Execution Simulator | **ECS Fargate** | Paper trading engine, order simulation |
| Risk Engine | **Lambda + Step Functions** | Pre-trade checks (sync), real-time monitors (async) |
| Audit Log | **QLDB** | Immutable append-only log, 7-year retention |
| Kill Switch | **Lambda + SNS + EventBridge** | Circuit breaker, immediate liquidation trigger |

### Monitoring & Alerting

| Component | Service | Purpose |
|---|---|---|
| Metrics Dashboard | **Grafana** (self-hosted on ECS) | Live IC, coverage maps, pipeline latency |
| Infrastructure Metrics | **CloudWatch** | CPU, memory, error rates, SLA tracking |
| Log Aggregation | **CloudWatch Logs** | Centralized logs from all services |
| Alerting | **SNS + PagerDuty** | P0–P3 severity routing |
| Uptime Monitoring | **Route 53 Health Checks** | Signal pipeline SLA tracking |

---

## Secrets Management

| Secret Type | Service | Access Pattern |
|---|---|---|
| API Keys (Copernicus, AIS) | **AWS Secrets Manager** | ECS task role, rotated quarterly |
| Database Credentials | **AWS Secrets Manager** | Auto-rotation enabled |
| MLflow Tracking URI | **SSM Parameter Store** | All compute services |
| Kafka Credentials | **AWS Secrets Manager** | MSK IAM auth |

---

## CI/CD Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  GitHub   │───▶│  GitHub   │───▶│  Build   │───▶│  Test    │───▶│  Deploy  │
│  Push     │    │  Actions  │    │  (Docker) │   │  (pytest) │   │  (CDK)   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │                                               │
                     │         ┌──────────┐                         │
                     └────────▶│  Lint +   │                         │
                               │  Type     │    ┌──────────┐         │
                               │  Check    │    │  Staging  │◀───────┘
                               └──────────┘    │  Deploy   │
                                               └─────┬────┘
                                                     │
                                               ┌─────▼────┐
                                               │  Prod     │
                                               │  Deploy   │
                                               │  (manual) │
                                               └──────────┘
```

| Stage | Tool | Details |
|---|---|---|
| Source Control | **GitHub** | `main` (prod), `develop` (staging), feature branches |
| CI Runner | **GitHub Actions** | On push/PR to `develop` and `main` |
| Linting | `ruff`, `mypy` | Enforced, no untyped code in `src/` |
| Testing | `pytest` | Unit (>80% coverage), integration (against LocalStack) |
| Container Build | **Docker** + **ECR** | Multi-stage builds, vulnerability scanning |
| IaC | **AWS CDK (Python)** | All infrastructure as code, diff-reviewed |
| Deployment | **CDK Deploy** | Staging: automatic; Production: manual approval gate |

---

## Monthly Cost Estimate (Steady State — Phase 1)

| Service | Configuration | Est. Monthly Cost |
|---|---|---|
| S3 Storage | ~500 GB (raw + processed tiles) | $12 |
| RDS PostgreSQL | db.t3.medium, Multi-AZ | $140 |
| MSK (Kafka) | kafka.t3.small × 3 | $200 |
| ECS Fargate (services) | 4 services, 0.5 vCPU / 1GB avg | $120 |
| AWS Batch (preprocessing) | c5.2xlarge spot, ~100 hrs/mo | $80 |
| SageMaker (training) | ml.g5.xlarge, ~40 hrs/mo | $200 |
| Lambda | ~500K invocations/mo | $5 |
| QLDB | ~1 GB storage, ~100K transactions/mo | $30 |
| Grafana (on ECS) | 0.5 vCPU / 1GB | $30 |
| MLflow (on ECS) | 0.5 vCPU / 1GB + RDS share | $30 |
| Label Studio (on ECS) | 0.5 vCPU / 1GB | $30 |
| CloudWatch | Logs + metrics | $50 |
| Secrets Manager | ~20 secrets | $10 |
| **Data transfer** | ~200 GB egress | $18 |
| **Total** | | **~$955/month** |

> [!TIP]
> Phase 1 estimated cost is **$955/month**, well within the $5,000/month compute budget. This leaves significant headroom for Phase 2 scaling (commercial data, more GPU training, increased storage).

---

## Single Points of Failure Analysis

| Component | SPOF Risk | Mitigation |
|---|---|---|
| RDS PostgreSQL | Database failure halts catalog queries | Multi-AZ standby, automated failover |
| MSK Kafka | Event bus failure halts pipeline | 3-broker cluster, replication factor 3 |
| S3 | Extremely low (11 9s durability) | N/A |
| ECS Services | Task failure | Auto-restart, min 2 tasks per service |
| SageMaker Training | Instance failure during training | Checkpointing every epoch, spot interruption handling |
| QLDB | Region-level failure | Cross-region backup (daily), but accept RTO ~4h |
| Secrets Manager | Access failure | Cache secrets locally with 1-hour TTL |
| GitHub Actions | Runner unavailability | Self-hosted runner as fallback |

> [!NOTE]
> **Accepted SPOF**: QLDB does not natively support cross-region replication. Daily snapshots to a second region provide disaster recovery with ~4-hour RTO. This is acceptable for internal research; upgrade to cross-region active-active if moving to regulated framework.

---

## Network Architecture

```
┌──────────────────────────────────────────────────┐
│                    VPC (10.0.0.0/16)              │
│                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │  Public      │  │  Private     │  │  Data     │ │
│  │  Subnet      │  │  Subnet      │  │  Subnet   │ │
│  │              │  │              │  │           │ │
│  │  NAT GW      │  │  ECS Tasks   │  │  RDS      │ │
│  │  ALB         │  │  Lambda      │  │  MSK      │ │
│  │  Grafana     │  │  Batch       │  │  QLDB     │ │
│  │              │  │  SageMaker   │  │           │ │
│  └─────────────┘  └─────────────┘  └───────────┘ │
│                                                    │
│  Security Groups:                                  │
│  - sg-grafana: 443 inbound from VPN/IP whitelist   │
│  - sg-ecs: no inbound, all outbound                │
│  - sg-data: inbound from sg-ecs only, port-specific│
└──────────────────────────────────────────────────┘
```

All satellite API calls go through NAT Gateway. No direct internet access for compute or data subnets. Grafana exposed via ALB with IP whitelist or VPN.
