# Testing Guide

This document describes the testing strategies, tools, and best practices for the GoblinOS Assistant frontend application built with Next.js.

## 🧪 Testing Overview

We follow a comprehensive testing approach with multiple layers:

1. **Unit Tests** - Test individual components and functions
2. **Integration Tests** - Test component interactions and API integration
3. **E2E Tests** - Test complete user workflows
4. **Visual Regression Tests** - Test UI consistency
5. **Accessibility Tests** - Test A11y compliance

## 🛠️ Testing Tools

### Jest & React Testing Library

- **Jest**: JavaScript testing framework
- **React Testing Library**: React component testing utilities
- **Coverage**: Minimum 80% coverage required

### Playwright

- **E2E Testing**: Cross-browser end-to-end testing
- **Performance Testing**: Lighthouse integration
- **Visual Testing**: Screenshot comparisons

### Storybook

- **Component Testing**: Isolated component testing
- **Visual Regression**: Chromatic integration
- **Documentation**: Living component documentation

## 📊 Testing Pyramid

```
    E2E Tests (Playwright)
   /                      \
  / Integration Tests     \
 / (React Query, API)     \
/__________________________\
     Unit Tests (Jest + RTL)
```

## 🎯 Unit Testing

### Component Testing

```tsx
// components/ui/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button Component', () => {
  it('renders with children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('shows loading state', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('applies correct variant classes', () => {
    const { container } = render(<Button variant="primary">Click me</Button>);
    expect(container.firstChild).toHaveClass('bg-blue-500');
  });

  it('renders with start and end icons', () => {
    render(
      <Button startIcon={<span>👈</span>} endIcon={<span>👉</span>}>
        Click me
      </Button>
    );
    expect(screen.getByText('👈')).toBeInTheDocument();
    expect(screen.getByText('👉')).toBeInTheDocument();
  });
});
```

### Hook Testing

```tsx
// hooks/useTheme.test.tsx
import { renderHook, act } from '@testing-library/react';
import { useTheme } from './useTheme';

describe('useTheme Hook', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  it('should initialize with light theme by default', () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe('light');
  });

  it('should initialize with saved theme from localStorage', () => {
    localStorage.setItem('theme', 'dark');
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe('dark');
  });

  it('should toggle theme', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.toggleTheme();
    });
    
    expect(result.current.theme).toBe('dark');
    
    act(() => {
      result.current.toggleTheme();
    });
    
    expect(result.current.theme).toBe('light');
  });

  it('should set theme explicitly', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.setTheme('dark');
    });
    
    expect(result.current.theme).toBe('dark');
    expect(localStorage.getItem('theme')).toBe('dark');
  });
});
```

### API Service Testing

```tsx
// lib/api/services/providerService.test.ts
import { providerService } from './providerService';
import { apiClient } from '../client-axios';

// Mock the API client
jest.mock('../client-axios', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('ProviderService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should get all providers', async () => {
    const mockProviders = [
      { id: '1', name: 'OpenAI', type: 'openai' },
      { id: '2', name: 'Anthropic', type: 'anthropic' },
    ];

    mockApiClient.get.mockResolvedValue(mockProviders);

    const result = await providerService.getProviders();

    expect(mockApiClient.get).toHaveBeenCalledWith('/api/providers');
    expect(result).toEqual(mockProviders);
  });

  it('should get a single provider', async () => {
    const mockProvider = { id: '1', name: 'OpenAI', type: 'openai' };

    mockApiClient.get.mockResolvedValue(mockProvider);

    const result = await providerService.getProvider('1');

    expect(mockApiClient.get).toHaveBeenCalledWith('/api/providers/1');
    expect(result).toEqual(mockProvider);
  });

  it('should create a provider', async () => {
    const mockProvider = { id: '1', name: 'OpenAI', type: 'openai' };
    const createData = { name: 'OpenAI', type: 'openai' };

    mockApiClient.post.mockResolvedValue(mockProvider);

    const result = await providerService.createProvider(createData);

    expect(mockApiClient.post).toHaveBeenCalledWith('/api/providers', createData);
    expect(result).toEqual(mockProvider);
  });

  it('should handle API errors', async () => {
    mockApiClient.get.mockRejectedValue(new Error('Network error'));

    await expect(providerService.getProviders()).rejects.toThrow('Network error');
  });
});
```

