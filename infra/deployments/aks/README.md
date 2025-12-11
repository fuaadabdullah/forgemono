# AKS Deployment Template

What this template provides:

- `manifests/deployment.yaml` and `manifests/service.yaml` - Kubernetes manifests for your application.
- `.github-workflows-deploy-aks.yml` - GitHub Actions workflow to build the image, push to Azure Container Registry (ACR), and apply the manifests to AKS.

Required secrets (GitHub repository secrets):

- `AZURE_CREDENTIALS` - JSON for a service principal with access to the resource group and AKS (use `az ad sp create-for-rbac --sdk-auth`).
- `ACR_REGISTRY` - registry name (e.g., `myregistry.azurecr.io`)

Usage notes:

1. Create an ACR and AKS cluster and ensure the service principal has permissions.
1. Update the `image` field in `manifests/deployment.yaml` to `${{ env.IMAGE }}` or use the workflow to replace it.
1. Copy the workflow into `.github/workflows/deploy-aks.yml` and customize resource names.
