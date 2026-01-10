# Goblin Assistant Code Style & Patterns Guide

## 🎯 Foundational Principles

1. **Consistency Hierarchy**
   - Primary > Team > Project > Personal Preference
   - If it exists in codebase → Follow it
   - If it conflicts → Choose most common pattern
   - If undefined → Establish standard here

### 🟨 TypeScript/JavaScript Guidelines

#### File Structure Pattern

```typescript
// 1. Imports (external → internal)
import React from 'react'
import { useRouter } from 'next/router'
import { Button } from '@/components/ui'
import { apiService } from '@/lib/api'
import { formatDate } from '@/utils/helpers'
import type { User } from '@/types/user'

// 2. Constants
const MAX_RETRIES = 3
const DEFAULT_CONFIG = {
  timeout: 5000,
  retry: true,
} as const

// 3. Type/Interface Definitions
interface ComponentProps {
  user: User
  onSuccess?: () => void
  isDisabled?: boolean
}

type ApiResponse<T = unknown> = {
  data: T
  error?: string
  timestamp: number
}

// 4. Main Component/Function
export default function UserProfile({ user, onSuccess, isDisabled = false }: ComponentProps) {
  // 5. Hooks (in order of React rules)
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const { data, error } = useQuery(['user', user.id], fetchUserDetails)

  // 6. Derived state
  const isActive = user.status === 'active'
  const fullName = `${user.firstName} ${user.lastName}`.trim()

  // 7. Event handlers
  const handleSave = useCallback(async () => {
    setLoading(true)
    try {
      await apiService.updateUser(user.id, user)
      onSuccess?.()
    } catch (err) {
      console.error('Save failed:', err)
    } finally {
      setLoading(false)
    }
  }, [user, onSuccess])

  // 8. Effects
  useEffect(() => {
    if (error) {
      showNotification('Failed to load user')
    }
  }, [error])

  // 9. Render logic
  if (!user) return <LoadingSpinner />

  return (
    <div className="profile-container">
      {/* JSX structure */}
    </div>
  )
}

// 10. Helper functions (outside component if not using props/state)
function formatUserRole(role: string): string {
  return role.charAt(0).toUpperCase() + role.slice(1).toLowerCase()
}

// 11. PropTypes (if using JavaScript)
UserProfile.propTypes = {
  user: PropTypes.object.isRequired,
  onSuccess: PropTypes.func,
}
```

#### Naming Conventions

```typescript
// Variables & Functions - camelCase
const userName = 'Goblin'
const fetchUserData = () => {}

// Classes & Types - PascalCase
class UserService { }
interface ApiResponse { }
type UserPreferences = { }

// Constants - UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 5
const DEFAULT_TIMEOUT = 3000

// Private members - prefix with underscore
private _internalCache = {}
private _handleInternalEvent() {}

// Boolean variables - prefix with is/has/should/can
const isVisible = true
const hasPermission = false
const shouldUpdate = true
const canEdit = false

// File names - kebab-case
// ✅ user-profile.tsx, api-client.ts, use-auth-hook.ts
// ❌ UserProfile.tsx, apiClient.ts, useAuthHook.ts
```

#### Variable Naming - Avoid Generic Names

**❌ Avoid these generic variable names:**

- `data` - Too vague, doesn't describe what the data represents
- `res` - Abbreviation for "response", use `apiResponse` or `userResponse`
- `obj` - Abbreviation for "object", use descriptive names like `userData` or `config`
- `arr` - Abbreviation for "array", use `items`, `users`, `results`
- `temp` - Temporary variables should be descriptive of their purpose
- `e` - Event handlers should use `event`, `clickEvent`, or `motionEvent`
- `x`, `y` - Mathematical coordinates should be `normalizedX`, `positionY`

**✅ Use descriptive, context-specific names:**