## 🔗 Integration Testing

### API Integration Testing

```tsx
// lib/api/queries/providerQueries.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useProviders, useCreateProvider } from './providerQueries';
import { providerService } from '../services/providerService';

// Mock the service
jest.mock('../services/providerService');

const mockProviderService = providerService as jest.Mocked<typeof providerService>;

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('Provider Queries', () => {
  const wrapper = createWrapper();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useProviders', () => {
    it('should fetch providers', async () => {
      const mockProviders = [
        { id: '1', name: 'OpenAI', type: 'openai' },
        { id: '2', name: 'Anthropic', type: 'anthropic' },
      ];

      mockProviderService.getProviders.mockResolvedValue(mockProviders);

      const { result } = renderHook(() => useProviders(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockProviders);
    });

    it('should handle errors', async () => {
      mockProviderService.getProviders.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useProviders(), { wrapper });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(new Error('Network error'));
    });
  });

  describe('useCreateProvider', () => {
    it('should create a provider and invalidate cache', async () => {
      const mockProvider = { id: '1', name: 'OpenAI', type: 'openai' };
      const createData = { name: 'OpenAI', type: 'openai' };

      mockProviderService.createProvider.mockResolvedValue(mockProvider);
      mockProviderService.getProviders.mockResolvedValue([mockProvider]);

      const { result } = renderHook(() => useCreateProvider(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync(createData);
      });

      expect(mockProviderService.createProvider).toHaveBeenCalledWith(createData);
      expect(mockProviderService.getProviders).toHaveBeenCalled();
    });
  });
});
```

### Component Integration Testing

```tsx
// components/providers/ProviderList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useProviders } from '@/lib/api/queries/providerQueries';
import { ProviderList } from './ProviderList';

// Mock the API hook
jest.mock('@/lib/api/queries/providerQueries');

const mockUseProviders = useProviders as jest.MockedFunction<typeof useProviders>;

describe('ProviderList Integration', () => {
  const queryClient = new QueryClient();

  beforeEach(() => {
    mockUseProviders.mockReturnValue({
      data: [
        { id: '1', name: 'OpenAI', type: 'openai', status: 'active' },
        { id: '2', name: 'Anthropic', type: 'anthropic', status: 'active' },
      ],
      isLoading: false,
      error: null,
    });
  });

  it('renders providers with correct information', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ProviderList />
      </QueryClientProvider>
    );

    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.getByText('Anthropic')).toBeInTheDocument();
    expect(screen.getByText('openai')).toBeInTheDocument();
    expect(screen.getByText('anthropic')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockUseProviders.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <ProviderList />
      </QueryClientProvider>
    );

    expect(screen.getByText('Loading providers...')).toBeInTheDocument();
  });

  it('shows error state', () => {
    const error = new Error('Failed to load providers');
    mockUseProviders.mockReturnValue({
      data: undefined,
      isLoading: false,
      error,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <ProviderList />
      </QueryClientProvider>
    );

    expect(screen.getByText('Error loading providers: Failed to load providers')).toBeInTheDocument();
  });
});
```

## 🎭 E2E Testing with Playwright

### Basic E2E Test

