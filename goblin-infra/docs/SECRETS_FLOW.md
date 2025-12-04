# Secrets flow and environment rules of engagement

This document describes the recommended approach for managing environment variables and secrets for Goblin Assistant deployments.

## Principles
- The infra repo (`goblin-infra`) is the source of truth for environment shape (templates, cloud-init, terraform variable definitions). It must NOT contain secrets.
- Secrets live in a dedicated secret manager (HashiCorp Vault, Doppler, or CircleCI contexts). CI injects secrets at deploy-time.
- VMs are bootstrapped via cloud-init; a small bootstrap script fetches ephemeral secrets from the CI bootstrap endpoint or Vault agent and writes them to a secure, root-owned file, e.g. `/etc/goblin/env`.
- Runtime processes read env from process env or mounted files. For containers, use Docker/K8s secrets or mounted files with restricted permissions.

## Recommended flow (VM style)
1. Terraform provisions VMs and outputs IPs and a bootstrap token.
2. CI builds images and writes secrets to Vault/Doppler or exposes a one-time token for the VM.
3. Cloud-init calls the CI bootstrap endpoint to retrieve secrets using the instance token.
4. Bootstrap script writes secrets to `/etc/goblin/env` and starts the container compose.

## Quick templates
- `goblin-infra/envs/.env.example` — env shape
- `goblin-infra/bootstrap/cloud-init.sh.tpl` — cloud-init snippet to call CI bootstrap
- `goblin-infra/bootstrap/bootstrap_secrets.sh` — example bootstrap script

## CI integration notes
- Use CircleCI contexts or Vault credentials in CircleCI to avoid leaking secrets.
- At build/deploy time the CI should write secrets to Vault or call an infra API to provision a one-time token for the VM.
- The VM fetches secrets over HTTPS and validates the token.

## Rotation & revocation
- Have a rotation plan: rotate long-lived credentials in secret manager and redeploy.
- Revoke tokens on VM destroy.

## Security checklist
- No secrets stored in git
- /etc/goblin/env is root-owned and mode 600
- CI uses least privilege to write secrets
- Vault or similar agent used in production