```typescript
// API Responses
const userData = await api.getUser();           // ✅ Clear what data this is
const apiResponse = await fetch('/api/data');   // ✅ Describes the source
const authResponse = await login();             // ✅ Specific to authentication

// Data Collections
const userList = await getUsers();              // ✅ Clear it's a list of users
const productItems = await getProducts();       // ✅ Specific item type
const searchResults = await search(query);      // ✅ Describes the operation

// Event Handlers
const handleClick = (clickEvent) => { ... };    // ✅ Descriptive event name
const handleMotionChange = (motionEvent) => { ... }; // ✅ Specific to motion

// Mathematical/Coordinate Variables
const normalizedX = (index / maxIndex) * width; // ✅ Clear it's normalized
const currentValue = array.reduce((sum, value) => sum + value); // ✅ Describes purpose
```

#### Commenting Guidelines

**💡 Philosophy: Comments should explain WHY, not WHAT**

##### When to Comment

**✅ DO comment when:**

- **Business logic complexity** - Explain domain-specific decisions
- **Non-obvious solutions** - Why this approach over alternatives
- **API contracts** - What the function does, parameters, return values
- **Side effects** - Async operations, state mutations, external calls
- **Constraints** - Performance requirements, security considerations
- **Future work** - TODOs, FIXMEs, technical debt

**❌ DON'T comment when:**

