# Removed/Archived Sensitive Files

The following files were removed from git tracking and moved into `.archive/removed-secrets/` on the working tree (ignored by .gitignore). Please transfer these files securely to your vault (e.g., Bitwarden / 1Password), then remove them from the archive.

- apps/goblin-assistant/.env
- apps/goblin-assistant/.env.development
- apps/goblin-assistant/backend/.env
- apps/goblin-assistant/backend/.env.backup
- apps/goblin-assistant/infra/kong/.env
- goblin-assistant-legacy-backup-20251209/.env.production
- apps/goblin-assistant/dump.rdb
- apps/goblin-assistant/lighthouse-report.report.json
- apps/goblin-assistant/lighthouse-report.report.html
- GoblinOS/.goblin-memory.db
- GoblinOS/forgetm.db
- GoblinOS/packages/**/.goblin-memory.db

**Next steps:**

- Move those files from `.archive/removed-secrets/` to a secure location (Vault) and delete them.
- If these files contained secrets that were committed previously, consider performing a BFG or git-filter-repo history purge to remove credentials from the history (not implemented here).

