# Routing Constitution

Routing is a sacred layer. One owner. One law.

## Source of Truth
- **Next.js `src/pages`** is the only routing system for this app.
- Route components live in `src/screens/` and are **only** referenced by route files.
- Do not add routes anywhere else.
- `src/App.tsx` is a legacy SPA shell and must not be deployed.

## Public (Customer) Routes
- `/` — Home (recent convo, suggestions, quick actions)
- `/startup` — Boot/diagnostics (startup flow + redirect)
- `/chat` — Conversations + focused chat
- `/search` — Global search (docs, messages, tasks)
- `/sandbox` — Safe experiments & automation
- `/account` — Profile, billing, preferences
- `/help` — Help center & support chat
- `/login` — Login
- `/register` — Register
- `/google-callback` — OAuth callback
- `/404` — Not found
- `/onboarding` — Legacy alias (redirects to `/`)

## Admin Routes (Internal Only)
All admin pages live under `/admin/*`.
- `/admin` — Admin dashboard
- `/admin/logs` — System logs
- `/admin/providers` — Provider management
- `/admin/settings` — Admin settings

## Middleware Guards
- `/admin/*` requires admin.
- `/chat`, `/search`, and `/account` require auth.
- `/sandbox` requires auth unless `?guest=1`.
- `/login` and `/register` require guest.

## Rules
1. **Lowercase only**. No camel case or TitleCase routes.
2. **No duplicate routes**. One route = one file.
3. **No aliases** unless explicitly documented with a redirect.
4. **Admin isolation**: internal tools live under `/admin/*` only.
5. **Legacy routes** must 404 or redirect. Never silently work.

## Enforcements
- Run `scripts/check-routes.ts` to verify no extra route files exist.
- Any new route must update this file.