```typescript
// e2e/app.spec.ts
import { test, expect } from '@playwright/test';

test.describe('GoblinOS Assistant', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load the homepage', async ({ page }) => {
    await expect(page).toHaveTitle(/GoblinOS/);
    await expect(page.locator('h1')).toContainText('Welcome');
  });

  test('should navigate to providers page', async ({ page }) => {
    await page.click('[data-testid="providers-link"]');
    await expect(page).toHaveURL('/providers');
    await expect(page.locator('h2')).toContainText('Providers');
  });

  test('should create a new provider', async ({ page }) => {
    await page.goto('/providers');
    
    await page.click('[data-testid="create-provider-button"]');
    
    await page.fill('[data-testid="provider-name-input"]', 'Test Provider');
    await page.selectOption('[data-testid="provider-type-select"]', 'openai');
    await page.fill('[data-testid="provider-api-key-input"]', 'test-api-key');
    
    await page.click('[data-testid="save-provider-button"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="provider-list"]')).toContainText('Test Provider');
  });

  test('should handle form validation', async ({ page }) => {
    await page.goto('/providers/new');
    
    await page.click('[data-testid="save-provider-button"]');
    
    await expect(page.locator('[data-testid="name-error"]')).toContainText('Name is required');
    await expect(page.locator('[data-testid="api-key-error"]')).toContainText('API key is required');
  });
});
```

### API Testing

```typescript
// e2e/api.spec.ts
import { test, expect } from '@playwright/test';

test.describe('API Endpoints', () => {
  test('should return providers list', async ({ request }) => {
    const response = await request.get('/api/providers');
    
    expect(response.status()).toBe(200);
    const providers = await response.json();
    expect(Array.isArray(providers)).toBe(true);
  });

  test('should create a new provider', async ({ request }) => {
    const newProvider = {
      name: 'Test Provider',
      type: 'openai',
      config: {
        apiKey: 'test-key',
        model: 'gpt-3.5-turbo'
      }
    };

    const response = await request.post('/api/providers', {
      data: newProvider
    });

    expect(response.status()).toBe(201);
    const createdProvider = await response.json();
    expect(createdProvider.name).toBe('Test Provider');
    expect(createdProvider.id).toBeDefined();
  });

  test('should return 400 for invalid provider data', async ({ request }) => {
    const invalidProvider = {
      name: '',
      type: 'invalid',
      config: {}
    };

    const response = await request.post('/api/providers', {
      data: invalidProvider
    });

    expect(response.status()).toBe(400);
    const error = await response.json();
    expect(error.message).toContain('Validation failed');
  });
});
```

### Performance Testing

```typescript
// e2e/performance.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Performance Tests', () => {
  test('should load homepage within performance budget', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    
    // Wait for all resources to load
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Performance budget: page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
    
    // Check Core Web Vitals
    const vitals = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const vitals = {};
          
          entries.forEach((entry) => {
            if (entry.name === 'first-contentful-paint') {
              vitals['FCP'] = entry.startTime;
            }
            if (entry.name === 'largest-contentful-paint') {
              vitals['LCP'] = entry.startTime;
            }
          });
          
          resolve(vitals);
        }).observe({ entryTypes: ['paint', 'largest-contentful-paint'] });
        
        // Fallback timeout
        setTimeout(() => resolve({}), 2000);
      });
    });
    
    expect(vitals['FCP']).toBeLessThan(1500); // FCP should be under 1.5s
    expect(vitals['LCP']).toBeLessThan(2500); // LCP should be under 2.5s
  });

  test('should handle 100 providers without performance degradation', async ({ page }) => {
    // Create 100 test providers
    for (let i = 0; i < 100; i++) {
      await page.request.post('/api/providers', {
        data: {
          name: `Provider ${i}`,
          type: 'openai',
          config: { apiKey: `key-${i}` }
        }
      });
    }

    const startTime = Date.now();
    
    await page.goto('/providers');
    await page.waitForLoadState('networkidle');
    
    const renderTime = Date.now() - startTime;
    
    // Should render 100 providers within 2 seconds
    expect(renderTime).toBeLessThan(2000);
    
    // Should be able to scroll through all providers
    const providerCount = await page.locator('[data-testid="provider-item"]').count();
    expect(providerCount).toBe(100);
  });
});
```

## 🎨 Visual Regression Testing

### Storybook Stories

```tsx
// components/ui/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Components/UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'ghost', 'danger'],
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
    },
    disabled: {
      control: { type: 'boolean' },
    },
    loading: {
      control: { type: 'boolean' },
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Primary Button',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary Button',
  },
};

export const WithIcon: Story = {
  args: {
    startIcon: <span>✨</span>,
    children: 'With Icon',
  },
};

export const Loading: Story = {
  args: {
    loading: true,
    children: 'Loading',
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
    children: 'Disabled',
  },
};
```

