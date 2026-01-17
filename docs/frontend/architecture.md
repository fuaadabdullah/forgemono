# Frontend Architecture

This document describes the architecture and design decisions for the GoblinOS Assistant frontend application.

## 🏗️ System Overview

The frontend is built with **Next.js 15** using the App Router, **TypeScript**, and **React 18**. It follows a modular architecture with clear separation of concerns between UI components, business logic, and data management.

### Technology Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.7+
- **Styling**: Tailwind CSS 3.4+
- **State Management**: Zustand 5.0+, React Query 5.0+
- **UI Components**: Custom component library with Radix UI primitives
- **Testing**: Jest, React Testing Library, Playwright
- **Build Tool**: Vite 6.0+
- **Linting**: ESLint 9.0+
- **Formatting**: Prettier 3.0+

### Architecture Diagram

```
┌─────────────────────────────────────────┐
│              Next.js App Router         │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────────┐  │
│  │   Pages     │  │   API Routes     │  │
│  │   (App)     │  │   (Middleware)   │  │
│  └─────────────┘  └──────────────────┘  │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────────┐  │
│  │   Components│  │   Hooks          │  │
│  │   (UI)      │  │   (Custom)       │  │
│  └─────────────┘  └──────────────────┘  │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────────┐  │
│  │   Services  │  │   Stores         │  │
│  │   (API)     │  │   (Zustand)      │  │
│  └─────────────┘  └──────────────────┘  │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐  │
│  │   Backend API (FastAPI)             │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 📦 Project Structure

```
apps/goblin-assistant/
├── app/                    # Next.js App Router pages
│   ├── api/               # API routes
│   ├── chat/              # Chat interface
│   ├── providers/         # Provider management
│   └── enhanced-providers/ # Enhanced provider UI
├── components/            # Reusable UI components
│   ├── ui/               # Base UI components
│   ├── layout/           # Layout components
│   └── dashboard/        # Dashboard components
├── lib/                  # Library code
│   ├── api/             # API clients and services
│   ├── hooks/           # Custom React hooks
│   └── utils/           # Utility functions
├── stores/              # Zustand stores
├── services/            # Business logic services
├── types/               # TypeScript type definitions
├── tests/               # Test files
└── docs/                # Documentation
```

## 🎨 Design System

### Component Architecture

The frontend follows a layered component architecture:

1. **Base Components** (`components/ui/`)
   - Atomic design principles
   - Reusable across the application
   - Built with Radix UI for accessibility

2. **Composite Components** (`components/`)
   - Combine base components
   - Feature-specific functionality
   - Higher-level abstractions

3. **Page Components** (`app/`)
   - Route-specific components
   - Orchestrate other components
   - Handle page-level logic

### State Management Strategy

We use a hybrid approach for state management:

#### Client State (Zustand)
- UI state (theme, modals, loading states)
- User preferences
- Authentication status
- Form state

```typescript
// Example Zustand store
interface UIState {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  setTheme: (theme: 'light' | 'dark') => void;
}

const useUIStore = create<UIState>((set) => ({
  theme: 'light',
  sidebarOpen: false,
  setTheme: (theme) => set({ theme }),
}));
```

#### Server State (React Query)
- API data
- Caching and synchronization
- Background updates
- Optimistic updates

```typescript
// Example React Query usage
const { data, isLoading, error } = useQuery({
  queryKey: ['providers'],
  queryFn: () => apiClient.getProviders(),
});
```

## 🔄 Data Flow

### Request Flow

1. **User Interaction** → Component Event
2. **Component** → Hook/Store Update
3. **Hook** → API Service Call
4. **Service** → Backend API Request
5. **Backend** → Process Request
6. **Response** → Update State
7. **State Update** → Re-render Components

### State Synchronization

- **Optimistic Updates**: Immediate UI feedback
- **Background Sync**: Keep data fresh
- **Error Handling**: Graceful fallbacks
- **Loading States**: Clear user feedback

## 🌐 API Integration

### Service Layer

API interactions are abstracted through a service layer:

```typescript
// API Client
class APIClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({ baseURL });
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get(url, config);
    return response.data;
  }
}

// Service
class ProviderService {
  constructor(private apiClient: APIClient) {}

