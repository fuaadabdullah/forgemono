---
description: "CHECKLIST"
---

# ForgeTM Lite Quick Start Checklist

Use this checklist to track your progress through Week 1 setup.

## ✅ Documentation (DONE)

- [x] Product definition created (`PRODUCT_DEFINITION.md`)
- [x] README with developer guide created
- [x] GoblinOS integration configured
- [x] Copilot instructions updated
- [x] Development tools script created

## 📋 Week 1: Foundations & Contract

### Day 1-2: Project Scaffold

- [ ] **Initialize Expo Project**
  ```bash
  cd /Users/fuaadabdullah/ForgeMonorepo/apps/forge-lite
  npx create-expo-app@latest . --template blank-typescript
  ```

- [ ] **Set up TypeScript strict mode**
  - [ ] Update `tsconfig.json` with strict: true
  - [ ] Add ESLint configuration
  - [ ] Add Prettier configuration

- [ ] **Install Core Dependencies**
  ```bash
  pnpm add @react-navigation/native expo-router
  pnpm add zustand # or react-query for state
  pnpm add victory-native # for charts
  ```

- [ ] **Configure Expo Router**
  - [ ] Create `src/app/_layout.tsx`
  - [ ] Create `src/app/(tabs)/cockpit.tsx`
  - [ ] Create `src/app/(tabs)/plan.tsx`
  - [ ] Create `src/app/(tabs)/journal.tsx`

### Day 2-3: FastAPI Backend

- [ ] **Initialize FastAPI Project**
  ```bash
  mkdir -p api/routers api/services api/tests
  cd api
  python3 -m venv venv
  source venv/bin/activate
  ```

- [ ] **Install FastAPI Dependencies**
  ```bash
  pip install fastapi uvicorn pydantic python-dotenv
  pip install pytest httpx  # for testing
  pip freeze > requirements.txt
  ```

- [ ] **Create API Structure**
  - [ ] `api/main.py` - FastAPI entry point
  - [ ] `api/routers/risk.py` - Risk calculation endpoints
  - [ ] `api/services/risk_calc.py` - Risk math logic
  - [ ] `api/tests/test_risk.py` - Unit tests

- [ ] **Implement `/risk/calc` Endpoint**
  - [ ] Calculate position size from entry/stop/risk%
  - [ ] Calculate R-multiple
  - [ ] Calculate projected P&L
  - [ ] Add unit tests (100% coverage)

### Day 3-4: Supabase Setup

- [ ] **Create Supabase Project**
  - [ ] Go to [supabase.com](https://supabase.com)
  - [ ] Create new project
  - [ ] Note project URL and anon key

- [ ] **Design Database Schema**
  - [ ] `users` table (via Supabase Auth)
  - [ ] `trades` table (id, user_id, ticker, status, entry, stop, target, size, r_multiple, etc.)
  - [ ] `setups` table (id, user_id, name, description)
  - [ ] `watchlists` table (id, user_id, name)
  - [ ] `watchlist_items` table (id, watchlist_id, ticker)

- [ ] **Create Initial Migration**
  ```sql
  -- supabase/migrations/001_init.sql
  CREATE TABLE trades (...);
  CREATE TABLE setups (...);
  -- etc.
  ```

- [ ] **Set up Row Level Security**
  ```sql
  -- supabase/migrations/002_rls.sql
  ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "Users see own trades" ...
  ```

- [ ] **Configure Environment Variables**
  - [ ] Create `.env.local`
  - [ ] Add `SUPABASE_URL`
  - [ ] Add `SUPABASE_ANON_KEY`
  - [ ] Add to `.gitignore`

### Day 4-5: Development Tools

- [ ] **Configure EAS (Expo Application Services)**
  ```bash
  pnpm add -g eas-cli
  eas login
  eas build:configure
  ```

- [ ] **Set up Sentry**
  ```bash
  pnpm add @sentry/react-native
  # Configure in app/_layout.tsx
  ```

- [ ] **Set up PostHog**
  ```bash
  pnpm add posthog-react-native
  # Configure analytics tracking
  ```

- [ ] **Configure CI/CD**
  - [ ] Create `.github/workflows/test.yml`
  - [ ] Add TypeScript type checking
  - [ ] Add ESLint
  - [ ] Add FastAPI pytest

### Day 5-6: First Build & Deploy

- [ ] **Build "Hello World" App**
  - [ ] Login screen (Supabase auth)
  - [ ] Simple home screen
  - [ ] Tab navigation (3 tabs)
  - [ ] Basic styling (dark mode)

- [ ] **TestFlight Submission**
  ```bash
  eas build --platform ios
  eas submit --platform ios
  ```

- [ ] **Google Play Internal Track**
  ```bash
  eas build --platform android
  eas submit --platform android
  ```

- [ ] **Test App**
  - [ ] App opens without crash
  - [ ] User can log in
  - [ ] App runs for 5 minutes without crash
  - [ ] Basic navigation works

### Store Metadata Checklist

- [ ] App Name, Subtitle, Keywords, Category
- [ ] Description (concise, compliant with “no advice, no execution”)
- [ ] Screenshots (phones + tablets), App Preview (optional)
- [ ] App Icon and Splash images
- [ ] Privacy Policy URL: set `EXPO_PUBLIC_PRIVACY_URL` in `.env.local`
- [ ] Terms of Service URL: set `EXPO_PUBLIC_TERMS_URL` in `.env.local`
- [ ] Support Email: set `EXPO_PUBLIC_SUPPORT_EMAIL` in `.env.local`
- [ ] Age Rating questionnaire completed
- [ ] Contact info completed in App Store / Play Console
- [ ] iOS `bundleIdentifier` and Android `package` set in `app.json`

## ✅ Week 1 Success Gate

- [ ] App opens without crash for 5 minutes
- [ ] User can log in (Supabase auth)
- [ ] Shows a basic screen with tab navigation
- [ ] Available on TestFlight
- [ ] Available on Play Console Internal Track

## 📝 Notes & Blockers

### Questions to Resolve:
- [ ] Which state management? (Zustand vs React Query)
- [ ] Which chart library? (Victory Native vs react-native-svg-charts)
- [ ] Local database? (WatermelonDB vs SQLite)

### Potential Blockers:
- [ ] Supabase free tier limits
- [ ] Apple Developer Account ($99/yr)
- [ ] Google Play Developer Account ($25 one-time)

### Resources Needed:
- [ ] API keys for market data (Alpha Vantage, etc.)
- [ ] Design assets (app icon, splash screen)
- [ ] Privacy policy & terms of service

---

**Current Status**: Documentation complete, ready to scaffold
**Next Action**: Run `bash tools/forge_lite_env.sh setup`
**Estimated Time**: Week 1 requires ~20-30 hours of focused work