### Visual Regression Tests

```typescript
// e2e/visual.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Visual Regression Tests', () => {
  test('homepage should not visually regress', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Full page screenshot
    await expect(page).toHaveScreenshot('homepage.png', {
      fullPage: true,
      threshold: 0.2,
    });
  });

  test('provider list should not visually regress', async ({ page }) => {
    await page.goto('/providers');
    await page.waitForLoadState('networkidle');
    
    // Screenshot of provider list section
    const providerList = page.locator('[data-testid="provider-list"]');
    await expect(providerList).toHaveScreenshot('provider-list.png');
  });

  test('provider form should not visually regress', async ({ page }) => {
    await page.goto('/providers/new');
    await page.waitForLoadState('networkidle');
    
    // Screenshot of form
    const form = page.locator('[data-testid="provider-form"]');
    await expect(form).toHaveScreenshot('provider-form.png');
  });

  test('error states should not visually regress', async ({ page }) => {
    await page.goto('/providers');
    
    // Trigger error state
    await page.click('[data-testid="delete-provider-button"]');
    await page.click('[data-testid="confirm-delete"]');
    
    // Screenshot of error message
    const errorMessage = page.locator('[data-testid="error-message"]');
    await expect(errorMessage).toHaveScreenshot('error-state.png');
  });
});
```

## ♿ Accessibility Testing

### Automated A11y Tests

```typescript
// e2e/accessibility.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Accessibility Tests', () => {
  test('homepage should be accessible', async ({ page }) => {
    await page.goto('/');
    
    // Run axe accessibility tests
    const { violations } = await page.accessibility.check();
    
    expect(violations).toEqual([]);
  });

  test('provider form should be accessible', async ({ page }) => {
    await page.goto('/providers/new');
    
    // Check form accessibility
    const { violations } = await page.accessibility.check({
      include: '[data-testid="provider-form"]'
    });
    
    expect(violations).toEqual([]);
  });

  test('keyboard navigation should work', async ({ page }) => {
    await page.goto('/providers');
    
    // Tab through all focusable elements
    await page.keyboard.press('Tab');
    
    // Check that we can navigate through the page
    const focusedElement = await page.evaluate(() => {
      return document.activeElement?.tagName;
    });
    
    expect(['BUTTON', 'A', 'INPUT', 'SELECT']).toContain(focusedElement);
  });

  test('color contrast should meet WCAG standards', async ({ page }) => {
    await page.goto('/');
    
    // Check color contrast using axe
    const { violations } = await page.accessibility.check({
      rules: {
        'color-contrast': { enabled: true }
      }
    });
    
    // Should have no color contrast violations
    const colorContrastViolations = violations.filter(
      v => v.id === 'color-contrast'
    );
    
    expect(colorContrastViolations).toEqual([]);
  });
});
```

### Component A11y Tests

```tsx
// components/ui/Button.a11y.test.tsx
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { Button } from './Button';

expect.extend(toHaveNoViolations);

describe('Button Accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper ARIA attributes', () => {
    const { getByRole } = render(<Button aria-label="Close">X</Button>);
    const button = getByRole('button', { name: 'Close' });
    
    expect(button).toHaveAttribute('aria-label', 'Close');
  });

  it('should be keyboard accessible', () => {
    const { getByRole } = render(<Button>Click me</Button>);
    const button = getByRole('button');
    
    expect(button).toHaveAttribute('tabindex', '0');
  });
});
```

## 📊 Test Coverage

### Coverage Configuration

```javascript
// jest.config.cjs
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/**/*.test.{ts,tsx}',
    '!src/**/*.spec.{ts,tsx}',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  coverageReporters: ['text', 'lcov', 'html', 'json'],
  coverageDirectory: 'coverage',
};
```

### Coverage Analysis

```bash
# Run coverage
pnpm test:coverage

# View coverage report
open coverage/lcov-report/index.html

# Check coverage thresholds
pnpm test:coverage --coverageThreshold
```

