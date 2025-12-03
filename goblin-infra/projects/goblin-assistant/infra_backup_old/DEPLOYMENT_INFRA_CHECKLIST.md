# Goblin Assistant — Infrastructure Deployment Checklist

This checklist is for teams preparing the infra (edge + K8s + workers) for production. Follow checks below before publishing or promoting releases to production.

## Secrets & Permissions

- [ ] Confirm SOPS-encrypted secrets exist for `dev`, `staging`, and `prod` under `infra/secrets/`.
- [ ] Ensure `sops-age` keys are stored in ArgoCD (or Flux) secret and available to the repo-server.
- [ ] Verify all `wrangler.toml` or Cloudflare token files do not contain plaintext secrets (bind secrets via Cloudflare secret bindings or env in deployment).
- [ ] Rotate any test keys and set production-only secrets in a secrets manager.

## Edge Workers & Cloudflare

- [ ] Deploy edge workers with `wrangler deploy` and validate `wrangler tail` logs for errors.
- [ ] Confirm KV namespaces & D1 database initialized for the worker runtime.
- [ ] Ensure Turnstile is configured and verification occurs server-side.
- [ ] Configure Cloudflare Tunnel and verify the tunnel is active and secure (Area 51 Mode).
- [ ] Verify `X-RateLimit-Limit` and other headers are present (edge level).

## Kubernetes (K8s) Deployments

- [ ] Deploy Ollama cluster (olaama-k8s) with correct image tags and verify readiness/liveness probes.
- [ ] Configure HPA and test autoscaling behavior in staging; tune HPA CPU/memory thresholds and custom metrics (e.g., `litebrain_complexity_score`).
- [ ] Ensure `ServiceMonitor` exists for Prometheus scraping for each service.
- [ ] Validate ingress rules and TLS certs from cert-manager.
- [ ] Double-check resource limits/requests and Pod Disruption Budgets (PDBs).

## Backups & DR

- [ ] Register automated backups for PostgreSQL; validate restore to a test namespace.
- [ ] Verify D1 or SQLite backup strategy if used; ensure a documented snapshot/restore procedure.
- [ ] Add instructions for failover for Ollama nodes or fallback to cloud providers.

## Observability & Alerting

- [ ] Ensure Prometheus scrapes `/metrics` for edge & backend; test by `curl /metrics`.
- [ ] Ensure Datadog agents (if used) are configured on all nodes and APM tracing is enabled in backend.
- [ ] Import Grafana dashboards and validate panels (latency, token usage, provider health, error rates).
- [ ] Set up alerts: provider health, high error rates, high latency, CPU/memory saturation, disk fullness, DB connectivity issues.

## Rate Limiting & WAF

- [ ] Implement distributed rate limiter in backend: Redis-backed sliding window or token bucket.
- [ ] Confirm Edge (Cloudflare) WAF rules and caching are tuned to avoid unnecessary LLM requests.
- [ ] Configure IP & UA-based rate limiting and API key tiers for production.

## Secrets Rotation

- [ ] Set a rotation policy: Postgres password, provider API keys, Cloudflare API tokens, and `ROUTING_ENCRYPTION_KEY`.
- [ ] Ensure a webhook for key rotation in the pipeline or a manual procedure in `infra/secrets/README.md`.

## Network & Security

- [ ] Confirm internal-only endpoints are not public (LLM admin ports, metrics endpoints unless through cluster service).
- [ ] Enable Zero Trust for admin paths using Cloudflare Access (ensures only approved users can visit admin UI).
- [ ] Verify CORS origins are configured properly for the frontend domains.
- [ ] Apply security network policies in Kubernetes to limit lateral movement.

## Pre-Launch Tests

- [ ] Run full smoke tests: login, chat, streaming, execute task, debug/suggest.
- [ ] Run load tests in staging to simulate production workloads against Ollama and cloud fallbacks.
- [ ] Run security scans: kube-linter, Helm chart scanning, secret scanning tool, Snyk or similar.
- [ ] Validate the observability pipeline by generating monitored errors and verifying alerts.

## Post-Launch Ops

- [ ] Monitor initial deployment for 24 hours: check error budget, request latencies, and costs.
- [ ] Ensure provider quotas are sufficient and alert on near-quota thresholds.
- [ ] Confirm that runbooks for common incidents (provider outage, DB outage, runaway job) are easily accessible.

## Rollback & Recovery

- [ ] Verify Argo CD rollback works for the deployed application.
- [ ] Ensure that DB schema migrations are reversible and have a rollback plan.
- [ ] Confirm that key secrets can be reissued and updated without downtime.

---

Keep this file up-to-date with any operational changes or new automation scripts for monitoring, backups, and autoscaling.
