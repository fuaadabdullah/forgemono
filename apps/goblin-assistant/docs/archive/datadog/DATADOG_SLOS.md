# Datadog SLOs for Goblin Assistant

This file contains recommended Service Level Objectives (SLOs) and Datadog monitor configurations for the MCP (Model Control Plane).

## SLO Definitions

1. Request Latency
   - SLI: 95th percentile of `assistant.latency_ms` for `service:goblin-api` over 1 hour.
   - SLO: 95% <= 1500ms
   - Datadog Query: `p95(last_1h):avg:assistant.latency_ms{service:goblin-api}.rollup(max, 60)`

2. Error Rate
   - SLI: Percentage of MCP requests that return status `failed` (or `error` counter) over 1 hour.
   - SLO: <= 3% (weekly)
   - Datadog Query: `100 * (sum:request.count{service:goblin-api,status:failed}.as_count() / sum:request.count{service:goblin-api}.as_count())`

3. Fallback Rate
   - SLI: Percentage of requests that used `mock`/fallback provider over 24 hours.
   - SLO: <= 5%
   - Datadog Query: `100 * (sum:provider.fallbacks{service:goblin-api}.as_count() / sum:request.count{service:goblin-api}.as_count())`

## Suggested Datadog Monitors

- Latency: monitor `assistant.latency_ms` p95 exceeding 1500ms for 15 minutes -> severity P2 -> page on-call.
- Error Rate: monitor error rate be above 3% for 15 minutes -> severity P1 -> page on-call.
- Fallback Rate: monitor fallback rate > 5% for 30 minutes -> severity P2 -> create a ticket.

## Creating SLOs in Datadog

1. Go to Datadog -> SLOs -> Create SLO.
2. Choose metric SLO and enter the query above.
3. Set the target and timeframe.
4. Add alerting and notifying channels (Ops Slack, email, or on-call rotation).

## Notes

- For production systems, set SLO targets informed by historical traffic and customer expectations.
- Adjust p95 threshold depending on model and latency expectations (if local models run slower, increase threshold).

---
Last updated: 2025-11-26
