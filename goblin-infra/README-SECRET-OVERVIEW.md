# Goblin Infra — Secrets & Bootstrap Overview

This file summarizes how Goblin infra handles environment shape and secrets.

- Infra is the source-of-truth for environment shape (.env.example, terraform var templates, cloud-init templates).
- CI (CircleCI) is responsible for writing secrets to a secret manager (Vault/Doppler) during deploy.
- VMs use cloud-init and a bootstrap script to fetch ephemeral secrets and write them to `/etc/goblin/env` (root-owned, mode 600).

Quick checklist:
- [ ] Pick a secret manager (Vault or Doppler)
- [ ] Add CircleCI steps to write secrets to the secret manager
- [ ] Add Terraform outputs for instance bootstrap tokens
- [ ] Wire cloud-init to call the CI bootstrap endpoint or Vault agent
- [ ] Ensure runtime reads env from process env or mounted files

