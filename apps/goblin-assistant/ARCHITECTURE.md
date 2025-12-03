# Goblin Assistant Frontend Architecture

## ✅ High-Level Architecture

This frontend follows best practices for modern React applications with TypeScript.

### Core Technologies

- **React 18.2** + **TypeScript 5.0** - Type-safe component development
- **Vite 4.3** - Fast build tool and dev server
- **React Router v6** - Client-side routing
- **Tailwind CSS 3.3** - Utility-first styling
- **Lucide React** - Icon system

### State Management

#### 1. **Server State: TanStack Query (React Query) v5** ✅

- **Purpose**: API data fetching, caching, and synchronization
- **Features**:
  - Automatic caching with 5min stale time
  - Retry logic (3 attempts with exponential backoff)
  - Network resilience (refetch on reconnect)
  - Optimistic updates and cache invalidation
  - Request deduplication

**Configuration**: `src/lib/queryClient.ts`

**Query Keys**: Centralized in `queryKeys` object for consistent cache management

**Example Usage**:
```tsx
import { useChatModels } from './hooks/api/useChat';

function MyComponent() {
  const { data: models, isLoading, error } = useChatModels();
  // Automatic caching, retries, and error handling!
}
```

#### 2. **Client State: Zustand 5.0** ✅

- **Purpose**: Lightweight local state (auth, UI preferences)
- **Features**:
  - Minimal boilerplate
  - localStorage persistence for auth
  - No providers needed
  - TypeScript-first

**Auth Store**: `src/store/authStore.ts`

**Example Usage**:
```tsx
import { useAuthStore } from './store/authStore';

function MyComponent() {
  const { token, isAuthenticated, setAuth, clearAuth } = useAuthStore();
  // Reactive, persisted auth state!
}
```

### API Layer: Axios ✅

**Client**: `src/api/client-axios.ts`

**Features**:
- Typed requests and responses
- Request/response interceptors
- Automatic auth token injection
- Centralized error handling
- 30s timeout with retry logic
- 401 handling (auto logout)

**Example**:
```tsx
import { apiClient } from './api/client-axios';

// Clean, typed API calls
const models = await apiClient.getAvailableModels();
```

### Routing: React Router v6 ✅

**Configuration**: `src/App.tsx`

**Routes**:
- `/` - Home/Dashboard
- `/chat` - Chat interface
- `/search` - RAG Search
- `/settings` - Provider & model settings
- `/execute` - Task execution (feature flagged)
- `/orchestrate` - Multi-step workflows (feature flagged)
- `/dashboard` - Analytics (feature flagged)

### Feature Flags ✅

**Configuration**: `src/config/features.ts`

**Environment Variables** (`.env.example`):
```bash
VITE_FEATURE_RAG_ENABLED=true
VITE_FEATURE_MULTI_PROVIDER=true
VITE_FEATURE_PASSKEY_AUTH=true
VITE_FEATURE_GOOGLE_AUTH=true
VITE_FEATURE_ORCHESTRATION=false
VITE_FEATURE_SANDBOX=false
```

**Usage**:
```tsx
import { isFeatureEnabled } from './config/features';

if (isFeatureEnabled('ragEnabled')) {
  // Show RAG UI
}
```

### Typed API Hooks 📁 `src/hooks/api/`

All hooks use TanStack Query for optimal data fetching:

| Hook File | Purpose | Exports |
|-----------|---------|---------|
| `useAuth.ts` | Authentication | `useLogin`, `useRegister`, `useLogout`, `useGoogleAuth`, `usePasskeyAuth` |
| `useChat.ts` | Chat completions | `useChatModels`, `useRoutingInfo`, `useChatCompletion` |
| `useSearch.ts` | RAG search | `useCollections`, `useSearchDocuments`, `useCreateCollection`, `useIndexDocument` |
| `useSettings.ts` | Settings CRUD | `useProviderSettings`, `useModelConfigs`, `useGlobalSettings`, `useUpdateProvider` |

### Component Architecture

**Modular Structure**:
```
src/
├── api/
│   ├── client-axios.ts       # Axios-based API client
│   └── client.ts             # Legacy fetch client (deprecated)
├── components/
│   ├── Auth/
│   │   ├── LoginForm.tsx     # Login/register form
│   │   └── PasskeyPanel.tsx  # WebAuthn passkey UI
│   └── Navigation.tsx        # Main nav header
├── config/
│   └── features.ts           # Feature flag configuration
├── hooks/
│   └── api/                  # Typed API hooks (React Query)
│       ├── useAuth.ts
│       ├── useChat.ts
│       ├── useSearch.ts
│       └── useSettings.ts
├── lib/
│   └── queryClient.ts        # React Query configuration
├── pages/
│   ├── ChatPage.tsx          # Main chat interface
│   ├── SearchPage.tsx        # RAG document search
│   ├── SettingsPage.tsx      # Provider/model config
│   └── ...
├── store/
│   └── authStore.ts          # Zustand auth state
├── App.tsx                   # Root component + routing
└── main.tsx                  # Entry point
```

