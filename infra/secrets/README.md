---title: SOPS Secrets Management
type: how-to
project: ForgeMonorepo
status: published
owner: GoblinOS
description: "README"

---

# SOPS Secrets Management

This directory contains encrypted secrets managed with [SOPS](https://github.com/getsops/sops) and [age](https://github.com/FiloSottile/age).

## Quick Start

### First-time Setup

1. **Install tools**:

```bash
# macOS
brew install sops age

# Linux
# Download from releases
# - https://github.com/getsops/sops/releases
# - https://github.com/FiloSottile/age/releases
```

1. **Generate age key** (one-time per developer):

```bash

age-keygen -o ~/.config/sops/age/keys.txt
```

1. **Share public key** with team lead:

```bash
# Print your public key
age-keygen -y ~/.config/sops/age/keys.txt
```

1. **Receive `.sops.yaml`** from team lead with your public key added.

### Encrypt a New Secret

```bash

# Create a new secret file
sops secrets/dev/litellm-secrets.enc.yaml

# SOPS will open your $EDITOR with
apiVersion: v1
kind: Secret
metadata:
  name: litellm-secrets
  namespace: overmind-dev
type: Opaque
stringData:
  openai-api-key: "YOUR_KEY_HERE"
  gemini-api-key: "YOUR_KEY_HERE"
  deepseek-api-key: "YOUR_KEY_HERE"

# Save and exit - file is automatically encrypted
```

### Decrypt & Edit

```bash
# Edit encrypted file
sops secrets/dev/litellm-secrets.enc.yaml

# View decrypted content
sops -d secrets/dev/litellm-secrets.enc.yaml

# Decrypt to stdout and apply to cluster
sops -d secrets/dev/litellm-secrets.enc.yaml | kubectl apply -f -
```

### Rotate Keys

```bash

# Add new recipient
sops updatekeys secrets/dev/litellm-secrets.enc.yaml

# Remove old recipient (edit .sops.yaml first)
sops updatekeys --rm-age <old-public-key> secrets/dev/litellm-secrets.enc.yaml
```

## Directory Structure

```
infra/secrets/
├── .sops.yaml                  # SOPS configuration
├── README.md                   # This file
├── Makefile                    # Helper commands
├── dev/
│   ├── litellm-secrets.enc.yaml
│   └── overmind-secrets.enc.yaml
├── staging/
│   └── *.enc.yaml
└── prod/
    └── *.enc.yaml
```

## SOPS Configuration

`.sops.yaml` defines encryption rules per environment:

```yaml
creation_rules:
  - path_regex: secrets/dev/.*
    age: >-
      age1public1...,
      age1public2...

  - path_regex: secrets/prod/.*
    age: >-
      age1public1...,
      age1public2...,
      age1public3...
```

## GitOps Integration

### With Argo CD

1. **Install SOPS plugin**:

```yaml

# argocd-cm ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
data:
  kustomize.buildOptions: "--enable-alpha-plugins --enable-helm"
```

1. **Create secret with age key**:

```bash
kubectl create secret generic sops-age \
  --from-file=key.txt=$HOME/.config/sops/age/keys.txt \
  -n argocd
```

1. **Use KSOPS kustomize plugin**:

```yaml

# kustomization.yaml
generators:

  - ./secrets/dev/litellm-secrets.enc.yaml
```

### With Flux

1. **Install SOPS controller**:

```bash
flux bootstrap github \
  --owner=your-org \
  --repository=your-repo \
  --path=clusters/production \
  --decryption-provider=sops \
  --decryption-secret=sops-age
```

1. **Create age secret**:

```bash

cat ~/.config/sops/age/keys.txt | 
kubectl create secret generic sops-age \
  --namespace=flux-system \
  --from-file=age.agekey=/dev/stdin
```

1. **Flux auto-decrypts** `*.enc.yaml` files.

## Security Best Practices

1. **Never commit unencrypted secrets** - `.gitignore` excludes `*.dec.yaml`
1. **Rotate age keys quarterly** - See rotation schedule in team calendar
1. **Use separate keys per environment** - Prod keys separate from dev
1. **Audit access regularly** - Review who has which keys
1. **Backup age keys** - Store securely (Bitwarden, 1Password, Vault, etc.)

## Makefile Commands

```bash
# Encrypt all files in a directory
make encrypt ENV=dev

# Decrypt all files in a directory (for local testing)
make decrypt ENV=dev

# Rotate keys for all files
make rotate ENV=dev

# Validate all encrypted files can be decrypted
make validate

# Apply secrets to cluster
make apply ENV=dev NAMESPACE=overmind-dev
```

## Troubleshooting

### "no age private key found"

```bash

# Ensure age key exists
ls -la ~/.config/sops/age/keys.txt

# If missing, generate new key
age-keygen -o ~/.config/sops/age/keys.txt

# Share public key with team
age-keygen -y ~/.config/sops/age/keys.txt
```

### "MAC mismatch"

File was modified without SOPS. Re-encrypt:

```bash
# Decrypt to temp file
sops -d secrets/dev/file.enc.yaml > temp.yaml

# Re-encrypt
sops -e temp.yaml > secrets/dev/file.enc.yaml

# Clean up
rm temp.yaml
```

### "failed to get the data key"

Your public key is not in `.sops.yaml`. Contact team lead to add you.

## References

- [SOPS Documentation](https://github.com/getsops/sops)
- [age Encryption](https://github.com/FiloSottile/age)
- [Argo CD SOPS Plugin](https://github.com/viaduct-ai/kustomize-sops)
- [Flux SOPS Guide](https://fluxcd.io/docs/guides/mozilla-sops/)

## Emergency Access

In case of lost keys, contact:

- **Team Lead**: @fuaadabdullah
- **Backup**: Check team Bitwarden (or 1Password) vault
- **Last Resort**: Regenerate secrets and re-encrypt

## Key Rotation Schedule

- **Dev/Staging**: Every 6 months
- **Production**: Every 90 days
- **Next rotation**: January 19, 2026
