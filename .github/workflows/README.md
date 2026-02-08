# GitHub Actions CI/CD Workflows

This directory contains GitHub Actions workflows that serve as fallbacks/alternatives to CircleCI for CI/CD operations.

## Available Workflows

### 1. Backend CI (`backend-ci.yml`)

- **Triggers**: Push/PR to `main` branch affecting backend code
- **What it does**:
  - Lints Python code with ruff
  - Runs unit tests with pytest
  - Uploads test results as artifacts

### 2. Docker CI (`docker-ci.yml`)

- **Triggers**: Push/PR to `main` branch affecting app code or Dockerfile
- **What it does**:
  - Builds Docker image from `apps/goblin-assistant/`
  - Pushes to GitHub Container Registry (GHCR)
  - Generates build provenance attestations

### 3. Terraform Security (`terraform-security.yml`)

- **Triggers**: Push/PR to `main` affecting Terraform code, or daily at 3 AM UTC
- **What it does**:
  - Runs tfsec for Terraform security scanning
  - Runs Checkov for infrastructure as code security
  - Uploads SARIF results to GitHub Security tab

### 4. Terraform Deploy (`terraform-deploy.yml`)

- **Triggers**: Manual workflow dispatch only
- **What it does**:
  - Plans and optionally applies Terraform changes
  - Supports dev/staging/prod environments
  - Uses Terraform Cloud for state management

### 5. Manual CI/CD Pipeline (now part of `backend-ci.yml`)

- **Triggers**: Manual workflow dispatch only (via `workflow_dispatch` inputs to `backend-ci.yml`)

- **What it does**:
  - Allows selective running of CI components for the backend (lint/tests, Docker build, and Terraform security)
  - Useful for testing or one-off deployments

## Required GitHub Secrets

Set these in your repository settings under **Settings → Secrets and variables → Actions**:

### Required Secrets

| Secret | Description | Where to get it |
|--------|-------------|-----------------|
| `TF_TOKEN` | Terraform Cloud API token | [app.terraform.io/app/settings/tokens](https://app.terraform.io/app/settings/tokens) |
| `GITHUB_TOKEN` | Auto-provided by GitHub | (Automatic - no setup needed) |

### Optional Secrets

| Secret | Description | When needed |
|--------|-------------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub username | If using Docker Hub instead of GHCR |
| `DOCKERHUB_TOKEN` | Docker Hub access token | If using Docker Hub instead of GHCR |

## Setup Instructions

### 1. Configure Repository Secrets

1. Go to **Settings → Secrets and variables → Actions**
2. Add the required secrets listed above

### 2. Configure Terraform Cloud (if using Terraform workflows)

1. Ensure your Terraform Cloud organization has these workspaces:
   - `GoblinOSAssistant` (dev)
   - `GoblinOSAssistant-staging` (staging)
   - `GoblinOSAssistant-prod` (prod)

2. The `TF_TOKEN` secret should have access to these workspaces

### 3. Enable Required Permissions

For Docker workflows, ensure the repository has:

- **Settings → Actions → General → Workflow permissions**: Read and write permissions

## Usage

### Automatic Triggers

Most workflows run automatically on:

- Pushes to `main` branch
- Pull requests to `main` branch
- Scheduled runs (security scans)

### Manual Triggers

Use **Actions** tab in GitHub to manually trigger workflows:

1. Go to **Actions** tab
2. Select the workflow you want to run
3. Click **Run workflow**
4. Fill in any required inputs
5. Click **Run workflow**

### Terraform Deployments

For Terraform deployments:

1. Go to **Actions → Terraform Deploy**
2. Click **Run workflow**
3. Select environment (dev/staging/prod)
4. Select action (plan/apply)
5. Run the workflow

**⚠️ Warning**: Apply actions will modify infrastructure. Use carefully!

## Differences from CircleCI

| Feature | CircleCI | GitHub Actions |
|---------|----------|----------------|
| Docker Registry | GHCR | GHCR |
| Terraform State | Terraform Cloud | Terraform Cloud |
| Security Scanning | tfsec + Checkov | tfsec + Checkov |
| Manual Approvals | Yes (staging/prod) | Manual trigger only |
| Cost | Credits-based | Minutes-based |
| Setup | Contexts required | Repository secrets |

## Troubleshooting

### Workflow doesn't run

- Check that triggers match (branch names, file paths)
- Verify required secrets are set
- Check repository permissions

### Docker build fails

- Ensure GHCR permissions are correct
- Check that `GITHUB_TOKEN` has package write access

### Terraform fails

- Verify `TF_TOKEN` is valid and has workspace access
- Check Terraform Cloud workspace names match

### Security scans fail

- Ensure Terraform files are in `goblin-infra/` directory
- Check that workflows have read access to repository contents

## Migration from CircleCI

If you want to switch from CircleCI to GitHub Actions:

1. Set up the required GitHub secrets
2. Test workflows individually using manual triggers
3. Update any documentation references
4. Disable CircleCI webhooks if desired

Both systems can run simultaneously as fallbacks for each other.