## 🚀 Running Tests

### Unit and Integration Tests

```bash
# Run all tests
pnpm test

# Run tests in watch mode
pnpm test:ui

# Run tests with coverage
pnpm test:coverage

# Run specific test file
pnpm test -- Button.test.tsx

# Run tests matching pattern
pnpm test -- --testPathPattern=provider

# Run tests with verbose output
pnpm test -- --verbose
```

### E2E Tests

```bash
# Install Playwright browsers
pnpm playwright install

# Run E2E tests
pnpm test:e2e

# Run E2E tests in headed mode
pnpm test:e2e --headed

# Run specific test
pnpm test:e2e --grep="create a new provider"

# Run tests in debug mode
pnpm test:e2e --debug
```

### Visual Regression Tests

```bash
# Update snapshots
pnpm test:e2e --update-snapshots

# Run visual tests only
pnpm test:e2e --grep="visual"

# Compare snapshots
pnpm test:e2e --grep="should not visually regress"
```

### Accessibility Tests

```bash
# Run a11y tests
pnpm test:e2e --grep="accessibility"

# Run axe tests
pnpm test --grep="a11y"
```

## 📈 Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        node-version: [20.x]

    steps:
    - uses: actions/checkout@v3

    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'pnpm'

    - name: Install dependencies
      run: |
        pnpm install

    - name: Run linting
      run: |
        pnpm lint

    - name: Run type checking
      run: |
        pnpm type-check

    - name: Run unit and integration tests
      run: |
        pnpm test:coverage

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage/lcov.info
        flags: unittests
        name: codecov-umbrella

  e2e:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Use Node.js 20.x
      uses: actions/setup-node@v3
      with:
        node-version: 20.x
        cache: 'pnpm'

    - name: Install dependencies
      run: |
        pnpm install

    - name: Install Playwright browsers
      run: |
        pnpm playwright install

    - name: Run E2E tests
      run: |
        pnpm test:e2e

    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: failure()
      with:
        name: test-results
        path: |
          test-results/
          playwright-report/

  visual:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Use Node.js 20.x
      uses: actions/setup-node@v3
      with:
        node-version: 20.x
        cache: 'pnpm'

    - name: Install dependencies
      run: |
        pnpm install

    - name: Install Playwright browsers
      run: |
        pnpm playwright install

    - name: Run visual regression tests
      run: |
        pnpm test:e2e --grep="visual"

    - name: Upload visual test results
      uses: actions/upload-artifact@v3
      if: failure()
      with:
        name: visual-test-results
        path: |
          test-results/
          playwright-report/
```

## 📚 Best Practices

### 1. Test Organization

- **Co-locate tests** with components (e.g., `Button.tsx` and `Button.test.tsx`)
- **Use descriptive test names** that explain the scenario
- **Group related tests** using `describe` blocks
- **Follow AAA pattern**: Arrange, Act, Assert

### 2. Test Data

- **Use factories** for creating test data
- **Avoid hardcoded IDs** and use meaningful names
- **Test edge cases** and error conditions
- **Keep test data minimal** and focused

### 3. Mocking

- **Mock external dependencies** (API calls, third-party libraries)
- **Avoid over-mocking** - test real behavior when possible
- **Use proper mock cleanup** to avoid test pollution
- **Test both mocked and real scenarios**

### 4. Performance

- **Keep tests fast** - avoid unnecessary delays
- **Use parallel execution** when possible
- **Optimize E2E tests** with proper waiting strategies
- **Cache dependencies** in CI/CD

### 5. Maintenance

- **Update tests** when refactoring code
- **Remove obsolete tests** that no longer provide value
- **Review test coverage** regularly
- **Fix flaky tests** immediately

## 🔗 Additional Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library Documentation](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Storybook Testing](https://storybook.js.org/docs/writing-tests/introduction)
- [jest-axe Documentation](https://github.com/nickcolley/jest-axe)
- [Testing Library Jest DOM](https://github.com/testing-library/jest-dom)