  async getProviders(): Promise<Provider[]> {
    return this.apiClient.get('/providers');
  }
}
```

### Error Handling

- **Global Error Boundaries**: Catch React errors
- **API Error Handling**: Consistent error responses
- **User Feedback**: Clear error messages
- **Logging**: Structured error logging

## 🎯 Performance Optimization

### Rendering Optimization

- **Memoization**: `useMemo` and `useCallback` for expensive calculations
- **Virtualization**: For long lists and dynamic content
- **Lazy Loading**: Code splitting with `dynamic()`
- **Image Optimization**: Next.js Image component

### Bundle Optimization

- **Tree Shaking**: Remove unused code
- **Code Splitting**: Route-based splitting
- **Dependency Optimization**: Analyze bundle size
- **Caching Strategy**: Leverage browser caching

### Caching Strategy

- **React Query**: Server state caching
- **Service Worker**: Asset caching
- **CDN**: Static asset delivery
- **Browser Cache**: Leverage HTTP caching

## 🔒 Security Considerations

### Client-Side Security

- **CSP Headers**: Content Security Policy
- **Input Validation**: Sanitize user inputs
- **XSS Protection**: Escape dynamic content
- **CSRF Protection**: CSRF tokens for state changes

### Authentication & Authorization

- **JWT Tokens**: Secure token storage
- **Session Management**: Proper session handling
- **Role-Based Access**: UI-level permission checks
- **Secure API Calls**: Include auth headers

## 🧪 Testing Strategy

### Testing Pyramid

1. **Unit Tests** (Jest + RTL)
   - Individual components
   - Utility functions
   - Custom hooks

2. **Integration Tests**
   - API service integration
   - State management
   - Component interactions

3. **E2E Tests** (Playwright)
   - User workflows
   - Cross-browser testing
   - Performance testing

### Test Coverage

- **Minimum 80%** code coverage required
- **Critical paths** must be fully tested
- **Accessibility tests** for all components
- **Performance benchmarks** for key operations

## 📱 Responsive Design

### Mobile-First Approach

- **Breakpoints**: Tailwind CSS responsive classes
- **Touch Targets**: Minimum 44px touch targets
- **Gesture Support**: Swipe, pinch, scroll
- **Performance**: Optimize for mobile networks

### Accessibility (A11y)

- **WCAG 2.1 AA** compliance
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: ARIA labels and roles
- **Color Contrast**: Sufficient contrast ratios
- **Focus Management**: Clear focus indicators

## 🚀 Deployment Architecture

### Build Process

1. **Type Checking**: TypeScript compilation
2. **Linting**: ESLint and Prettier
3. **Testing**: Unit and integration tests
4. **Building**: Next.js production build
5. **Optimization**: Bundle analysis and optimization

### Deployment Targets

- **Vercel**: Primary deployment platform
- **Static Export**: Fallback for other platforms
- **Docker**: Containerized deployment option

### Environment Configuration

- **Environment Variables**: `NEXT_PUBLIC_*` prefix
- **Runtime Configuration**: Dynamic config loading
- **Feature Flags**: Conditional feature enablement

## 🔧 Development Workflow

### Local Development

1. **Setup**: Clone repo and install dependencies
2. **Environment**: Configure environment variables
3. **Development**: Hot reload with `pnpm dev`
4. **Testing**: Run tests with `pnpm test`
5. **Building**: Production build with `pnpm build`

### Code Quality

- **Pre-commit Hooks**: ESLint and Prettier
- **Type Checking**: TypeScript strict mode
- **Testing**: Automated test runs
- **Code Review**: Pull request reviews

## 📊 Monitoring & Observability

### Performance Monitoring

- **Core Web Vitals**: Lighthouse CI
- **Real User Monitoring**: Vercel Analytics
- **Error Tracking**: Sentry integration
- **Bundle Analysis**: Webpack Bundle Analyzer

### Logging Strategy

- **Structured Logging**: JSON format logs
- **Error Logging**: Sentry for error tracking
- **Performance Logs**: Timing and metrics
- **User Analytics**: Privacy-compliant tracking

## 🔄 Future Considerations

### Scalability

- **Micro Frontends**: Consider for large-scale applications
- **Module Federation**: Dynamic module loading
- **Performance Budgets**: Set and enforce limits
- **Bundle Splitting**: Advanced code splitting strategies

### Technology Evolution

- **React Server Components**: Consider for Next.js 15+
- **Concurrent Features**: Leverage React 18+ features
- **TypeScript**: Stay updated with latest features
- **Build Tools**: Evaluate new build tools and optimizations

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Query Documentation](https://tanstack.com/query)
- [Zustand Documentation](https://zustand-demo.pmnd.rs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Testing Library Documentation](https://testing-library.com/docs/)
