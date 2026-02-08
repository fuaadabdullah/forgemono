# Observability & Runbook

This runbook provides a short, actionable guide for on-call engineers when an alert triggers for the Goblin Assistant MCP service.

## Primary Contacts

- Platform Owner (Ops) - Socketwright (`volt-furnace`)
- Security Owner (Secrets) - Sealkeeper (`sentenial-ledgerwarden`)
- Observability Owner - Fine Spellchecker / Mages gang (`launcey-gauge`)

## Common Alerts and Triage

1. Latency Spike (P2/P1 depending on severity)
   - Check Datadog p95/mean latency and timeline for the spike.
   - Inspect recent provider calls and circuit breaker state (use the admin dashboard `/admin/dashboard`).
   - If explained by load or model fallback, throttle new traffic if necessary and escalate.

2. Error Rates Increasing (P1)
   - Check Datadog logs for exceptions; find stack traces and correlated request IDs.
   - Check provider availability, circuit breakers, and API quotas.
   - If provider credentials are failing, confirm Vault API key validity and rotation status.

3. Fallback Rate Increase (P2)
   - Check provider health, circuit breaker states and counts (via `mcp_providers.ProviderManager` statuses).
   - If fallback rate persists, run a manual test request with a stable provider and check response.

## Immediate Actions

1. Gather breadcrumbs
   - Request IDs from Datadog dashboard, worker logs and `mcp_event` table for examples.
2. Try soft remediation
   - Restart worker processes or scale-up temporarily.
   - If Redis or storage is flaky, restart those services.
3. Rollback or scale down suspect changes
   - Revert to last known good Docker image and re-check SLOs.
4. Engage provider vendors if quotas or API issues are suspected.

## Post-Incident

1. Update the incident report (JIRA/GitHub) with root cause analysis and timeline.
2. Add new alerts or tune thresholds if needed.
3. Schedule follow-up tasks (fixes, tests, capacity plan).

## Runbook References

- Datadog dashboards: `admin/dashboard` and `goblin.mcp.*` metrics.
- Database queries: Use `mcp_event` for recent traces.
- Vault and secrets: `vault_client` usage, check `docs/vault_integration.md` for recovery steps.

---
Last updated: 2025-11-26
