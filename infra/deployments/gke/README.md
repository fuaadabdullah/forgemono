# GKE Deployment Template

What this template provides:

- `manifests/deployment.yaml` and `manifests/service.yaml` - Kubernetes manifests for your app.
- `.github-workflow-deploy-gke.yml` - GitHub Actions workflow to build the Docker image, push to Google Container Registry (GCR) or Artifact Registry, authenticate to GKE and apply the manifests.

Required secrets (GitHub repository secrets):

- `GCP_SA_KEY` - JSON key for a GCP service account with `roles/container.admin` and `roles/storage.admin` (or narrower permissions to push to registry and manage GKE).
- `GKE_CLUSTER` - GKE cluster name
- `GKE_ZONE` / `GKE_REGION` - cluster location
- `GCP_PROJECT` - project id

Usage notes:

1. Create a service account with the required roles and store the JSON key as `GCP_SA_KEY`.
1. Create Artifact Registry or enable GCR, and update image name accordingly.
1. Copy the workflow to `.github/workflows/deploy-gke.yml` and customize.