### Design System

**Tailwind CSS Configuration**: `tailwind.config.js`

**Theme**:
- Background: `bg-gray-50`
- Primary: `indigo-600` (brand color)
- Cards: `white` with `border-gray-200`
- Text: `gray-900` (headings), `gray-600` (body)

**Components**:
- Clean, centered layouts (`max-w-3xl`, `max-w-6xl`)
- Rounded corners (`rounded-lg`, `rounded-xl`)
- Subtle shadows (`shadow-sm`, `shadow-md`)
- Consistent spacing (`p-6`, `gap-6`)

### Best Practices ✅

1. **Type Safety**: All API responses typed with TypeScript
2. **Error Handling**: Centralized in axios interceptors
3. **Loading States**: Automatic with React Query (`isLoading`, `isFetching`)
4. **Optimistic Updates**: Cache invalidation after mutations
5. **Network Resilience**: Retry logic + reconnect handling
6. **Code Splitting**: Dynamic imports for routes (future)
7. **Feature Flags**: Easy toggle for experimental features
8. **Persistent Auth**: Zustand + localStorage

### Environment Variables

**Required**:
```bash
VITE_FASTAPI_URL=http://127.0.0.1:8001  # Backend API URL
```

**Optional** (see `.env.example` for full list):
- Feature flags (`VITE_FEATURE_*`)
- Provider API keys (status display only)
- Analytics config

### Frontend Production Security & Hardening

These are frontend-specific best practices to adopt before deploying to production.

- Token Storage: Avoid storing long-lived JWTs in `localStorage`. Prefer using HttpOnly, Secure cookies for session tokens to mitigate XSS token theft. If localStorage is used, ensure the app has strict CSP and input sanitization. Consider rotating tokens frequently.
- Streaming Authentication: EventSource (SSE) cannot send custom headers; do not place secrets in the query string. Use session cookies (HttpOnly) for EventSource authentication, or issue short-lived signed stream tokens which the backend validates. Ensure the stream token is single-use and rotated.
- Vite Env Vars: Any `VITE_` variables are injected into the client bundle and are public. Never include secrets (provider API keys, private keys) in `VITE_` variables—these should remain server-side.
- CSP & XSS: Set a strict Content Security Policy (CSP) header in production; avoid `dangerouslySetInnerHTML`. Sanitize model outputs before rendering if HTML rendering is necessary.
- Turnstile Bot Protection: Use Cloudflare Turnstile for bot protection on sensitive endpoints, and validate tokens server-side. Ensure invisible tokens are short-lived and verify server-side to prevent replay.
- Rate-limiting: Add client-side rate limiting for UX (debounce, disable inputs) and rely on server-side rate limits (Redis-backed) for actual enforcement.
- Error/Crash Reporting: Add Sentry (or equivalent) and correlate frontend errors with server traces (include correlation id header). Do not log PII or secrets.

### Streaming & Auth Pattern (recommended)

Use one of the following secure patterns for EventSource streaming:

1. Cookie-based (recommended): Store session token in HttpOnly, Secure Cookie. Server validates session on requests and EventSource. No tokens in query string.
2. Short-lived Token (if cookies impossible): Obtain a short-lived stream token from the server via POST; server responds with a one-time token that the client uses in the `EventSource` query param. Server accepts token once and expires it immediately.
3. WebSocket alternative: Use WebSocket with Authorization header via a WebSocket protocol that supports header-based auth.

### Accessibility & Privacy

- Ensure the app honors reduced motion and high-contrast preferences.
- Mask or truncate sensitive data in UI display for audit logs (PII / API keys are never displayed in UI), and ensure the UI does not expose secrets fetched from the server.


### Development

**Start Dev Server**:
```bash
cd apps/goblin-assistant
pnpm dev  # Runs on localhost:3000
```

**Build**:
```bash
pnpm build  # TypeScript + Vite production build
```

**Lint**:
```bash
pnpm lint  # ESLint checks
```

### Migration Guide

**Old → New API Usage**:

```tsx
// ❌ Old: Manual fetch, no caching
const [data, setData] = useState(null);
useEffect(() => {
  fetch('/api/models').then(r => r.json()).then(setData);
}, []);

// ✅ New: React Query with caching
const { data } = useChatModels();
```

**Old → New Auth**:

```tsx
// ❌ Old: localStorage directly
const token = localStorage.getItem('token');

// ✅ New: Zustand store
const { token, isAuthenticated } = useAuthStore();
```

### Next Steps

- [ ] Add OpenAPI/TypeScript codegen for API types
- [ ] Implement code splitting for routes
- [ ] Add error boundary components
- [ ] Set up Sentry for error tracking
- [ ] Add analytics integration
- [ ] Create reusable component library (shadcn/ui)

---

**Last Updated**: December 1, 2025
**Architecture Version**: 2.0 (TanStack Query + Zustand + Axios)
