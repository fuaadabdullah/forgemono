## Environment Variables & .env Usage

This repo follows a conservative policy: do not commit secrets as `.env` files. Keep only `.env.example` files in the repository and move live `.env` files to your secure vault (Bitwarden, 1Password, or equivalent). When in doubt, prefer `ENV` variables on CI/CD or managed secrets stores.

Guidelines:

- Keep `.env.example` in the repo — it documents required variables (no secrets).
- Move project-specific environment templates into docs (e.g. `apps/goblin-assistant/backend/docs/ENVIRONMENT_VARIABLES.md`).
- Avoid committing any `*.db`, `*.rdb`, or `.env` files.
- If a `.env` file was committed in the past, consider rotating the credential and running `bfg` or `git-filter-repo` to purge secrets from history.

Where to find env docs:

- `apps/goblin-assistant/backend/docs/ENVIRONMENT_VARIABLES.md` — backend-specific env variables and required steps.
- `goblin-infra/envs/` — environment templates for infra (CI, Terraform, cloud).

If you need help migrating `.env` content into your secret vault, ask a member of the Keepers guild and follow the `docs/migrations/VAULT_MIGRATION_COMPLETE.md` checklist.