- **Code is self-explanatory** - `incrementCounter()` doesn't need "increments counter"
- **Implementation details** - What each line does (that's what code is for)
- **Obvious logic** - `if (user.isActive)` doesn't need "check if user is active"
- **Commented-out code** - Delete it or use version control

##### JSDoc Standards

**Always use JSDoc for:**

- **Public API functions** - Components, hooks, utilities
- **Complex business logic** - Multi-step algorithms
- **Configuration objects** - What each option controls
- **Error conditions** - When and why exceptions are thrown

````typescript
/**
 * Authenticates user with OAuth provider and establishes session
 *
 * @param provider - OAuth provider ('google', 'github', 'discord')
 * @param redirectUrl - Where to redirect after successful auth
 * @returns Promise resolving to user session data
 * @throws {AuthError} When authentication fails or provider is unsupported
 * @throws {NetworkError} When OAuth service is unreachable
 *
 * @example
 * ```typescript
 * const session = await authenticateUser('google', '/dashboard');
 * console.log('User authenticated:', session.user.email);
 * ```
 */
export async function authenticateUser(
  provider: OAuthProvider,
  redirectUrl: string
): Promise<UserSession> {
  // Implementation...
}
````

````typescript
/**
 * Custom hook for managing async data fetching with caching
 *
 * @param key - Unique cache key for this data
 * @param fetcher - Function that returns the data
 * @param options - Configuration options
 * @param options.staleTime - How long data stays fresh (default: 5min)
 * @param options.refetchOnWindowFocus - Refetch when window regains focus
 * @returns Object with data, loading state, and refetch function
 *
 * @example
 * ```typescript
 * const { data, isLoading, refetch } = useQuery(
 *   ['user-profile', userId],
 *   () => api.getUser(userId),
 *   { staleTime: 10000 }
 * );
 * ```
 */
export function useQuery<T>(
  key: QueryKey,
  fetcher: () => Promise<T>,
  options: QueryOptions = {}
): QueryResult<T> {
  // Implementation...
}
````

##### Comment Quality Standards

**✅ Good Comments:**

```typescript
// Business logic: Premium users get 2x faster processing to reduce wait times
// and improve conversion rates based on A/B test results (Experiment #247)
if (user.tier === 'premium') {
  processingSpeed = baseSpeed * 2;
}

// Security: Rate limit to prevent abuse, allows 100 req/min per IP
// Based on OWASP guidelines for API protection
const rateLimiter = new RateLimiter({ windowMs: 60000, max: 100 });
```

**❌ Bad Comments:**

```typescript
// This function gets the user data
function getUserData() { ... }

// Check if user is logged in
if (user.loggedIn) { ... }

// Increment the counter by 1
counter = counter + 1;
```

##### File Header Comments

**For complex files, add a header explaining purpose and scope:**

```typescript
/**
 * @fileoverview User authentication and session management
 *
 * This module handles the complete OAuth flow for multiple providers,
 * session persistence, and automatic token refresh. It integrates with
 * our backend API and maintains security best practices.
 *
 * Key responsibilities:
 * - OAuth provider integration (Google, GitHub, Discord)
 * - JWT token management and refresh
 * - Session state persistence
 * - Security headers and CSRF protection
 *
 * @author Auth Team
 * @since 1.0.0
 */
```

##### TODO and FIXME Comments

**Use structured format for future work:**

```typescript
// TODO: [AUTH-123] Implement OAuth PKCE flow for enhanced security
// See: https://tools.ietf.org/html/rfc7636
// Priority: High, ETA: Sprint 12

// FIXME: [PERF-456] This causes N+1 queries, optimize with dataloader
// Temporary workaround until backend adds batch endpoint
// Impact: Affects user list page performance
```

#### Component Patterns

```typescript
// 1. Function Components with TypeScript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  onClick: () => void
  children: React.ReactNode
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', onClick, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={`btn btn-${variant} btn-${size}`}
        onClick={onClick}
        {...props}
      >
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'

// 2. Custom Hooks Pattern
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch {
      return initialValue
    }
  })

  const setValue = useCallback((value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value
      setStoredValue(valueToStore)
      window.localStorage.setItem(key, JSON.stringify(valueToStore))
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error)
    }
  }, [key, storedValue])

  return [storedValue, setValue] as const
}

// 3. Compound Components Pattern
const Card = ({ children }: { children: React.ReactNode }) => (
  <div className="card">{children}</div>
)

Card.Header = ({ children }: { children: React.ReactNode }) => (
  <div className="card-header">{children}</div>
)

Card.Body = ({ children }: { children: React.ReactNode }) => (
  <div className="card-body">{children}</div>
)

// Usage: <Card><Card.Header>Title</Card.Header><Card.Body>Content</Card.Body></Card>
```

### 🐍 Python Guidelines

#### Python File Structure Pattern

```python
# 1. Module docstring
"""
user_service.py - Handles user-related operations
"""

# 2. Imports (standard lib → third-party → local)
import os
import json
from typing import Optional, Dict, List
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .schemas import UserCreate, UserUpdate

# 3. Constants
MAX_LOGIN_ATTEMPTS = 5
DEFAULT_PAGE_SIZE = 20
SUPPORTED_LOCALES = ['en', 'es', 'fr']

# 4. Type definitions
class UserStats:
    """Statistics for a user"""
    total_posts: int
    last_active: datetime

# 5. Exception classes
class UserNotFoundError(Exception):
    """Raised when user is not found"""
    pass

class InvalidCredentialsError(Exception):
    """Raised when credentials are invalid"""
    pass

# 6. Main classes/functions
class UserService:
    """Service for user management operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve user by ID.

        Args:
            user_id: The user's unique identifier

        Returns:
            User object if found, None otherwise

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            raise UserNotFoundError(f"User {user_id} not found")

        return user

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user.

        Args:
            user_data: Validated user creation data

        Returns:
            The created User instance
        """
        # Implementation
        pass

# 7. Helper functions
def validate_email_format(email: str) -> bool:
    """Validate email format using basic regex."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# 8. Main guard (if script is runnable)
if __name__ == "__main__":
    # Example usage
    service = UserService()
```

#### Python-Specific Rules

```python
# Naming
snake_case_for_variables = "value"
CONSTANT_VALUES = "immutable"
ClassNamePascalCase = "For classes"

# Type hints everywhere
def calculate_total(
    items: List[float],
    discount: Optional[float] = None
) -> float:
    """Calculate total with optional discount."""
    total = sum(items)
    if discount:
        total *= (1 - discount)
    return total

# Use dataclasses for data containers
from dataclasses import dataclass
from typing import Optional

@dataclass
class UserProfile:
    username: str
    email: str
    age: Optional[int] = None
    is_active: bool = True

# Context managers for resources
def read_file_safely(path: str) -> str:
    with open(path, 'r') as file:
        return file.read()

# Use pathlib instead of os.path
from pathlib import Path
config_path = Path(__file__).parent / 'config.yaml'
```

## 📁 Project Structure Pattern

### Consistent Directory Layout

```text
goblin-assistant/
├── src/                    # Source code
│   ├── components/         # React components
│   │   ├── ui/            # Base UI components (Button, Input, etc.)
│   │   ├── layout/        # Layout components
│   │   ├── features/      # Feature-specific components
│   │   └── shared/        # Shared across features
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # Library code, utilities
│   │   ├── api/           # API clients, service layers
│   │   ├── utils/         # Pure utility functions
│   │   └── constants/     # App constants
│   ├── types/             # TypeScript type definitions
│   ├── styles/            # Global styles, themes
│   └── pages/             # Next.js pages or route components
├── backend/               # Python backend
│   ├── api/               # FastAPI/routes
│   │   ├── v1/            # API version 1
│   │   └── v2/            # API version 2
│   ├── core/              # Core business logic
│   │   ├── config/        # Configuration
│   │   ├── models/        # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/      # Business logic services
│   ├── database/          # DB connection, migrations
│   └── utils/             # Backend utilities
├── tests/                 # All tests
│   ├── frontend/
│   │   ├── unit/          # Component/utility tests
│   │   ├── integration/   # Integration tests
│   │   └── e2e/           # Cypress/Playwright tests
│   └── backend/
│       ├── unit/          # Service/function tests
│       └── integration/   # API/database tests
├── scripts/               # Build/deployment scripts
├── docs/                  # Documentation
└── tools/                 # Development tools, scripts
```

### Import Aliases Pattern

```json
// tsconfig.json / jsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@lib/*": ["src/lib/*"],
      "@hooks/*": ["src/hooks/*"],
      "@types/*": ["src/types/*"],
      "@styles/*": ["src/styles/*"]
    }
  }
}

// Usage in code
import { Button } from '@/components/ui/Button'
import { apiClient } from '@/lib/api/client'
import { useAuth } from '@/hooks/useAuth'
```

## 🔧 API Design Patterns

### REST API Consistency

```python
# API Response Standard
from typing import Generic, TypeVar, Optional
from pydantic.generics import GenericModel

T = TypeVar('T')

class ApiResponse(GenericModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    message: Optional[str] = None

    @classmethod
    def success_response(cls, data: T, message: str = "Success") -> "ApiResponse[T]":
        return cls(success=True, data=data, message=message)

    @classmethod
    def error_response(cls, error: str, message: str = "Error") -> "ApiResponse[None]":
        return cls(success=False, error=error, message=message)

# Error Handling Middleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Convert to standardized error response
    return JSONResponse(
        status_code=500,
        content=ApiResponse.error_response(
            error="Internal server error",
            message="An unexpected error occurred"
        ).dict()
    )
```

### Frontend API Client Pattern

```typescript
// src/lib/api/client.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Handle token refresh
          await this.refreshToken();
          return this.client.request(error.config);
        }
        return Promise.reject(error);
      }
    );
  }

  // Standardized methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.get(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.post(url, data, config);
    return response.data;
  }

  // Add put, delete, patch similarly
}

// Singleton instance
export const apiClient = new ApiClient(process.env.NEXT_PUBLIC_API_URL || '/api');
```

## ✅ Testing Patterns

### Frontend Test Structure

```typescript
// tests/frontend/unit/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '@/components/ui/Button'

describe('Button Component', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click</Button>)

    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('applies correct variant classes', () => {
    const { container } = render(<Button variant="danger">Delete</Button>)
    expect(container.firstChild).toHaveClass('btn-danger')
  })
})

// Test utilities pattern
// tests/frontend/test-utils.tsx
import { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { ThemeProvider } from '@/components/providers/ThemeProvider'

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return <ThemeProvider>{children}</ThemeProvider>
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }
```

### Backend Test Pattern

```python
# tests/backend/unit/test_user_service.py
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from backend.core.models import User
from backend.core.services.user_service import UserService
from backend.core.schemas import UserCreate

class TestUserService:
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        return UserService(db=mock_db)

    def test_get_user_by_id_found(self, service, mock_db):
        # Arrange
        mock_user = User(id=1, username="testuser")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Act
        result = service.get_user_by_id(1)

        # Assert
        assert result == mock_user
        mock_db.query.assert_called_once_with(User)

    def test_get_user_by_id_not_found(self, service, mock_db):
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundError):
            service.get_user_by_id(999)
```

## 🧪 Unit Testing Implementation

### Testing Setup

Install testing libraries:

```bash
npm install --save-dev jest @testing-library/react @testing-library/jest-dom @testing-library/user-event @types/jest ts-jest
```

Create `jest.config.js`:

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/**/*.test.{ts,tsx}',
    '!src/**/index.{ts,tsx}',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  testPathIgnorePatterns: ['/node_modules/', '/.next/'],
};
```

Create `jest.setup.js`:

```javascript
import '@testing-library/jest-dom';
import { jest } from '@jest/globals';

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    query: {},
    pathname: '/',
  }),
}));

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock fetch
global.fetch = jest.fn();
```

### Component Test Template

```typescript
// Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with default props', () => {
    render(<Button>Click me</Button>);

    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('btn-primary');
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Button variant="primary">Test</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-primary');

    rerender(<Button variant="danger">Test</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-danger');
  });

  it('is disabled when loading', () => {
    render(<Button loading>Submit</Button>);

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveTextContent('Loading...');
  });
});
```

### Hook Test Template

```typescript
// useLocalStorage.test.ts
import { renderHook, act } from '@testing-library/react';
import { useLocalStorage } from './useLocalStorage';

