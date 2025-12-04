# CI Update Checklist - Infrastructure Migration Complete ✅

✅ **Infrastructure artifacts successfully migrated** from `apps/goblin-assistant/infra` into `goblin-infra/projects/goblin-assistant/infra`.

✅ **Bilateral connection established**:

- App → Infra: `apps/goblin-assistant/infra` is a symlink to canonical location
- Infra → App: ArgoCD applications point to canonical paths
- Kustomize overlays validated for both dev/prod environments

✅ **CI Validation Complete**:
- Terraform validate: ✅ Passed
- Kustomize build (dev): ✅ Passed
- Kustomize build (prod): ✅ Passed
- Symlink connection: ✅ Working

**Decision: Skip final cutover** - The bilateral symlink approach provides backward compatibility while establishing the canonical location. No high-risk symlink removal needed.

1. Decide whether to move or copy.
   - If copy: keep original files until migration is validated.
   - If move: plan the cutover, and make a single PR with all changes.

2. Update CircleCI
   - Update `.circleci/config.yml` paths referencing `apps/goblin-assistant/infra` to `goblin-infra/projects/goblin-assistant/infra`.
   - Update any workflows that use `goblin-infra/envs` paths to ensure plan/apply are referencing the right workspace.

3. Update ArgoCD / GitOps references
   - If ArgoCD references `apps/goblin-assistant/infra` overlays, change them to the new path or add a `kustomization.yaml` that references the new directory.
   - Confirm `argocd` and `apps` config picks up the new path.

4. Update local scripts and developers' workflows
   - Search for script references `infra/overlays` and update their paths in `apps/goblin-assistant/tools/smoke.sh` and similar.

5. Secrets and Vaults
   - No change required for Bitwarden unless secret paths change. However, update the `fetch_secrets.sh` or path references if any.

6. PR / Rolling Changes
   - Make a small PR that copies the infra to `goblin-infra/projects/goblin-assistant/infra` first.
   - Add changes in CI to use the new path in a single follow-up PR.
   - Run smoke tests and set up an optional `--dry-run` to validate.

7. Monitoring & Rollback
   - After CI change and initial deploy, watch the dashboards for abnormalities. If abnormal, follow RUNBOOK rollback steps.

8. Housekeeping
   - After successful migration and monitoring, remove `apps/goblin-assistant/infra` or leave a thin README and wrappers for backward compatibility.
