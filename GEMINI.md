# Project Context: GoblinOS Assistant (ForgeMonorepo)

## Overview
This repository is a monorepo containing the **GoblinOS Assistant** application and its infrastructure. It utilizes a hybrid CI/CD approach, with GitHub Actions configured as robust alternatives/fallbacks to CircleCI.

## Repository Structure

### 1. Application (`apps/goblin-assistant/`)
*   **Role**: Backend Application source code.
*   **Language**: Python.
*   **Containerization**: Docker (built from this directory).
*   **Quality Gates**:
    *   Linting: `ruff`
    *   Testing: `pytest`

### 2. Infrastructure (`goblin-infra/`)
*   **Role**: Infrastructure as Code (IaC).
*   **Tooling**: Terraform.
*   **State Management**: Terraform Cloud.
*   **Environments (Workspaces)**:
    *   `GoblinOSAssistant` (Dev)
    *   `GoblinOSAssistant-staging` (Staging)
    *   `GoblinOSAssistant-prod` (Prod)
*   **Security**: Scanned via `tfsec` and `Checkov`.

### 3. CI/CD (`.github/workflows/`)
*   **Registry**: GitHub Container Registry (GHCR).
*   **Key Workflows**:
    *   `backend-ci.yml`: Runs Python linting and unit tests.
    *   `docker-ci.yml`: Builds Docker images and pushes to GHCR with provenance.
    *   `terraform-security.yml`: Runs security scans on Terraform code.
    *   `terraform-deploy.yml`: Manually triggered workflow to Plan/Apply Terraform changes.

## Development Guidelines

### Backend Development
*   Ensure all Python code adheres to `ruff` standards.
*   New features should include unit tests runnable via `pytest`.
*   Pushes to `main` affecting this directory automatically trigger CI and Docker builds.

### Infrastructure Management
*   **Warning**: The `terraform-deploy` workflow can modify live infrastructure.
*   Always run a `Plan` action before an `Apply` action in the manual workflow.
*   Ensure `TF_TOKEN` is configured in repository secrets for Terraform Cloud access.

### Secrets & Configuration
*   **Required Secrets**: `TF_TOKEN` (Terraform Cloud), `GITHUB_TOKEN` (Automatic).
*   **Optional Secrets**: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` (if switching from GHCR).

## Migration Notes
*   This project is set up to transition from CircleCI to GitHub Actions.
*   Both systems may run simultaneously; check `.github/workflows/README.md` for feature parity comparisons.