describe('useLocalStorage', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it('initializes with default value', () => {
    const { result } = renderHook(() => useLocalStorage('test-key', 'default'));

    expect(result.current[0]).toBe('default');
  });

  it('retrieves existing value from localStorage', () => {
    localStorage.setItem('test-key', JSON.stringify('stored-value'));

    const { result } = renderHook(() => useLocalStorage('test-key', 'default'));

    expect(result.current[0]).toBe('stored-value');
  });

  it('updates localStorage when value changes', () => {
    const { result } = renderHook(() => useLocalStorage('test-key', 'default'));

    act(() => {
      result.current[1]('new-value');
    });

    expect(localStorage.setItem).toHaveBeenCalledWith('test-key', JSON.stringify('new-value'));
    expect(result.current[0]).toBe('new-value');
  });
});
```

### Test Coverage Report Script

Add to `package.json`:

```json
"scripts": {
  "test": "jest",
  "test:watch": "jest --watch",
  "test:coverage": "jest --coverage",
  "test:update": "jest --updateSnapshot",
  "test:ci": "jest --coverage --coverageReporters=text-lcov | coveralls"
}
```

Create test coverage checker:

```javascript
// scripts/check-test-coverage.js
const fs = require('fs');
const path = require('path');

const MIN_COVERAGE = {
  lines: 80,
  statements: 80,
  functions: 80,
  branches: 70,
};

