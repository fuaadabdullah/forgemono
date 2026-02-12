# Data Flow Diagram

```mermaid
graph TD;
  User[User]
  Frontend[Frontend (Expo/React Native)]
  API[FastAPI Backend]
  DB[(Supabase/Postgres)]
  MarketData[Market Data Provider]
  Telemetry[Telemetry (Sentry/PostHog)]

  User --> Frontend
  Frontend --> API
  API --> DB
  API --> MarketData
  API --> Telemetry
```

**Description:**

- Users interact with the Frontend (mobile/web app).
- Frontend communicates with the FastAPI backend for all business logic and risk calculations.
- Backend reads/writes to Supabase/Postgres for persistent data.
- Backend fetches market data from external providers (server-side only).
- Telemetry events are sent to Sentry and PostHog for monitoring and analytics.
