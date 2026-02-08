---title: Argo CD GitOps for Overmind
type: reference
project: GoblinOS/Overmind
status: published
owner: GoblinOS
goblin_name: Overmind GitOps
description: "README"

---

# Argo CD GitOps Setup

GitOps deployment automation for Overmind using [Argo CD](https://argo-cd.readthedocs.io/).

## Overview

Argo CD provides:

- ✅ **Declarative GitOps** - Infrastructure as code from Git
- ✅ **Automated sync** - Continuous deployment from Git commits
- ✅ **SOPS integration** - Encrypted secrets with KSOPS plugin
- ✅ **Multi-environment** - Dev, staging, production
- ✅ **Rollback support** - Easy revert to previous versions
- ✅ **Health monitoring** - Real-time application status
- ✅ **Sync waves** - Ordered deployment dependencies

## Architecture

```
Git Repository (source of truth)
├── infra/charts/           # Helm charts
│   ├── litellm/
│   └── temporal-worker/
├── infra/overlays/         # Kustomize overlays
│   ├── dev/
│   └── prod/
├── infra/secrets/          # SOPS-encrypted secrets
│   ├── dev/
│   └── prod/
└── infra/gitops/           # Argo CD Applications
    └── applications/
        ├── overmind-dev.yaml
        └── overmind-prod.yaml

Argo CD → Monitors Git → Syncs to Kubernetes
```

## Quick Start

### Prerequisites

```bash
# Install Argo CD CLI
brew install argocd

# Or via script
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd
sudo mv argocd /usr/local/bin/
```

### Install Argo CD

```bash

# Create namespace
kubectl create namespace argocd

# Install Argo CD
kubectl apply -n argocd -f <https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml>

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s
```

### Install KSOPS Plugin (for SOPS secrets)

```bash
# Apply KSOPS-enabled Argo CD patch
kubectl apply -f infra/gitops/argocd/argocd-repo-server-ksops-patch.yaml

# Restart repo server
kubectl rollout restart deployment argocd-repo-server -n argocd
```

### Access Argo CD UI

```bash

# Port forward
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get initial admin password
argocd admin initial-password -n argocd

# Open browser
open <https://localhost:8080>

# Login (username: admin, password from above)
argocd login localhost:8080
```

### Change Admin Password

```bash
argocd account update-password
```

## Application Deployment

### Deploy Overmind Dev Environment

```bash

# Apply Application manifest
kubectl apply -f infra/gitops/applications/overmind-dev.yaml

# Watch sync progress
argocd app get overmind-dev

# Sync manually (if auto-sync disabled)
argocd app sync overmind-dev

# View sync status
argocd app wait overmind-dev --health
```

### Deploy Overmind Production Environment

```bash
# Apply Application manifest
kubectl apply -f infra/gitops/applications/overmind-prod.yaml

# Sync with confirmation
argocd app sync overmind-prod --async

# Monitor deployment
argocd app get overmind-prod --refresh
```

## Application Manifests

### Development Environment

**File:** `applications/overmind-dev.yaml`

```yaml

apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: overmind-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: <https://github.com/your-org/ForgeMonorepo.git>
    targetRevision: main
    path: infra/overlays/dev
  destination:
    server: <https://kubernetes.default.svc>
    namespace: overmind-dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:

    - CreateNamespace=true
```

### Production Environment

**File:** `applications/overmind-prod.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: overmind-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/ForgeMonorepo.git
    targetRevision: release/v1.0
    path: infra/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: overmind-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

## SOPS Integration

### KSOPS Plugin Configuration

**File:** `argocd/argocd-repo-server-ksops-patch.yaml`

```yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: argocd-repo-server
  namespace: argocd
spec:
  template:
    spec:
      volumes:

      - name: custom-tools
        emptyDir: {}

      - name: sops-age
        secret:
          secretName: sops-age
      initContainers:

      - name: install-ksops
        image: viaductoss/ksops:v4.3.2
        command: ["/bin/sh", "-c"]
        args:

        - echo "Installing KSOPS...";
          cp ksops /custom-tools/;
          cp $GOPATH/bin/kustomize /custom-tools/;
          echo "Done.";
        volumeMounts:

        - mountPath: /custom-tools
          name: custom-tools
      containers:

      - name: argocd-repo-server
        volumeMounts:

        - mountPath: /usr/local/bin/ksops
          name: custom-tools
          subPath: ksops

        - mountPath: /usr/local/bin/kustomize
          name: custom-tools
          subPath: kustomize

        - mountPath: /home/argocd/.config/sops/age
          name: sops-age
        env:

        - name: XDG_CONFIG_HOME
          value: /home/argocd/.config

        - name: SOPS_AGE_KEY_FILE
          value: /home/argocd/.config/sops/age/keys.txt
```

### Add Age Key Secret

```bash
# Create secret with age private key
kubectl create secret generic sops-age \
  --from-file=keys.txt=~/.config/sops/age/keys.txt \
  -n argocd

# Verify
kubectl get secret sops-age -n argocd
```

## Sync Waves

Use sync waves to control deployment order:

```yaml

apiVersion: v1
kind: Secret
metadata:
  name: postgres-credentials
  annotations:
    argocd.argoproj.io/sync-wave: "0"  # Deploy first
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: overmind-api
  annotations:
    argocd.argoproj.io/sync-wave: "1"  # Deploy after secrets
---
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  annotations:
    argocd.argoproj.io/sync-wave: "2"  # Run after deployment
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
