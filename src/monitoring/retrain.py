"""
Retraining Scheduler — Phase 8.2

Trigger conditions for model retraining:
  - Monthly: PSI > 0.2 on any feature → full retrain
  - Monthly: PSI 0.1-0.2 → fine-tuning
  - Quarterly: scheduled retrain on expanding window
  - On-demand: manual trigger by research analyst

Expanding window only — never shrink training data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RetrainTrigger(str, Enum):
    SCHEDULED_QUARTERLY = "scheduled_quarterly"
    DRIFT_FULL_RETRAIN = "drift_full_retrain"  # PSI > 0.2
    DRIFT_FINE_TUNE = "drift_fine_tune"  # PSI 0.1-0.2
    IC_DEGRADATION = "ic_degradation"  # 10 days below P10
    MANUAL = "manual"


class RetrainStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    APPROVED = "approved"  # Promoted to staging
    REJECTED = "rejected"  # Did not beat baseline


@dataclass
class RetrainJob:
    """A single retraining job."""

    job_id: str
    trigger: RetrainTrigger
    model_name: str
    status: RetrainStatus = RetrainStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    train_data_start: datetime | None = None
    train_data_end: datetime | None = None
    baseline_sharpe: float | None = None
    new_sharpe: float | None = None
    improvement_delta: float | None = None
    drift_psi: float | None = None
    notes: str = ""


class RetrainingScheduler:
    """
    Orchestrates model retraining based on drift detection and schedules.

    Key invariant: always uses expanding training window — never shrinks.
    New model must beat current production by ≥ 0.02 Sharpe to be promoted.
    """

    MIN_SHARPE_IMPROVEMENT = 0.02
    QUARTERLY_INTERVAL_DAYS = 90
    IC_ALERT_CONSECUTIVE_DAYS = 10

    def __init__(self) -> None:
        self._jobs: list[RetrainJob] = []
        self._last_quarterly_retrain: datetime | None = None
        self._training_data_start: datetime = datetime(2020, 1, 1, tzinfo=UTC)

    def check_triggers(
        self,
        feature_drift_results: dict[str, dict[str, Any]] | None = None,
        ic_below_p10_days: int = 0,
        current_time: datetime | None = None,
    ) -> list[RetrainJob]:
        """Check all retrain triggers and create jobs as needed."""
        now = current_time or datetime.now(UTC)
        new_jobs: list[RetrainJob] = []

        # 1. Quarterly scheduled retrain
        if self._should_quarterly_retrain(now):
            job = self._create_job(
                RetrainTrigger.SCHEDULED_QUARTERLY,
                f"Quarterly retrain ({now.strftime('%Y-Q%q' if hasattr(now, 'quarter') else '%Y-%m')})",
                now,
            )
            new_jobs.append(job)
            self._last_quarterly_retrain = now

        # 2. Drift-triggered retrain
        if feature_drift_results:
            max_psi = 0.0
            drifted_features = []

            for feature_name, result in feature_drift_results.items():
                psi = result.get("psi", 0.0)
                classification = result.get("classification", "STABLE")
                max_psi = max(max_psi, psi)

                if classification in ("SIGNIFICANT_DRIFT", "MODERATE_DRIFT"):
                    drifted_features.append(feature_name)

            if max_psi >= 0.2:
                job = self._create_job(
                    RetrainTrigger.DRIFT_FULL_RETRAIN,
                    f"PSI {max_psi:.3f} ≥ 0.2 on features: {', '.join(drifted_features)}",
                    now,
                )
                job.drift_psi = max_psi
                new_jobs.append(job)
            elif max_psi >= 0.1:
                job = self._create_job(
                    RetrainTrigger.DRIFT_FINE_TUNE,
                    f"PSI {max_psi:.3f} ≥ 0.1 on features: {', '.join(drifted_features)}",
                    now,
                )
                job.drift_psi = max_psi
                new_jobs.append(job)

        # 3. IC degradation trigger
        if ic_below_p10_days >= self.IC_ALERT_CONSECUTIVE_DAYS:
            job = self._create_job(
                RetrainTrigger.IC_DEGRADATION,
                f"IC below P10 for {ic_below_p10_days} consecutive days",
                now,
            )
            new_jobs.append(job)

        return new_jobs

    def evaluate_retrained_model(
        self,
        job_id: str,
        new_sharpe: float,
        baseline_sharpe: float,
    ) -> bool:
        """
        Evaluate retrained model against production baseline.
        Must beat by ≥ 0.02 Sharpe to be promoted.
        """
        job = next((j for j in self._jobs if j.job_id == job_id), None)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.baseline_sharpe = baseline_sharpe
        job.new_sharpe = new_sharpe
        job.improvement_delta = new_sharpe - baseline_sharpe
        job.completed_at = datetime.now(UTC)

        if job.improvement_delta >= self.MIN_SHARPE_IMPROVEMENT:
            # Phase 7: Enforce hard 4-week A/B forward walk OOS
            if self._verify_ab_oos_period(job):
                job.status = RetrainStatus.APPROVED
                logger.info(
                    f"RETRAIN APPROVED: {job.model_name} — "
                    f"+{job.improvement_delta:.4f} Sharpe improvement. "
                    f"Registering as STAGING."
                )
                return True
            else:
                job.status = RetrainStatus.FAILED
                job.notes += " | FAILED A/B OOS: Period < 4 weeks"
                logger.error(
                    f"RETRAIN FAILED: {job.model_name} did not satisfy 4-week A/B OOS requirement."
                )
                return False
        else:
            job.status = RetrainStatus.REJECTED
            logger.info(
                f"RETRAIN REJECTED: {job.model_name} — "
                f"+{job.improvement_delta:.4f} Sharpe improvement "
                f"< {self.MIN_SHARPE_IMPROVEMENT} threshold."
            )
            return False

    def _verify_ab_oos_period(self, job: RetrainJob) -> bool:
        """Ensure the out-of-sample (OOS) validation period is exactly 4 weeks."""
        if not job.train_data_end or not job.completed_at:
            return False

        oos_duration = job.completed_at - job.train_data_end
        # Requirement: At least 28 days of out-of-sample forward walk
        return oos_duration >= timedelta(weeks=4)

    def manual_trigger(self, operator_id: str, reason: str) -> RetrainJob:
        """Manual retrain trigger by research analyst."""
        now = datetime.now(UTC)
        job = self._create_job(
            RetrainTrigger.MANUAL,
            f"Manual trigger by {operator_id}: {reason}",
            now,
        )
        logger.info(f"Manual retrain triggered by {operator_id}: {reason}")
        return job

    def get_pending_jobs(self) -> list[RetrainJob]:
        return [j for j in self._jobs if j.status == RetrainStatus.PENDING]

    def get_job_history(self) -> list[RetrainJob]:
        return list(self._jobs)

    def _create_job(self, trigger: RetrainTrigger, notes: str, now: datetime) -> RetrainJob:
        import uuid

        job = RetrainJob(
            job_id=str(uuid.uuid4()),
            trigger=trigger,
            model_name="sattrade_ensemble",
            train_data_start=self._training_data_start,
            train_data_end=now,
            notes=notes,
        )
        self._jobs.append(job)
        return job

    def _should_quarterly_retrain(self, now: datetime) -> bool:
        if self._last_quarterly_retrain is None:
            return True
        return (now - self._last_quarterly_retrain).days >= self.QUARTERLY_INTERVAL_DAYS
