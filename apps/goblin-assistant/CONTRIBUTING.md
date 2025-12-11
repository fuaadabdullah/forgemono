# Goblin Assistant — Contributing (App-level guidance)

This file adds app-level guidance that complements the root `docs/development/CONTRIBUTING.md`.

Key responsibilities and canonical doc locations

- Frontend docs (canonical): `apps/goblin-assistant/PRODUCTION_DEPLOYMENT.md` and `apps/goblin-assistant/docs/`.
- Backend docs (canonical): `apps/goblin-assistant/backend/docs/`.
- Infrastructure docs (canonical): `goblin-infra/projects/goblin-assistant/` and `apps/goblin-assistant/infra/` (symlink to canonical).

- CI/CD: The Goblin Assistant uses CircleCI for CI and automated deployments. CircleCI config is in the repo root `.circleci/config.yml` with app-level overrides in `apps/goblin-assistant/.circleci/config.yml`. Follow `.circleci/SETUP.md` and `apps/goblin-assistant/docs/PRODUCTION_PIPELINE.md` for onboarding and deployment details. Do not commit secrets—use Bitwarden + CircleCI contexts per `docs/SECRETS_HANDLING.md`.

- Database migrations & RLS: When changing the schema or adding tables, use the Supabase CLI to create new migrations (e.g. `supabase migration new my_change`) and commit the resulting SQL. Run the RLS audit helper before opening a PR:


    ```bash
    # from repo root
    chmod +x scripts/ops/supabase_rls_check.sh
    scripts/ops/supabase_rls_check.sh apps/goblin-assistant/supabase
    ```

    Ensure migrations include `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;` and create appropriate `CREATE POLICY` statements.

Before opening a PR that includes documentation:

1. Check whether the change belongs under frontend/backend/infra. Use the canonical location above.
2. If you update a doc that affects more than one area, add a note and link to the cross-affected component's canonical doc.
3. Replace duplicates with links to the canonical file where applicable (e.g., backend docs shouldn't include step-by-step frontend setup—link to `apps/goblin-assistant/PRODUCTION_DEPLOYMENT.md`).
4. If you add new docs, add a short entry to the `docs/development/CONTRIBUTING.md` checklist (optional), or open a PR note calling out the canonical location.

Why this matters

- It prevents fragmentation and ensures a single source of truth for configuration and deployment instructions.
- It avoids stale or inconsistent instructions across backend, frontend, and infra artifacts.

Questions? Tag the repo owners listed in `CODEOWNERS` and add a short note describing why the doc belongs in the chosen area.
