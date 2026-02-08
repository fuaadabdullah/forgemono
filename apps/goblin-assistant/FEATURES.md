# Features Map

This file maps **routes** to **screens** and **feature modules** so routing stays predictable.

## Canonical Routing
- Source of truth: `src/pages/*` (Next.js pages router)
- Pages are thin wrappers that render a screen from `src/screens/*`
- Screens orchestrate; features own UI + hooks + api wrappers

## Public Routes
- `/` -> `src/pages/index.tsx` -> `src/screens/HomePage.tsx` -> `src/features/onboarding/HomeScreen.tsx`
- `/startup` -> `src/pages/startup.tsx` -> `src/screens/StartupScreen.tsx` -> `src/features/startup/*`
- `/help` -> `src/pages/help.tsx` -> `src/screens/HelpPage.tsx` -> `src/features/help/*`
- `/login` -> `src/pages/login.tsx` -> `src/screens/LoginPage.tsx`
- `/register` -> `src/pages/register.tsx` -> `src/screens/LoginPage.tsx` (register mode)
- `/google-callback` -> `src/pages/google-callback.tsx` -> `src/screens/GoogleCallback.tsx`

## Auth Routes
- `/chat` -> `src/pages/chat.tsx` -> `src/screens/ChatPage.tsx` -> `src/features/chat/*`
- `/search` -> `src/pages/search.tsx` -> `src/screens/SearchPage.tsx` -> `src/features/search/*`
- `/account` -> `src/pages/account.tsx` -> `src/screens/AccountPage.tsx` -> `src/features/account/*`
- `/sandbox` -> `src/pages/sandbox.tsx` -> `src/screens/SandboxPage.tsx` -> `src/features/sandbox/*`
- Guest sandbox is allowed with `?guest=1` (no persistence guarantees)

## Admin Routes (Internal Only)
- `/admin` -> `src/pages/admin/index.tsx` -> dynamic `src/components/EnhancedDashboard.tsx`
- `/admin/providers` -> `src/pages/admin/providers.tsx` -> `src/screens/EnhancedProvidersPage.tsx`
- `/admin/logs` -> `src/pages/admin/logs.tsx` -> `src/screens/LogsPage.tsx`
- `/admin/settings` -> `src/pages/admin/settings.tsx` -> `src/screens/SettingsPage.tsx`

## Feature Boundary Rules
- Features must not import other features directly.
- Allowed shared features: `src/features/shared/*`, `src/features/contracts/*`.
- Cross-feature types/logic should live in `src/domain/*`, `src/lib/*`, or `src/services/*`.
- `src/services/provider-router.ts` must not contain frontend route paths or navigation logic.

## Enforcements
- `npm run check:routes`
- `npm run check:features`
- `npm run check:appledouble`

