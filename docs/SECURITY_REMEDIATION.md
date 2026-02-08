# Repo Secrets Remediation & Best Practices

This document contains recommended steps to remediate exposed secrets, purge secrets from git history, rotate keys, and set automation to prevent future leaks.

## Immediate Steps (High priority)

1. Identify committed secrets
   - We scanned for common patterns (sk-*, AIza*, AKIA*, `-----BEGIN PRIVATE KEY-----`, etc.). Replace any live keys in the repo with `REDACTED`.

2. Rotate keys
   - For every real key found in commit history, rotate (regenerate) the key with the provider immediately.
   - Revoke old keys where possible.

3. Purge git history
   - Use `git filter-repo` or `bfg` to remove secrets from commit history.
   - Example (with filter-repo installed):
     - git clone --mirror <repo-url>
     - cd repo.git
     - git filter-repo --path PATH/CONTAINING/SECRET --force
     - git push --force

   - NOTE: This rewrites git history and requires a coordinated force-push and coordination with all collaborators.

4. Remove root-level secrets and venvs

   - Delete committed `venv` directories and ensure they're listed in `.gitignore`.
   - Use `tools/clean_venv.sh` to find and untrack venvs.

## Preventative Controls (Medium priority)

1. Add CI scanners
   - Use `gitleaks` as a GitHub Actions step for PRs and pushes (we added `.github/workflows/ci/gitleaks.yml`).

2. Add pre-commit hooks
   - Use `pre-commit` with `gitleaks` and other linters to block local commits that contain secrets.

3. Use secret managers
   - Store secrets in cloud provider secret managers or sealed/external secrets for Kubernetes.

4. Add `*.env` and `venv` to the project `.gitignore` (done).

## Developer Hygiene

- Replace secrets in the repo with `REDACTED` and keep a local `.env` or `.env.local` that is gitignored.
- Migrating to CI/CD secret injection (GitHub Actions Sealed Secrets or `secrets` context) is recommended.
- Add documented steps for retrieving secrets for local dev: `tools/README_DEV_SECRETS.md`.

## Rotating Keys and Communication

- After rotating keys, update the affected deployments and external services (Supabase, Sentry, PostHog, Prisma, Pinecone, etc.).
- Communicate with team to update any local configs or CI secrets.

## Example: Remove and rotate an API Key

1. Rotate keys in provider portal.
2. Update CI secrets and secret manager with new value.
3. Remove old key from repo and commit with `REDACTED` placeholder.
4. Run `git filter-repo` to remove historical exposures.
5. Alert team to re-clone the repo and reconfigure local dev environments.

## Tools & Links

- <https://github.com/newren/git-filter-repo>
- <https://rtyley.github.io/bfg-repo-cleaner/>
- <https://github.com/zricethezav/gitleaks>
- <https://pre-commit.com>

## Notes

If you'd like, I can:

- Draft a `git filter-repo` script to purge certain paths.
- Create a GitHub Action to rotate keys as a follow-up automation (requires provider access).
- Add pre-commit hooks for local dev.