function checkCoverage() {
  const coveragePath = path.join(__dirname, '../coverage/coverage-summary.json');

  if (!fs.existsSync(coveragePath)) {
    console.error('❌ Coverage report not found. Run tests first.');
    process.exit(1);
  }

  const coverage = JSON.parse(fs.readFileSync(coveragePath, 'utf-8'));

  console.log('\n📊 Test Coverage Report:\n');

  let allPassed = true;

  Object.keys(coverage.total).forEach((key) => {
    const value = coverage.total[key].pct;
    const min = MIN_COVERAGE[key] || 0;
    const passed = value >= min;

    const icon = passed ? '✅' : '❌';
    console.log(`${icon} ${key}: ${value}% (minimum: ${min}%)`);

    if (!passed) {
      allPassed = false;
    }
  });

  console.log('\n📁 File-by-file coverage:');

  // Show low coverage files
  Object.keys(coverage).forEach((file) => {
    if (file !== 'total') {
      const fileCoverage = coverage[file];
      const lines = fileCoverage.lines.pct;

      if (lines < MIN_COVERAGE.lines) {
        console.log(`  ⚠️  ${file}: ${lines}% line coverage`);
      }
    }
  });

  if (!allPassed) {
    console.error('\n❌ Minimum coverage not met.');
    process.exit(1);
  }

  console.log('\n✅ All coverage targets met!');
}

