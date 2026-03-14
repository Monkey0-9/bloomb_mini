# Physical Holdout Enforcement Policy

## Objective
To prevent look-ahead bias and model overfit by ensuring training environments have no physical path to the blind validation (holdout) data.

## Enforcement Mechanism
1.  **Logical Isolation**: Training scripts are strictly prohibited from indexing the `holdout/` directory.
2.  **Identity-Based Access (IAM)**:
    - The `TrainingService` IAM role is explicitly denied `s3:GetObject` on the `s3://sattrade-data/holdout/` prefix.
    - Only the `ValidationService` role (run post-training) has read access to the holdout set.
3.  **Cryptographic Locking**:
    - Training data and Holdout data are encrypted with distinct KMS keys.
    - Training compute instances do not possess the decryption grant for the Holdout KMS key.
4.  **CI/CD Guardrail**:
    - The build pipeline fails if any file path in `src/features/` or `src/signals/` includes the substring `holdout`.

## Audit Procedure
The "External Risk Consultant" shall verify these IAM policies and KMS key grants as part of the Phase 12 readiness review.
