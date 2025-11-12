---
description: "PRODUCT_DEFINITION"
---

# ForgeTM Lite — From free to formidable

## Product definition

A free, cross-platform trading cockpit for retail traders and students: watchlist + pre-trade planning + risk sizing + journaling + performance analytics.

**No broker execution. No paid wall for essentials. Discipline > dopamine.**

## Hard guardrails

- **No execution, no signals.** Education and analytics only. You're not a broker, therapist, or prophet.
- **Truth over vibes.** Everything measured in R first, dollars second.
- **Offline-first, sync later.** App works on the train; syncs when back online.

## Monetization without breaking "free"

Keep the core free forever. Monetize the edges:

### Free (forever):

- Unlimited planned trades
- Risk calc, journal, filters
- Equity curve, win rate, avg R
- 1 watchlist, local-only attachments

### Pro ($7/mo or $49/yr):

- Multi-accounts (paper vs live)
- CSV import/export + auto-backup
- Setup analytics by tag, time, session
- Cloud sync across devices
- Image uploads for chart screenshots
- Team journal (up to 3 seats)

### B2B / Campus club license ($99/mo):

- Shared workspace, role-based access
- Aggregated stats by member
- Custom onboarding template pack

### Long-tail:

- White-label for Discord communities
- Affiliates for trading education creators
- Paid template packs (journals, weekly reviews)

**You keep it free; you still get paid. Simple.**

## Platform strategy (pick once, execute)

You want web + iOS + Android. Two viable paths:

### Option A — Expo (React Native) everywhere ✅ Recommended

- One codebase: iOS, Android, Web (via RN Web)
- Native perf, real push notifications later
- Easier App Store compliance
- Charts: Victory Native or react-native-svg-charts

### Option B — Next.js PWA + Capacitor shell

- Fastest to ship web
- Wrap for iOS/Android with Capacitor
- Risk: Apple can be picky if it's just a webview; add at least one native feature (file picker, share sheet, haptics) to be safe

**My call:** Option A (Expo) for the flagship app, and a separate Next.js marketing site.

## Backend, data, and costs

### Auth & DB
- **Supabase** (Postgres + Row Level Security). It's fast, cheap, sane.

### API services
- Keep **FastAPI** for risk math and analytics endpoints
- Clean separation: Supabase for storage/auth, FastAPI for domain logic and scheduled crunching

### Market data
Don't die on "live ticks." Use delayed/quote endpoints with caching.

- **Free-ish tiers:** Alpha Vantage, Twelve Data, Finnhub (rate-limited)
- Put keys server-side. Never ship market-data keys in the app bundle

### Ops
- **Fly.io/Render** for FastAPI
- **Supabase** free/low tier to start
- **Cloudflare** in front

### Telemetry
- **Sentry** (crash)
- **PostHog** (product analytics, self-host later)

## Compliance & app store stuff you can't ignore

1. **Privacy Policy + Terms + Disclaimers** linked in-app and on site
   - "Educational only. Not investment advice. No execution."

2. **Data export required:** let users export their trades as CSV

3. **Sign in with Apple:** if you offer Google/Facebook login on iOS, Apple requires you also offer Sign in with Apple

4. **Age rating & review guidelines:** avoid anything that smells like financial advice or gambling
   - No get-rich-quick copy. Keep it "journal + analytics."

5. **Google Play Data Safety / Apple Privacy Nutrition Labels:** list what you collect (email, usage analytics, crash data), why, and how it's stored

## Product roadmap (6-week launch plan, brutal and real)

### Week 1 — Foundations & contract

- Write the 1-pager spec: problem, personas, non-goals, success metrics
- Repo scaffold (Expo + TypeScript), EAS set up, Sentry, PostHog
- Supabase project: users, trades, setups, watchlists
- FastAPI service: `/risk/calc`, `/metrics/*` with unit tests
- Ship a read-only "Hello, World" to TestFlight/Internal Track

**Gate:** App opens, logs in, shows a dumb screen without crashing for 5 minutes.

### Week 2 — Core flows (pre-trade to journal)

- Watchlist screen with basic quotes and search
- Risk Planner: entry/stop/target + %risk → size, R, projected PnL
- "Save as Planned" → create trade with status=PLANNED
- Offline mode: local cache for trades; sync job when online

**Gate:** Time to First Value < 3 minutes (new user can plan a trade).

### Week 3 — Journal + analytics v1

- Journal table with filters: date range, ticker, setup, side
- Stats: win rate, avg R, total R, streaks
- Charts: equity curve in R, R per trade
- CSV export

**Gate:** D1 retention > 35% in test cohort.

### Week 4 — Polish & onboarding

- Onboarding checklist: connect watchlist, define setups, log first trade, review weekly
- Empty states and error states that don't gaslight users
- Keyboard shortcuts (web), haptics (mobile), share sheet for exporting summary image

**Gate:** Median session length > 3 minutes, crash rate < 1%.

### Week 5 — Pro features + paywall skeleton

- Pro flag in Supabase; IAP scaffolding (no paywall messaging yet)
- Multi-accounts, attachments (images), weekly PDF review export
- Team workspace alpha (invite by email, 3 seats)

**Gate:** 5 pilot users using Team workspace weekly.

### Week 6 — Beta launch & GTM

- Landing page (Next.js): waitlist, features, screenshots, blog
- Publish TestFlight + Play Console closed tracks
- Beta cohort: uni trading clubs, Discord mods, YouTube educators
- Collect testimonials and bugs; lock v1.0

**Gate:** 100 weekly active users, 20% D7 retention in beta.

## Growth engine (no cringe)

### Templates as growth loops
- Public "setup packs," weekly review templates
- Shareable links import straight into the app

### Shareable performance images
- Equity curve card you can post
- Free ad every time someone flexes discipline

### Campus program
- Give club leaders free Pro and shared workspaces
- They onboard their members for you

### YouTube micro-content
- 90-second breakdowns: "Sizing trades with R," "Stop loss discipline," "Journal like a villain"

### SEO
Target queries like:
- "trade journal app"
- "position size calculator"
- "R multiple calculator"
- "trading journal template"

## UX that feels paid, even when it's free

- **Dark mode first**, high contrast, readable at 6 a.m. with caffeine shakes
- **Three tabs:** Cockpit, Plan, Journal. No kitchen sink navigation
- **One big CTA per screen.** Every screen ends in progress: "Plan trade," "Save note," "Export week"

## Non-negotiable engineering standards

1. **Single source of truth for risk math in FastAPI.** Frontend only displays
2. **Type-safe API client** (openapi-generator or tRPC-style wrapper)
3. **E2E smoke test on CI:** create user → plan trade → export CSV
4. **Feature flags for dangerous stuff.** Kill-switch ready

---

**Last Updated**: November 9, 2025