checkCoverage();
```

### CI/CD Integration: GitHub Actions Workflow

Create `.github/workflows/quality-checks.yml`:

```yaml
name: Quality Checks

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  quality:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Lint check
        run: npm run lint

      - name: Type check
        run: npm run type-check

      - name: Naming convention check
        run: npm run check:naming

      - name: Component analysis
        run: npm run analyze:components

      - name: Run tests with coverage
        run: npm run test:coverage

      - name: Check test coverage
        run: npm run check:coverage

      - name: Build check
        run: npm run build
```

### Pre-Push Validation: Husky Git Hooks

Install Husky and create `.husky/pre-push`:

```bash
npm install --save-dev husky
npx husky install
npx husky add .husky/pre-push
```

Add to `.husky/pre-push`:

```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

echo "🚀 Running pre-push checks..."

# Run tests
npm test

# Check for console.log statements (except in tests)
if grep -r "console\.log" src --include="*.ts" --include="*.tsx" --exclude-dir="*.test.*" | grep -v "// console.log allowed"; then
  echo "❌ Found console.log in source files. Remove before pushing."
  exit 1
fi

# Check for leftover TODO comments without issue links
if grep -r "TODO\|FIXME\|HACK\|XXX" src --include="*.ts" --include="*.tsx" | grep -v "#ISSUE-" | grep -v "https://"; then
  echo "❌ TODO comments must include issue tracker link."
  exit 1
fi

echo "✅ All checks passed!"
```

**Note**: Due to current disk space constraints, Husky installation is pending. Add this hook once storage is available.

## 💬 Documentation Patterns

### Code Documentation Standards

````typescript
/**
 * Calculates the total price with tax and discounts applied.
 *
 * @param items - Array of item prices
 * @param taxRate - Tax rate as decimal (e.g., 0.08 for 8%)
 * @param discountCode - Optional discount code to apply
 *
 * @returns The final total price rounded to 2 decimals
 *
 * @example
 * ```typescript
 * const total = calculateTotal([10, 20, 30], 0.08, 'SAVE10')
 * console.log(total) // 64.80
 * ```
 *
 * @throws {ValidationError} If taxRate is negative
 * @throws {DiscountError} If discount code is invalid
 */
function calculateTotal(items: number[], taxRate: number, discountCode?: string): number {
  // Implementation
}
````

```python
def calculate_total(items: List[float], tax_rate: float = 0.08) -> float:
    """Calculate total with tax.

    Args:
        items: List of item prices as floats
        tax_rate: Tax rate as decimal (default 0.08 for 8%)

    Returns:
        Total price with tax applied, rounded to 2 decimals

    Raises:
        ValueError: If tax_rate is negative
        TypeError: If items contains non-numeric values

    Example:
        >>> calculate_total([10.0, 20.0, 30.0], 0.08)
        64.80
    """
    if tax_rate < 0:
        raise ValueError("Tax rate cannot be negative")

    subtotal = sum(items)
    total = subtotal * (1 + tax_rate)
    return round(total, 2)
```

## 🔄 State Management Pattern

### Consistent State Structure

```typescript
// src/store/user/userSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { User } from '@/types/user';
import { apiClient } from '@/lib/api/client';

interface UserState {
  currentUser: User | null;
  loading: boolean;
  error: string | null;
  users: User[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    hasMore: boolean;
  };
}

const initialState: UserState = {
  currentUser: null,
  loading: false,
  error: null,
  users: [],
  pagination: {
    page: 1,
    limit: 20,
    total: 0,
    hasMore: false,
  },
};

