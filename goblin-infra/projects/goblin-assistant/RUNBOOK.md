# GoblinOS Assistant - Infra Runbook

This runbook is for on-call engineers and deployers who need to manage the GoblinOS Assistant infrastructure.

## Quick Validation
- Confirm Bitwarden access and that the Bitwarden session has been created
  - `bw login --raw` (or check `BW_SESSION`) – ensure proper access
  - `./apps/goblin-assistant/scripts/test_vault.sh` to validate secrets
- Verify Terraform state and plan (for infra changes)
  - `cd goblin-infra/envs/dev && terraform plan`
  - Use Terraform Cloud workflows for plan/apply as configured in CI
- Verify Kubernetes manifests and local Kustomize overlays
  - `kustomize build apps/goblin-assistant/infra/overlays/prod | kubectl apply -f - --dry-run=client`
  - `helm lint` for Helm charts in `infra/charts`

## Deploying (Kubernetes - GitOps)
1. Update overlay in `apps/goblin-assistant/infra/overlays/<env>/`.
2. Push changes and let ArgoCD pick up the new manifests (or manually apply):
   - `kubectl -n argocd port-forward svc/argocd-server 8080:80` and navigate to ArgoCD UI
   - Or `argocd app sync <app-name>`

## Deploying (Fly.io)
1. Validate `fly.toml` under `apps/goblin-assistant/` and ensure resources are set.
2. Set secrets: `fly secrets set JWT_SECRET_KEY=...` (or use Bitwarden secrets loader)
3. Deploy: `./apps/goblin-assistant/deploy-fly.sh` (or `flyctl deploy`)

## Rollback (Kubernetes)
- Use `kubectl rollout undo`:
  - `kubectl rollout undo deployment/<name> -n <namespace>`
  - Check the date/time diff: `kubectl rollout history deployment/<name>`
- If ingress changes broke the environment: revert ingress or DNS routing changes first.

## Rollback (Fly)
- Revert to last stable release with `flyctl`:
  - `flyctl releases list --app <app>` to find last release
  - `flyctl releases promote <release-id>` or `flyctl rollback <release-id>`

## Data & Secrets Compromise
- If secrets are compromised, rotate secrets in Bitwarden and trigger a rolling restart in both Fly and Kubernetes environments.
- Rotate JWT keys and provider keys (Anthropic/OpenAI). Update env stores and redeploy.

## Observability & Alerts
- Prometheus alerts: `infra/observability/alertmanager/` has playbooks and runbooks
- Dashboards and SLOs: Grafana dashboards in `infra/observability/grafana/dashboards` (copy from rendering)

## Post-deploy checks
- Smoke tests: `apps/goblin-assistant/tools/smoke.sh`
- Health checks: `curl -f -s https://<host>/health` and `/metrics`
- Logs: Check Loki / Datadog traces and Grafana dashboards

## Escalation
- Who to escalate to: See `docs/WORKSPACE_OVERVIEW.md` -> Keepers/Mages guild.
- Contact details: `owners/email` in README (if present) or use GoblinOS admin channel.

