# Secrets & Encryption Key Handling

This document explains how this repository stores encrypted secrets and how to handle secret decryption keys safely.

Summary (short):

- Encrypted files: `GoblinOS/secrets.enc.yaml`, `GoblinOS/.env.enc` — these are SOPS/age-encrypted and safe to commit.
- Never commit private decryption keys (age private keys, PGP private keys, or SOPS unencrypted files).
- If a private key was accidentally committed (for example `infra/charts/age-key.txt`), remove it and rotate/revoke the key immediately.

Key rules

- Only commit encrypted secrets (SOPS, age-encrypted blobs). Commit the public recipients (age public keys) or sops metadata — do NOT commit private keys.
- Store the decryption private keys in a secure vault (Bitwarden, 1Password, HashiCorp Vault, AWS Secrets Manager, or similar) and only grant access to required persons.
- Use a machine-level keyring (OS protected store) or the vault to mount the key at runtime; do not store in plaintext in the repo.

## HashiCorp Vault

We recommend storing secrets in HashiCorp Vault for both dev and production. See `docs/vault_integration.md` for detailed integration and rotation steps.

Typical pattern:

- Store provider keys under `secret/goblin-assistant/providers/<provider>`.
- Create a `secret/goblin-assistant/backups/<provider>` path to persist rotated keys temporarily, if needed.
- Use a `VaultClient` wrapper (included in repo at `vault_client.py`) to read secrets into the app's environment.


Quick verification

1. Search the repo for likely private key markers:

```bash
# from repo root
git grep -n "AGE-SECRET-KEY-\|-----BEGIN PRIVATE KEY\|-----BEGIN PGP PRIVATE KEY" || true
```

2. If you find a private key file (e.g. `infra/charts/age-key.txt`), **do not** re-commit it. Instead:

- Remove the file from the working tree and index

```bash

git rm --cached --quiet path/to/file
rm path/to/file
git commit -m "chore(secrets): remove committed private key file"
```

- Rotate/revoke the key immediately (follow the provider's docs). Assume the key is compromised until rotation is complete.

Purging history (if secret was committed previously)

- The repository history will still contain the secret; follow these steps to purge it from history and force-push.

Using git filter-repo (recommended):

1) Install: <https://github.com/newren/git-filter-repo>

2) Example to remove a path (run on a clean clone; backup first):

```bash
# clone a fresh copy
git clone --mirror git@github.com:your_org/your_repo.git repo.git
cd repo.git

# remove the sensitive file path(s)
git filter-repo --invert-paths --paths "infra/charts/age-key.txt" --paths "**/.goblin-memory.db" --refs --tag-rename 'refs/tags/*:refs/tags/*'

# push the rewritten repo
git remote add origin git@github.com:your_org/your_repo.git
git push --force --all
git push --force --tags
```

Using BFG (simpler for file removal):

```bash

# create a mirror clone
git clone --mirror git@github.com:your_org/your_repo.git
cd your_repo.git

# run BFG to delete the file path
bfg --delete-files 'age-key.txt'

# or delete by file pattern
bfg --delete-files '*.db'

# follow BFG instructions (gc, push)
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force
```

Important notes on history purge

- Purging history is destructive and requires force-pushing. Coordinate with your team and mirror any branches you need. After a purge, all collaborators must reclone or reset their clones.

Post-incident actions

- Rotate credentials or API keys that may have been exposed.
- Audit CI/CD secrets and environment variables — rotate where needed.
- Add scanning (git-secrets, gitleaks) to CI to prevent re-commits.

Recommendations

- Add automation to scan commits for secrets (pre-commit, CI). Recommended projects: `git-secrets`, `gitleaks`.
- Keep SOPS metadata (encrypted blobs) in repo; keep SOPS decryption keys in a vault and use automation to provide them to authorized CI runners only.

If you need, I can prepare a small script/PR to run gitleaks across the history and a template for rotating keys.

---
Last updated: 2025-11-13
