---
description: "SETUP_SUMMARY"
---

# ForgeTM Lite Setup Summary

**Date**: November 6, 2025
**Status**: Project Initialized ✅

## What We Created

### 1. Core Documentation
- ✅ **`PRODUCT_DEFINITION.md`** - Complete product specification
  - Product definition & philosophy
  - Monetization strategy (Free/Pro/B2B)
  - Platform strategy (Expo recommended)
  - Backend architecture (Supabase + FastAPI)
  - 6-week roadmap with gates
  - Growth engine strategy
  - UX & engineering standards
  - Compliance requirements

- ✅ **`README.md`** - Project overview & developer guide
  - Quick start guide
  - Project structure
  - Architecture overview
  - Development workflows
  - Testing & quality standards

### 2. GoblinOS Integration
- ✅ **Updated `.github/copilot-instructions.md`**
  - ForgeTM Lite as primary focus
  - Tech stack documentation
  - Development guidelines
  - Compliance requirements
  - AI assistant workflows

- ✅ **Updated `GoblinOS/goblins.yaml`**
  - New **ForgeTM Lite Guild** with 5 goblins:
    - `mobilesmith` - Expo & React Native
    - `apismith` - FastAPI & risk math
    - `datasmith` - Supabase & data
    - `testsmith` - QA & compliance
    - `buildsmith` - DevOps & releases

  - New toolbelt with 5 commands:
    - `forge-lite-dev` - Expo dev server
    - `forge-lite-api-dev` - FastAPI backend
    - `forge-lite-test` - Run all tests
    - `forge-lite-lint` - Run linters
    - `forge-lite-build` - Production build

### 3. Development Tools
- ✅ **`tools/forge_lite_env.sh`** - Environment management script
  - `setup` - Initial project setup
  - `dev` - Start Expo dev server
  - `api` - Start FastAPI backend
  - `test` - Run all tests
  - `lint` - Run linters
  - `build` - Production build

## Project Structure

```
ForgeMonorepo/
├── .github/
│   └── copilot-instructions.md    # ✅ Updated with ForgeTM Lite focus
│
├── apps/
│   └── forge-lite/                # ✅ New project
│       ├── PRODUCT_DEFINITION.md  # ✅ Complete product spec
│       ├── README.md              # ✅ Developer guide
│       └── [awaiting scaffold]    # Next: Expo + FastAPI setup
│
├── GoblinOS/
│   └── goblins.yaml               # ✅ Updated with Forge Lite Guild
│
└── tools/
    └── forge_lite_env.sh          # ✅ New dev environment script
```

## Next Steps

### Week 1: Foundations & Contract (Current)

#### Immediate Actions:
1. **Scaffold Expo Project**
   ```bash
   cd /Users/fuaadabdullah/ForgeMonorepo/apps/forge-lite
   npx create-expo-app@latest . --template blank-typescript
   ```

2. **Set up FastAPI Backend**
   ```bash
   mkdir -p api/routers api/services api/tests
   # Create FastAPI structure
   ```

3. **Initialize Supabase**
   - Create Supabase project
   - Set up database schema
   - Configure Row Level Security
   - Create `.env.local` with credentials

4. **Configure Development Tools**
   - Set up EAS (Expo Application Services)
   - Configure Sentry for crash reporting
   - Configure PostHog for analytics
   - Add TypeScript strict mode

5. **First Deployment**
   - Ship "Hello World" to TestFlight
   - Ship "Hello World" to Play Console Internal Track

#### Success Gate:
✅ App opens, logs in, shows a dumb screen without crashing for 5 minutes

### Development Workflow

Using GoblinOS (recommended):
```bash
# From ForgeMonorepo root
cd /Users/fuaadabdullah/ForgeMonorepo

# Setup project
bash tools/forge_lite_env.sh setup

# Start dev server
bash tools/forge_lite_env.sh dev

# Start API (in separate terminal)
bash tools/forge_lite_env.sh api

# Run tests
bash tools/forge_lite_env.sh test
```

Direct commands:
```bash
cd apps/forge-lite

# Frontend
pnpm dev
pnpm test
pnpm lint

# Backend
cd api
uvicorn main:app --reload
pytest
```

## Key Decisions Made

### Platform: Expo (React Native)
- **Why**: Single codebase for iOS, Android, Web
- **Benefits**: Native performance, easier App Store compliance
- **Trade-offs**: Slight learning curve vs pure web

### Backend: FastAPI
- **Why**: Single source of truth for risk calculations
- **Benefits**: Fast, type-safe, auto-generated API docs
- **Trade-offs**: Separate deployment from Supabase

### Database: Supabase
- **Why**: Postgres + Row Level Security + Auth in one
- **Benefits**: Fast, cheap, scalable, built-in realtime
- **Trade-offs**: Vendor lock-in (but Postgres underneath)

### Monetization: Freemium
- **Free forever**: Core features (planning, journal, basic analytics)
- **Pro ($7/mo)**: Multi-accounts, cloud sync, images, team
- **B2B ($99/mo)**: Shared workspaces, aggregated stats

## Guardrails & Compliance

### Hard Rules:
- ❌ NO execution, NO signals
- ❌ NO financial advice
- ✅ Educational disclaimers everywhere
- ✅ Data export required (CSV)
- ✅ Privacy policy & terms required
- ✅ Sign in with Apple if offering social login

### Engineering Standards:
1. **Risk math ONLY in FastAPI** - Frontend displays only
2. **Type-safe API client** - Generated from OpenAPI
3. **Offline-first** - Local cache, sync later
4. **E2E smoke tests** - CI/CD gate
5. **Feature flags** - Kill-switch ready

## Resources

### Documentation:
- [`PRODUCT_DEFINITION.md`](./PRODUCT_DEFINITION.md) - Complete spec
- [`README.md`](./README.md) - Developer guide
- [`/.github/copilot-instructions.md`](../../.github/copilot-instructions.md) - AI guidelines

### Tools:
- [`tools/forge_lite_env.sh`](../../tools/forge_lite_env.sh) - Dev environment
- [`GoblinOS/goblins.yaml`](../../GoblinOS/goblins.yaml) - Automation config

### External:
- [Expo Docs](https://docs.expo.dev/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Supabase Docs](https://supabase.com/docs)

## Team & Ownership

### GoblinOS Guild: ForgeTM Lite
- **mobilesmith**: Expo app, offline-first, App Store compliance
- **apismith**: FastAPI, risk calculations, type-safe APIs
- **datasmith**: Supabase, RLS, migrations, data privacy
- **testsmith**: E2E tests, unit tests, QA, compliance checks
- **buildsmith**: EAS builds, releases, telemetry, feature flags

### Human Ownership:
- **Product**: Fuaad Abdullah
- **Development**: Fuaad Abdullah (with AI assistance)
- **Design**: TBD (using dark mode first principles)

## Success Metrics

### Week 1 Gate:
- App opens without crash for 5 minutes ✅
- User can log in ✅
- Basic screen displays ✅

### 6-Week Beta Goal:
- 100 weekly active users
- 20% D7 retention
- < 1% crash rate
- Median session > 3 minutes

### Long-term Vision:
- 10,000+ free users
- 1,000+ Pro subscribers (10% conversion)
- 50+ campus club licenses
- Self-sustaining SaaS business

---

**Status**: Ready to scaffold! 🚀
**Next**: Run `bash tools/forge_lite_env.sh setup` to begin
