# Deployment Templates

This folder contains ready-to-customize deployment templates and CI workflows for common Kubernetes targets and ECS. These templates are designed to work with the unified telemetry plan mentioned in the docs.

## Available Templates

### Amazon ECS

- **Location**: `ecs/`
- **Use Case**: Serverless container orchestration on AWS
- **Components**: Task definition, GitHub Actions workflow, ECR integration
- **Quick Start**: Copy `.github-workflow-deploy-ecs.yml` to `.github/workflows/deploy-ecs.yml`

### Azure AKS

- **Location**: `aks/`
- **Use Case**: Managed Kubernetes on Azure
- **Components**: K8s manifests (Deployment + Service + HPA), ACR integration
- **Quick Start**: Copy `.github-workflow-deploy-aks.yml` to `.github/workflows/deploy-aks.yml`

### Google GKE

- **Location**: `gke/`
- **Use Case**: Managed Kubernetes on GCP
- **Components**: K8s manifests (Deployment + Service + HPA), GCR/Artifact Registry integration
- **Quick Start**: Copy `.github-workflow-deploy-gke.yml` to `.github/workflows/deploy-gke.yml`

### Multi-Cloud Unified

- **Location**: `.github-workflow-deploy-multi-cloud.yml`
- **Use Case**: Single workflow to deploy to any supported cloud
- **Components**: Matrix-based deployment with conditional logic
- **Quick Start**: Copy to `.github/workflows/deploy-multi-cloud.yml` and customize matrix

## Prerequisites

### Docker Images

All templates assume you have a Dockerfile in your repository root. Update image names and build contexts as needed.

### Secrets Setup

#### ECS Secrets (GitHub Repository Secrets)

```bash
AWS_ACCESS_KEY_ID     = your-aws-access-key
AWS_SECRET_ACCESS_KEY = your-aws-secret-key
AWS_REGION           = us-east-1
ECR_REPOSITORY       = your-repo-name
```

#### AKS Secrets

```bash

AZURE_CREDENTIALS    = {"clientId": "...", "clientSecret": "...", "subscriptionId": "...", "tenantId": "..."}
ACR_REGISTRY         = yourregistry.azurecr.io
AKS_RESOURCE_GROUP   = your-resource-group
AKS_CLUSTER_NAME     = your-aks-cluster
```

#### GKE Secrets

```bash
GCP_SA_KEY          = your-service-account-json
GCP_PROJECT         = your-gcp-project-id
GKE_CLUSTER         = your-gke-cluster
GKE_ZONE            = us-central1-a
```

## Getting Started

1. **Choose your target cloud** (ECS, AKS, or GKE)
1. **Set up required secrets** in GitHub repository settings
1. **Copy the workflow template** to `.github/workflows/`
1. **Customize cluster names, registry URLs, and service names**
1. **Update manifests** with your application configuration
1. **Test with a manual workflow dispatch**

## Example Commands

```bash

# Test ECS deployment
gh workflow run deploy-ecs.yml

# Test AKS deployment
gh workflow run deploy-aks.yml

# Test GKE deployment
gh workflow run deploy-gke.yml
```

## Integration with Telemetry Plan

These templates are designed to work with the unified telemetry plan in `docs/observability/unified-telemetry-plan.md`. The manifests include basic resource requests/limits and HPA configurations for autoscaling.

For production deployments, consider:

- Adding health checks and readiness probes
- Configuring ingress controllers (ALB, NGINX, etc.)
- Setting up monitoring and logging integrations
- Adding secrets management (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager)

## Support

Each provider directory contains a `README.md` with provider-specific setup instructions and troubleshooting tips.
