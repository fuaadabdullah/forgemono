---
title: "README"
description: "ConfigMap for custom health check"
---


apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  annotations:
    argocd.argoproj.io/sync-wave: '2' # Run after deployment
```

## Health Checks

Argo CD monitors resource health automatically. Custom health checks:

```yaml
# ConfigMap for custom health check
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  resource.customizations: |
    apps/Deployment:
      health.lua: |
        hs = {}
        if obj.status ~= nil then
          if obj.status.availableReplicas == obj.spec.replicas then
            hs.status = "Healthy"
            hs.message = "All replicas are running"
          else
            hs.status = "Progressing"
            hs.message = "Waiting for replicas"
          end
        end
        return hs
```

## Multi-Environment Strategy

### Branch-based Environments

- `main` → dev environment (overmind-dev namespace)
- `release/v*` → prod environment (overmind-prod namespace)
- `feature/*` → ephemeral preview environments

### Application Sets

For managing multiple environments with less duplication:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: overmind-environments
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: dev
            revision: main
            namespace: overmind-dev

          - env: prod
            revision: release/v1.0
            namespace: overmind-prod
  template:
    metadata:
      name: 'overmind-{{env}}'
    spec:
      project: default
      source:
        repoURL: <https://github.com/your-org/ForgeMonorepo.git>
        targetRevision: '{{revision}}'
        path: 'infra/overlays/{{env}}'
      destination:
        server: <https://kubernetes.default.svc>
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

## Rollback

### Via CLI

```bash
# List sync history
argocd app history overmind-prod

# Rollback to previous version
argocd app rollback overmind-prod <HISTORY_ID>

# Rollback to specific revision
argocd app rollback overmind-prod 0  # Latest
```

### Via UI

1. Navigate to application
1. Click "History and Rollback"
1. Select previous successful sync
1. Click "Rollback"

## Notifications

### Slack Integration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: $slack-token
  template.app-deployed: |
    message: |
      Application {{.app.metadata.name}} deployed to {{.app.spec.destination.namespace}}
      Revision: {{.app.status.sync.revision}}
  trigger.on-deployed: |

    - when: app.status.operationState.phase in ['Succeeded']
      send: [app-deployed]
```

## Best Practices

1. **Use Git as source of truth** - All changes via Git commits
1. **Enable auto-sync cautiously** - Start manual, automate when confident
1. **Use sync waves** - Control deployment order
1. **Encrypt secrets with SOPS** - Never commit plain secrets
1. **Monitor sync status** - Set up alerts for failed syncs
1. **Use ApplicationSets** - Reduce duplication across environments
1. **Tag production releases** - Use semantic versioning
1. **Test in dev first** - Validate changes before production

## Monitoring

### Prometheus Metrics

Argo CD exposes metrics on port 8083:

- `argocd_app_sync_total`
- `argocd_app_health_status`
- `argocd_app_sync_status`

### Grafana Dashboards

Import official dashboards:

- Argo CD Application Overview (ID: 14584)
- Argo CD Operational Overview (ID: 14585)

## Troubleshooting

### "Application health degraded"

```bash
# Check application details
argocd app get overmind-dev

# Check pod status
kubectl get pods -n overmind-dev

# View logs
kubectl logs -n overmind-dev deployment/overmind-api
```

### "Sync failed: SOPS decryption error"

```bash

# Verify age key secret exists
kubectl get secret sops-age -n argocd

# Check repo server logs
kubectl logs -n argocd deployment/argocd-repo-server | grep -i sops
```

### "Out of sync" status

```bash
# Refresh application
argocd app get overmind-dev --refresh

# Hard refresh (ignore cache)
argocd app get overmind-dev --hard-refresh

# Manual sync
argocd app sync overmind-dev
```

## References

- [Argo CD Documentation](https://argo-cd.readthedocs.io/)
- [KSOPS Plugin](https://github.com/viaduct-ai/kustomize-sops)
- [Application CRD](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/)
- [Sync Waves](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/)

## License

MIT
