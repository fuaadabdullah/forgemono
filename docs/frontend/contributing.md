# Contributing Guidelines

Thank you for your interest in contributing to the GoblinOS Assistant frontend! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Community Guidelines](#community-guidelines)

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js**: Version 20.0.0 or higher
- **pnpm**: Version 9.0.0 or higher
- **Git**: Version 2.30 or higher
- **TypeScript**: Version 5.7 or higher (global installation recommended)

### Setup

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/forgemono.git
   cd forgemono
   ```
3. **Install dependencies**:
   ```bash
   pnpm install
   ```
4. **Navigate to frontend**:
   ```bash
   cd apps/goblin-assistant
   ```
5. **Copy environment file**:
   ```bash
   cp .env.example .env.local
   ```
6. **Start development server**:
   ```bash
   pnpm dev
   ```

### Backend Setup

For full functionality, you'll need the backend running:

```bash
cd apps/goblin-assistant/backend
source .venv/bin/activate  # Or your preferred method
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## 🔄 Development Workflow

### Branch Naming

Use descriptive branch names with the following format:

```
type/issue-number-description
```

**Examples:**
- `feat/123-add-dark-mode-toggle`
- `fix/456-resolve-api-error`
- `docs/update-contribution-guide`
- `chore/refactor-component-structure`

**Type prefixes:**
- `feat` - New features
- `fix` - Bug fixes
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks
- `perf` - Performance improvements

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Examples:**
```bash
git commit -m "feat(auth): add OAuth2 integration

- Implement OAuth2 client
- Add login/logout functionality
- Update authentication store

Closes #123"
```

```bash
git commit -m "fix(api): resolve CORS issues

- Add proper CORS headers
- Update API client configuration

Fixes #456"
```

**Commit types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

## 🎨 Code Style

### TypeScript/JavaScript Guidelines

#### Naming Conventions

- **Variables & Functions**: `camelCase`
  ```typescript
  const userName = 'John';
  function getUserData() {}
  ```

- **Constants**: `UPPER_SNAKE_CASE`
  ```typescript
  const MAX_RETRY_ATTEMPTS = 3;
  ```

- **Classes & Interfaces**: `PascalCase`
  ```typescript
  interface UserData {}
  class UserService {}
  ```

- **Files**: `kebab-case` for components, `camelCase` for utilities
  ```bash
  # Components
  user-profile.tsx
  button.component.tsx
  
  # Utilities
  formatDate.ts
  apiClient.ts
  ```

#### TypeScript Best Practices

```typescript
// ✅ Good: Explicit types
interface User {
  id: string;
  name: string;
  email: string;
}

const createUser = (userData: User): User => {
  return { ...userData, id: generateId() };
};

// ❌ Avoid: Any types
const data: any = fetchData();

// ✅ Good: Proper typing
const data: ApiResponse<User[]> = await fetchUsers();
```

#### Component Guidelines

```tsx
// ✅ Good: Functional component with TypeScript
interface UserProfileProps {
  user: User;
  onEdit: (user: User) => void;
  isLoading?: boolean;
}

const UserProfile: React.FC<UserProfileProps> = ({ 
  user, 
  onEdit, 
  isLoading = false 
}) => {
  // Component logic
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  );
};
```

#### Commenting Guidelines

```typescript
/**
 * Fetches user data from the API
 * 
 * @param userId - The unique identifier for the user
 * @returns Promise resolving to user data
 * @throws Error if user is not found
 */
const fetchUserData = async (userId: string): Promise<User> => {
  // Implementation
};
```

### React Guidelines

#### Hooks Usage

```tsx
// ✅ Good: Proper hook usage
const UserProfile = ({ userId }: { userId: string }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    const loadUser = async () => {
      setLoading(true);
      try {
        const userData = await fetchUser(userId);
        setUser(userData);
      } catch (error) {
        console.error('Failed to load user:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadUser();
  }, [userId]);
  
  // Component render
};
```

#### State Management

- **Local State**: Use `useState` and `useReducer` for component-specific state
- **Global State**: Use Zustand for shared application state
- **Server State**: Use React Query for API data and caching

```typescript
// Zustand store example
interface UserState {
  users: User[];
  loading: boolean;
  fetchUsers: () => Promise<void>;
  addUser: (user: User) => void;
}

const useUserStore = create<UserState>((set) => ({
  users: [],
  loading: false,
  fetchUsers: async () => {
    set({ loading: true });
    const users = await apiClient.getUsers();
    set({ users, loading: false });
  },
  addUser: (user) => set((state) => ({ users: [...state.users, user] })),
}));
```

### Styling Guidelines

#### Tailwind CSS

```tsx
// ✅ Good: Semantic class organization
const Button = ({ variant = 'primary' }) => {
  const baseClasses = 'px-4 py-2 rounded font-medium transition-colors';
  
  const variantClasses = {
    primary: 'bg-blue-500 hover:bg-blue-600 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    danger: 'bg-red-500 hover:bg-red-600 text-white',
  };
  
  return (
    <button className={`${baseClasses} ${variantClasses[variant]}`}>
      Click me
    </button>
  );
};
```

#### Component Styling

- **Base Components**: Use Tailwind classes directly
- **Complex Components**: Extract styles to CSS-in-JS or CSS modules
- **Global Styles**: Add to `globals.css` with clear comments

## 🧪 Testing

### Test Structure

```
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   ├── Button.stories.tsx
│   │   └── index.ts
│   └── __tests__/
├── hooks/
│   ├── useAuth/
│   │   ├── useAuth.ts
│   │   └── useAuth.test.tsx
└── __tests__/
```

### Writing Tests

#### Unit Tests

```tsx
// Button.test.tsx
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
});
```

#### Integration Tests

```tsx
// UserProfile.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UserProfile } from './UserProfile';

describe('UserProfile Integration', () => {
  const queryClient = new QueryClient();

  it('displays user information', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <UserProfile userId="123" />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });
});
```

#### E2E Tests

```typescript
// e2e/user-flow.spec.ts
import { test, expect } from '@playwright/test';

test('user can create and edit a provider', async ({ page }) => {
  await page.goto('/providers');
  
  await page.click('[data-testid="create-provider-button"]');
  
  await page.fill('[data-testid="provider-name-input"]', 'Test Provider');
  await page.selectOption('[data-testid="provider-type-select"]', 'openai');
  await page.fill('[data-testid="provider-api-key-input"]', 'test-key');
  
  await page.click('[data-testid="save-provider-button"]');
  
  await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  await expect(page.locator('[data-testid="provider-list"]')).toContainText('Test Provider');
});
```

### Test Coverage

- **Minimum 80%** code coverage required
- **Critical paths** must be fully tested
- **Accessibility tests** for all components
- **Performance benchmarks** for key operations

```bash
# Run tests with coverage
pnpm test:coverage

# View coverage report
open coverage/lcov-report/index.html
```

## 📚 Documentation

### Code Documentation

#### JSDoc Comments

```typescript
/**
 * Creates a new user in the system
 * 
 * @param userData - User data object containing name and email
 * @param options - Optional configuration for user creation
 * @param options.sendWelcomeEmail - Whether to send a welcome email
 * @returns Promise resolving to the created user
 * 
 * @example
 * ```typescript
 * const newUser = await createUser(
 *   { name: 'John Doe', email: 'john@example.com' },
 *   { sendWelcomeEmail: true }
 * );
 * ```
 */
const createUser = async (
  userData: { name: string; email: string },
  options: { sendWelcomeEmail?: boolean } = {}
): Promise<User> => {
  // Implementation
};
```

#### Component Documentation

```tsx
/**
 * UserProfile Component
 * 
 * Displays user information and provides editing capabilities.
 * 
 * @param props - Component props
 * @param props.user - User object to display
 * @param props.onEdit - Callback function when user clicks edit
 * @param props.loading - Loading state indicator
 * 
 * @example
 * ```tsx
 * <UserProfile 
 *   user={{ id: '1', name: 'John Doe', email: 'john@example.com' }}
 *   onEdit={handleEdit}
 *   loading={false}
 * />
 * ```
 */
const UserProfile: React.FC<UserProfileProps> = ({ user, onEdit, loading }) => {
  // Component implementation
};
```

### README Documentation

Each major component or feature should have a README file:

```markdown
# Component Name

Brief description of what this component does.

## Features

- Feature 1
- Feature 2
- Feature 3

## Usage

```tsx
<ComponentName prop1="value" />
```

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| prop1 | string | Yes | Description of prop1 |
| prop2 | boolean | No | Description of prop2 |

## Examples

See `examples/` directory for more usage examples.

## Testing

Run tests with:
```bash
pnpm test -- ComponentName
```

## Accessibility

This component follows WCAG 2.1 AA guidelines.
```

## 📝 Pull Request Process

### Before Creating a PR

1. **Ensure all tests pass**:
   ```bash
   pnpm test
   pnpm test:coverage
   ```

2. **Check linting and formatting**:
   ```bash
   pnpm lint
   pnpm format
   ```

3. **Verify build**:
   ```bash
   pnpm build
   ```

4. **Documentation Review** - Critical Step:
   - [ ] **Code Documentation**: All new code has appropriate JSDoc comments
   - [ ] **README Updates**: Component READMEs updated if applicable
   - [ ] **API Documentation**: API changes documented in `docs/frontend/api-integration.md`
   - [ ] **Breaking Changes**: Breaking changes documented in `CHANGELOG.md`
   - [ ] **Examples**: New features include usage examples
   - [ ] **Accessibility**: Accessibility considerations documented in `docs/frontend/accessibility.md`

5. **Documentation Review Checklist**:
   ```markdown
   ## Documentation Review Checklist
   - [ ] Code is self-documenting with clear variable/function names
   - [ ] Complex logic includes inline comments explaining "why"
   - [ ] New components have JSDoc with @param, @returns, and @example
   - [ ] Public APIs are documented with usage examples
   - [ ] Breaking changes are clearly marked and explained
   - [ ] README files are updated for affected components/features
   - [ ] Accessibility implications are documented
   - [ ] Performance considerations are noted if applicable
   ```

6. **Documentation Review Process**:
   - **For Major Features**: Create a draft documentation PR first
   - **For API Changes**: Update API documentation before code changes
   - **For Components**: Ensure Storybook stories are updated
   - **For Breaking Changes**: Document migration path

7. **Squash commits** (if appropriate):
   ```bash
   git rebase -i HEAD~n  # where n is the number of commits
   ```

### Creating a PR

1. **Push to your fork**:
   ```bash
   git push origin your-branch-name
   ```

2. **Create PR on GitHub** with the following template:

```markdown
## Summary
Brief description of the changes (1-3 sentences)

## Test plan
- [ ] All existing tests pass
- [ ] New functionality tested
- [ ] Edge cases covered
- [ ] No regressions introduced

## Documentation
- [ ] Code is commented and self-documenting
- [ ] README updated (if applicable)
- [ ] API documentation updated (if applicable)

## Screenshots (if applicable)
Before:
![before](url)

After:
![after](url)

## Additional notes
Any additional information, context, or considerations
```

### PR Review Process

1. **Automated Checks**: All CI/CD checks must pass
2. **Code Review**: At least one maintainer approval required
3. **Testing**: All tests must pass
4. **Documentation**: Ensure documentation is up-to-date

### After PR Merge

1. **Update your local repository**:
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Delete feature branch**:
   ```bash
   git branch -d your-branch-name
   git push origin --delete your-branch-name
   ```

## 🐛 Issue Reporting

### Before Reporting

1. **Check existing issues** - Your issue might already be reported
2. **Update to latest version** - Ensure you're using the most recent code
3. **Search documentation** - The answer might be in our docs

### Creating an Issue

Use the appropriate issue template:

#### Bug Report

```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment info**
- OS: [e.g. macOS, Windows, Linux]
- Browser [e.g. chrome, safari]
- Version [e.g. 22]
- Node.js version
- pnpm version

**Additional context**
Add any other context about the problem here.

**Reproduction repository (if applicable)**
Link to a minimal reproduction
```

#### Feature Request

```markdown
**Is your feature request related to a problem?**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
```

## 🤝 Community Guidelines

### Code of Conduct

We expect all contributors to:

- **Be respectful** - Treat others with kindness and respect
- **Be inclusive** - Welcome people of all backgrounds and skill levels
- **Be constructive** - Provide helpful feedback and suggestions
- **Be patient** - Understand that people have different experience levels
- **Be collaborative** - Work together to find the best solutions

### Communication

- **GitHub Issues**: For bug reports and feature requests
- **Pull Requests**: For code contributions and discussions
- **Discussions**: For questions and community discussions

### Getting Help

- **Documentation**: Check our docs first
- **Issues**: Search existing issues
- **Community**: Join our Discord/Slack for real-time help
- **Mentors**: Reach out to experienced contributors

### Recognition

We appreciate and recognize contributions through:

- **GitHub contributions** - Your commits will be visible
- **Release notes** - Major contributions mentioned in releases
- **Thank you messages** - We'll acknowledge your help
- **Mentorship opportunities** - For experienced contributors

## 📖 Additional Resources

### Learning Materials

- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React Documentation](https://react.dev/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Testing Library](https://testing-library.com/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)

### Tools and Extensions

**VS Code Extensions:**
- ESLint
- Prettier
- TypeScript Importer
- GitLens
- Thunder Client (for API testing)

**Development Tools:**
- [GitKraken](https://www.gitkraken.com/) - Git GUI
- [Postman](https://www.postman.com/) - API testing
- [Chrome DevTools](https://developer.chrome.com/docs/devtools/) - Browser debugging

### Contributing to Open Source

- [First Contributions](https://github.com/firstcontributions/first-contributions)
- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)

## 📞 Contact

If you have questions or need help:

- **GitHub Discussions**: For community discussions
- **Issue Tracker**: For bug reports and feature requests
- **Email**: Contact the maintainers directly

---

**Thank you for contributing to GoblinOS Assistant!** 🎉

Your contributions help make this project better for everyone.
