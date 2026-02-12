# Production Readiness & Release Checklist

This checklist ensures that a release meets security, performance, monitoring, and testing standards.

## Owners

- Security: Sealkeeper (`sentenial-ledgerwarden`)
- Observability & Dashboards: Fine Spellchecker (`launcey-gauge`)
- Performance & Load Testing: Forecasting Fiend (`hex-oracle`)
- Platform Operations: Socketwright (`volt-furnace`)

## Pre-release (Developer)

1. Code review completed; tests pass locally and in CI (unit/integration/e2e).
2. No secrets are committed; all provider keys are on Vault; review `gitleaks`/SOPS checks.
3. Linting and formatting pass.
4. DB migrations prepared and included; tested locally using migration script.
5. Security scan results are reviewed; any critical issues remediated.

## Release candidate (QA / Staging)

1. Smoke tests (functional): passes in staging.
2. Load test at expected production traffic: no SLO violations.
3. Observability & Dashboards: Datadog dashboards show expectations, and alert thresholds are configured.
4. Secrets rotation validated: Vault access and rotated keys work for the service.
5. Performance: p95 latency under 1500 ms for 95% of requests.

## Production release (Ops)

1. Run pre-deploy checklist: back up DB, snapshots, and confirm Rollback playbook.
2. Deploy rolling update or canary with limited traffic.
3. Validate no 5xx errors and SLOs across canary.
4. Notify stakeholders (Slack & on-call) and confirm monitors.
5. After verified, promote full deployment.

## Post-release (All)

1. Monitor for 30 minutes for anomalies (errors, high latency, fallback increase).
2. Update incident/CC docs for any issues and ensure follow-up tickets are created.
3. Rotate any temporary keys used during deployment and clear access.

## Critical Security Steps (always)

- Rotate API keys in Vault if a provider key was updated or compromised.
- Run a secret-scan of repo to ensure nothing new is leaked.
- Ensure RBAC policies limiting production secret access are enforced.

---
Last updated: 2025-11-26
