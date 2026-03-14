"""
AWS CDK Infrastructure — Phase 0.3

Defines the complete AWS infrastructure stack per the Infrastructure Blueprint.

Services:
  - S3: Raw tile storage (immutable)
  - RDS: Feature store metadata
  - MSK: Kafka for event pipeline
  - ECS: Container orchestration for pipeline services
  - AWS Batch: Preprocessing compute
  - SageMaker: Model training & inference
  - Lambda: Lightweight trigger functions
  - QLDB: Immutable audit ledger
  - CloudWatch + Grafana: Monitoring

Phase 1 estimated cost: ~$955/month
"""

from __future__ import annotations

# CDK imports (in production: pip install aws-cdk-lib constructs)
# This module defines the stack structure — CDK is used at deploy time.

STACK_CONFIG = {
    "stack_name": "SatTradeStack",
    "region": "us-east-1",
    "environment": "staging",  # staging | production
}


def define_stack() -> dict:
    """
    Define the complete SatTrade AWS infrastructure.
    Returns a declarative stack configuration.
    """
    return {
        "metadata": {
            "stack_name": STACK_CONFIG["stack_name"],
            "region": STACK_CONFIG["region"],
            "description": "Satellite-Based AI Trading System Infrastructure",
            "tags": {
                "Project": "SatTrade",
                "Environment": STACK_CONFIG["environment"],
                "CostCenter": "research",
            },
        },

        # ── Storage ──────────────────────────────────────────
        "s3_buckets": {
            "raw_tiles": {
                "bucket_name": "sattrade-raw-tiles",
                "versioned": True,
                "lifecycle_rules": [
                    {"transition_to_ia": 90, "transition_to_glacier": 365},
                ],
                "encryption": "AES256",
                "block_public_access": True,
                "immutable": True,  # Object Lock
                "cors": [],
            },
            "processed_tiles": {
                "bucket_name": "sattrade-processed-tiles",
                "versioned": True,
                "lifecycle_rules": [
                    {"transition_to_ia": 180},
                ],
                "encryption": "AES256",
            },
            "model_artifacts": {
                "bucket_name": "sattrade-model-artifacts",
                "versioned": True,
                "encryption": "AES256",
            },
            "backtest_results": {
                "bucket_name": "sattrade-backtest-results",
                "versioned": True,
                "encryption": "AES256",
            },
        },

        # ── Database ─────────────────────────────────────────
        "rds": {
            "instance_class": "db.t3.medium",
            "engine": "postgres",
            "engine_version": "15.4",
            "database_name": "sattrade",
            "multi_az": False,  # Single AZ for staging; True for production
            "storage_gb": 100,
            "storage_encrypted": True,
            "backup_retention_days": 7,
            "deletion_protection": True,
            "monitoring_interval_seconds": 60,
        },

        "qldb": {
            "ledger_name": "sattrade-audit-ledger",
            "deletion_protection": True,
            "permissions_mode": "STANDARD",
            "tables": [
                "risk_checks",
                "order_executions",
                "model_deployments",
                "kill_switch_events",
                "data_ingestion_events",
            ],
        },

        # ── Streaming ────────────────────────────────────────
        "msk": {
            "cluster_name": "sattrade-kafka",
            "kafka_version": "3.5.1",
            "broker_instance_type": "kafka.t3.small",
            "number_of_broker_nodes": 2,
            "ebs_storage_gb": 100,
            "encryption_in_transit": True,
            "topics": [
                {"name": "raw.tiles.new", "partitions": 6, "replication": 2},
                {"name": "raw.tiles.rejected", "partitions": 3, "replication": 2},
                {"name": "processed.tiles", "partitions": 6, "replication": 2},
                {"name": "signals.scored", "partitions": 6, "replication": 2},
                {"name": "risk.alerts", "partitions": 3, "replication": 2},
                {"name": "risk.kill_switch", "partitions": 1, "replication": 2},
                {"name": "monitoring.drift", "partitions": 3, "replication": 2},
            ],
        },

        # ── Compute ──────────────────────────────────────────
        "ecs": {
            "cluster_name": "sattrade-cluster",
            "services": [
                {
                    "name": "sentinel-ingestor",
                    "cpu": 1024,
                    "memory": 2048,
                    "desired_count": 1,
                    "container_image": "sattrade:latest",
                    "command": ["src.ingest.sentinel"],
                    "schedule": "rate(6 hours)",
                },
                {
                    "name": "ais-ingestor",
                    "cpu": 512,
                    "memory": 1024,
                    "desired_count": 1,
                    "container_image": "sattrade:latest",
                    "command": ["src.ingest.ais"],
                    "schedule": "rate(1 day)",
                },
                {
                    "name": "signal-scorer",
                    "cpu": 2048,
                    "memory": 4096,
                    "desired_count": 1,
                    "container_image": "sattrade:latest",
                    "command": ["src.execution.signal_scoring"],
                },
                {
                    "name": "risk-engine",
                    "cpu": 1024,
                    "memory": 2048,
                    "desired_count": 1,
                    "container_image": "sattrade:latest",
                    "command": ["src.execution.risk_engine"],
                },
            ],
        },

        "batch": {
            "compute_environment": "sattrade-preprocess",
            "instance_types": ["c5.2xlarge", "c5.4xlarge"],
            "min_vcpus": 0,
            "max_vcpus": 32,
            "job_definitions": [
                {
                    "name": "optical-preprocess",
                    "vcpus": 4,
                    "memory": 16384,
                    "container_image": "sattrade:latest",
                    "command": ["src.preprocess.optical"],
                },
                {
                    "name": "sar-preprocess",
                    "vcpus": 4,
                    "memory": 16384,
                    "container_image": "sattrade:latest",
                    "command": ["src.preprocess.sar"],
                },
                {
                    "name": "thermal-preprocess",
                    "vcpus": 2,
                    "memory": 8192,
                    "container_image": "sattrade:latest",
                    "command": ["src.preprocess.thermal"],
                },
            ],
        },

        "sagemaker": {
            "training_instance_type": "ml.g4dn.xlarge",
            "inference_instance_type": "ml.t3.medium",
            "model_registry": "sattrade-models",
        },

        # ── Networking ───────────────────────────────────────
        "vpc": {
            "cidr": "10.0.0.0/16",
            "max_azs": 2,
            "nat_gateways": 1,
            "subnets": {
                "public": [
                    {"cidr": "10.0.1.0/24", "az": "us-east-1a"},
                    {"cidr": "10.0.2.0/24", "az": "us-east-1b"},
                ],
                "private": [
                    {"cidr": "10.0.10.0/24", "az": "us-east-1a"},
                    {"cidr": "10.0.11.0/24", "az": "us-east-1b"},
                ],
                "isolated": [
                    {"cidr": "10.0.20.0/24", "az": "us-east-1a"},
                    {"cidr": "10.0.21.0/24", "az": "us-east-1b"},
                ],
            },
        },

        # ── Monitoring ───────────────────────────────────────
        "monitoring": {
            "cloudwatch_alarms": [
                {
                    "name": "DataPipelineOutage",
                    "metric": "sattrade_tiles_processed_total",
                    "threshold": 0,
                    "comparison": "LessThanOrEqualToThreshold",
                    "evaluation_periods": 4,
                    "period_seconds": 3600,
                    "action": "sns:sattrade-alerts",
                },
                {
                    "name": "HighLatency",
                    "metric": "sattrade_pipeline_latency_seconds_p95",
                    "threshold": 21600,  # 6 hours
                    "comparison": "GreaterThanThreshold",
                    "evaluation_periods": 1,
                    "period_seconds": 3600,
                    "action": "sns:sattrade-alerts",
                },
                {
                    "name": "KillSwitchActivated",
                    "metric": "sattrade_kill_switch_total",
                    "threshold": 0,
                    "comparison": "GreaterThanThreshold",
                    "evaluation_periods": 1,
                    "period_seconds": 60,
                    "action": "sns:sattrade-critical",
                },
            ],
            "grafana": {
                "workspace_name": "sattrade-monitoring",
                "data_sources": ["CloudWatch", "Prometheus"],
            },
        },

        # ── Secrets ──────────────────────────────────────────
        "secrets_manager": [
            "sattrade/copernicus-cdse",
            "sattrade/usgs-m2m",
            "sattrade/planet-api",
            "sattrade/capella-api",
            "sattrade/spire-api",
            "sattrade/rds-credentials",
        ],

        # ── Cost Estimate (Phase 1) ─────────────────────────
        "cost_estimate_monthly_usd": {
            "s3": 50,
            "rds": 100,
            "msk": 200,
            "ecs": 150,
            "batch": 200,
            "sagemaker": 100,
            "networking": 50,
            "monitoring": 30,
            "qldb": 25,
            "secrets_manager": 5,
            "ecr": 10,
            "data_transfer": 35,
            "total": 955,
        },
    }