// Async thunks follow naming convention: <entity>/<action>
export const fetchUsers = createAsyncThunk(
  'users/fetchUsers',
  async (page: number, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(`/users?page=${page}&limit=20`);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch users');
    }
  }
);

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    // Synchronous actions
    setCurrentUser: (state, action: PayloadAction<User | null>) => {
      state.currentUser = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.loading = false;
        state.users = action.payload.data;
        state.pagination = action.payload.pagination;
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { setCurrentUser, clearError } = userSlice.actions;
export default userSlice.reducer;
```

## ⚙️ Configuration Pattern

### Environment Configuration

```typescript
// src/config/env.ts
interface AppConfig {
  api: {
    baseUrl: string;
    timeout: number;
  };
  features: {
    enableAnalytics: boolean;
    enableExperimental: boolean;
  };
  urls: {
    website: string;
    docs: string;
  };
}

// Load from environment with defaults
export const config: AppConfig = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api',
    timeout: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '10000'),
  },
  features: {
    enableAnalytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
    enableExperimental: process.env.NEXT_PUBLIC_ENABLE_EXPERIMENTAL === 'true',
  },
  urls: {
    website: process.env.NEXT_PUBLIC_WEBSITE_URL || 'https://goblin-assistant.com',
    docs: process.env.NEXT_PUBLIC_DOCS_URL || 'https://docs.goblin-assistant.com',
  },
};
```

## 🔗 Git & Commit Patterns

### Commit Message Convention

```text
<type>(<scope>): <subject>

<body>

<footer>

Types:
feat:     New feature
fix:      Bug fix
docs:     Documentation
style:    Formatting, missing semi-colons, etc (no code change)
refactor: Code refactoring
test:     Adding tests
chore:    Build process or auxiliary tool changes
```

### Branch Naming

```text
feature/<short-description>    # New features
bugfix/<issue-number>          # Bug fixes
hotfix/<critical-issue>        # Emergency fixes
refactor/<area-of-refactor>    # Refactoring
docs/<documentation-update>    # Documentation
```

## 🧩 Modularization Examples

### BEFORE - Monolithic Component

```typescript
// UserDashboard.tsx - 350 lines
const UserDashboard = () => {
  const [user, setUser] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({});

  // 5 useEffect hooks
  // 3 API calls
  // Multiple conditional renders
  // Form handling
  // Chart rendering
  // etc...

  return (
    <div>
      {/* 150 lines of JSX */}
    </div>
  );
};
```

### AFTER - Modular Components

```typescript
// UserDashboard.tsx - 50 lines
const UserDashboard = () => {
  const { user, loading, error } = useUser();
  const { orders } = useOrders();
  const { stats } = useUserStats();

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div className="dashboard">
      <DashboardHeader user={user} />
      <StatsOverview stats={stats} />
      <RecentOrders orders={orders} />
      <QuickActions userId={user.id} />
    </div>
  );
};

// Extracted hooks
// hooks/useUser.ts
// hooks/useOrders.ts

// Extracted components
// components/dashboard/DashboardHeader.tsx
// components/dashboard/StatsOverview.tsx
// components/dashboard/RecentOrders.tsx
// components/dashboard/QuickActions.tsx
```

## 🎨 Quick Reference Cheatsheet

### DOs and DON'Ts

```typescript
// ✅ DO
const userList = []; // descriptive
const isLoading = true; // boolean prefix
function fetchUserData() {} // verb-noun
interface ApiResponse {} // PascalCase for interface
const MAX_RETRIES = 3; // constant

// ❌ DON'T
const list = []; // vague
const loading = true; // ambiguous
function user() {} // not a verb
interface apiResponse {} // camelCase for interface
const maxRetries = 3; // not constant case

// ✅ DO - Early returns
function processOrder(order: Order) {
  if (!order.isValid) return null;
  if (order.isCancelled) return { status: 'cancelled' };

  // Main logic
  return processValidOrder(order);
}

// ❌ DON'T - Nested conditionals
function processOrder(order: Order) {
  if (order.isValid) {
    if (!order.isCancelled) {
      // Deep nesting
    }
  }
}
```

## 🚀 Implementation Priority

### Phase 1: Establish Basics (Week 1)

- Set up ESLint + Prettier with shared config
- Create .editorconfig for cross-IDE consistency
- Document naming conventions in `/docs/code-style.md`
- Fix 10 most critical style violations

### Phase 2: Refactor Hotspots (Week 2)

- Standardize API layer (frontend + backend)
- Unify error handling patterns
- Consolidate component patterns
- Create shared TypeScript types

### Phase 3: Automated Enforcement (Week 3)

- Git hooks for pre-commit checks
- CI pipeline with style checks
- Create code templates for new files
- Documentation examples for common patterns
