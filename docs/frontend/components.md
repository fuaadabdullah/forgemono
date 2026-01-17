# Component Library

This document describes the UI component library and design system used in the GoblinOS Assistant frontend application.

## 🎨 Design System Overview

Our design system is built on **Tailwind CSS** with **Radix UI** primitives, providing a consistent and accessible foundation for all UI components.

### Design Principles

- **Consistency**: Uniform look and feel across all components
- **Accessibility**: WCAG 2.1 AA compliance out of the box
- **Flexibility**: Highly customizable while maintaining consistency
- **Performance**: Optimized for fast rendering and small bundle size
- **Type Safety**: Full TypeScript support with strict typing

### Color Palette

```typescript
// Primary Colors
const colors = {
  primary: {
    50: '#eff6ff',
    500: '#3b82f6',  // Main brand color
    600: '#2563eb',
    700: '#1d4ed8',
  },
  
  // Semantic Colors
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',
  
  // Neutral Colors
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  }
};
```

### Typography Scale

```typescript
// Font Sizes and Line Heights
const typography = {
  xs: '0.75rem/1rem',    // 12px/16px
  sm: '0.875rem/1.25rem', // 14px/20px
  base: '1rem/1.5rem',    // 16px/24px
  lg: '1.125rem/1.75rem', // 18px/28px
  xl: '1.25rem/1.75rem',  // 20px/28px
  '2xl': '1.5rem/2rem',   // 24px/32px
};
```

### Spacing Scale

```typescript
// Spacing using Tailwind scale
const spacing = {
  xs: '0.25rem',  // 4px
  sm: '0.5rem',   // 8px
  md: '1rem',     // 16px
  lg: '1.5rem',   // 24px
  xl: '2rem',     // 32px
  '2xl': '3rem',  // 48px
  '3xl': '4rem',  // 64px
};
```

## 🧩 Component Architecture

### Atomic Design Structure

We follow the atomic design methodology:

1. **Atoms** - Basic building blocks (`components/ui/`)
2. **Molecules** - Simple component combinations
3. **Organisms** - Complex component combinations
4. **Templates** - Page layouts
5. **Pages** - Complete page implementations

### Component Organization

```
components/
├── ui/                    # Atoms - Base components
│   ├── Button.tsx        # Primary button component
│   ├── Input.tsx         # Form input component
│   ├── Badge.tsx         # Status badge component
│   ├── Modal.tsx         # Modal dialog
│   └── index.ts          # Barrel export
├── layout/               # Layout components
│   ├── Header.tsx        # App header
│   ├── Sidebar.tsx       # Navigation sidebar
│   └── Layout.tsx        # Main layout wrapper
├── dashboard/            # Dashboard-specific components
│   ├── DashboardCard.tsx # Dashboard card component
│   ├── StatCard.tsx      # Statistics card
│   └── QuickActions.tsx  # Quick action buttons
└── shared/               # Shared composite components
    ├── FormField.tsx     # Form field wrapper
    ├── DataTable.tsx     # Data table component
    └── LoadingSpinner.tsx # Loading indicator
```

## 🔘 Base Components (UI)

### Button Component

The Button component is our primary interactive element with multiple variants and sizes.

```tsx
// Usage Examples
import { Button } from '@/components/ui/Button';

// Basic usage
<Button>Click me</Button>

// Variants
<Button variant="primary">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="danger">Danger</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>

// States
<Button disabled>Disabled</Button>
<Button loading>Loading</Button>

// With icons
<Button startIcon={<SaveIcon />}>Save</Button>
<Button endIcon={<ArrowRightIcon />}>Next</Button>
```

**Props Interface:**

```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
}
```

### Input Component

The Input component provides a flexible form input with validation states.

```tsx
// Usage Examples
import { Input } from '@/components/ui/Input';

// Basic usage
<Input placeholder="Enter your name" />

// With label
<Input 
  label="Email Address"
  placeholder="user@example.com"
/>

// With validation
<Input 
  error="This field is required"
  value={value}
  onChange={onChange}
/>

// Different types
<Input type="password" />
<Input type="email" />
<Input type="number" />
```

**Props Interface:**

```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
}
```

### Badge Component

The Badge component displays status indicators and labels.

```tsx
// Usage Examples
import { Badge } from '@/components/ui/Badge';

// Status badges
<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="danger">Error</Badge>
<Badge variant="info">Info</Badge>

// With icons
<Badge variant="primary" icon={<CheckIcon />}>
  Verified
</Badge>
```

**Props Interface:**

```typescript
interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'primary';
  icon?: React.ReactNode;
}
```

### Modal Component

The Modal component provides accessible modal dialogs.

```tsx
// Usage Examples
import { Modal } from '@/components/ui/Modal';

function MyComponent() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setOpen(true)}>Open Modal</Button>
      <Modal open={open} onClose={() => setOpen(false)}>
        <Modal.Header>
          <Modal.Title>Delete Item</Modal.Title>
          <Modal.Description>
            Are you sure you want to delete this item?
          </Modal.Description>
        </Modal.Header>
        <Modal.Content>
          This action cannot be undone.
        </Modal.Content>
        <Modal.Actions>
          <Button variant="ghost" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button variant="danger">Delete</Button>
        </Modal.Actions>
      </Modal>
    </>
  );
}
```

**Props Interface:**

```typescript
interface ModalProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}
```

## 🏗️ Composite Components

### FormField Component

The FormField component wraps inputs with labels, validation, and helper text.

```tsx
// Usage Examples
import { FormField } from '@/components/shared/FormField';

function UserForm() {
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setEmail(value);
    
    if (value && !validateEmail(value)) {
      setEmailError('Please enter a valid email address');
    } else {
      setEmailError('');
    }
  };

  return (
    <FormField
      label="Email Address"
      error={emailError}
      helperText="We'll never share your email with anyone else."
    >
      <Input
        type="email"
        value={email}
        onChange={handleEmailChange}
        placeholder="Enter your email"
      />
    </FormField>
  );
}
```

**Props Interface:**

```typescript
interface FormFieldProps {
  label?: string;
  error?: string;
  helperText?: string;
  children: React.ReactNode;
  required?: boolean;
}
```

### DataTable Component

The DataTable component provides a feature-rich data table with sorting, filtering, and pagination.

```tsx
// Usage Examples
import { DataTable } from '@/components/shared/DataTable';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  status: 'active' | 'inactive' | 'pending';
}

function UsersTable() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);

  const columns = [
    {
      key: 'name',
      title: 'Name',
      sortable: true,
      render: (user: User) => (
        <div className="flex items-center space-x-3">
          <Avatar src={user.avatar} alt={user.name} />
          <span>{user.name}</span>
        </div>
      ),
    },
    {
      key: 'email',
      title: 'Email',
      sortable: true,
    },
    {
      key: 'role',
      title: 'Role',
      sortable: true,
      render: (user: User) => <Badge variant="info">{user.role}</Badge>,
    },
    {
      key: 'status',
      title: 'Status',
      sortable: true,
      render: (user: User) => (
        <Badge 
          variant={user.status === 'active' ? 'success' : 
                  user.status === 'inactive' ? 'warning' : 'neutral'}
        >
          {user.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      title: 'Actions',
      render: (user: User) => (
        <div className="flex space-x-2">
          <Button size="sm" variant="ghost">Edit</Button>
          <Button size="sm" variant="danger">Delete</Button>
        </div>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={users}
      loading={loading}
      onSort={(column, direction) => {
        // Handle sorting
      }}
      onFilter={(filters) => {
        // Handle filtering
      }}
      pagination={{
        total: users.length,
        page: 1,
        pageSize: 10,
        onPageChange: (page) => {
          // Handle page change
        },
      }}
    />
  );
}
```

**Props Interface:**

```typescript
interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[];
  loading?: boolean;
  onSort?: (column: string, direction: 'asc' | 'desc') => void;
  onFilter?: (filters: Record<string, any>) => void;
  pagination?: {
    total: number;
    page: number;
    pageSize: number;
    onPageChange: (page: number) => void;
  };
}

interface DataTableColumn<T> {
  key: string;
  title: string;
  sortable?: boolean;
  render?: (item: T) => React.ReactNode;
}
```

## 🎛️ Layout Components

### Layout Component

The Layout component provides the main application structure.

```tsx
// Usage Examples
import { Layout } from '@/components/layout/Layout';

function App() {
  return (
    <Layout>
      <Layout.Header>
        <Header />
      </Layout.Header>
      <Layout.Sidebar>
        <Sidebar />
      </Layout.Sidebar>
      <Layout.Content>
        <main className="p-6">
          {/* Page content */}
        </main>
      </Layout.Content>
    </Layout>
  );
}
```

**Props Interface:**

```typescript
interface LayoutProps {
  children: React.ReactNode;
  variant?: 'default' | 'sidebar' | 'header';
}
```

### Header Component

The Header component provides the application header with navigation.

```tsx
// Usage Examples
import { Header } from '@/components/layout/Header';

function AppHeader() {
  return (
    <Header>
      <Header.Brand>
        <Logo />
        <span className="ml-2 text-xl font-bold">GoblinOS</span>
      </Header.Brand>
      <Header.Navigation>
        <NavLink href="/dashboard">Dashboard</NavLink>
        <NavLink href="/providers">Providers</NavLink>
        <NavLink href="/settings">Settings</NavLink>
      </Header.Navigation>
      <Header.Actions>
        <ThemeToggle />
        <UserMenu />
      </Header.Actions>
    </Header>
  );
}
```

## 📊 Dashboard Components

### StatCard Component

The StatCard component displays key metrics and statistics.

```tsx
// Usage Examples
import { StatCard } from '@/components/dashboard/StatCard';

function Dashboard() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        title="Total Users"
        value="1,234"
        trend={{ value: 12.5, direction: 'up' }}
        icon={<UsersIcon />}
      />
      <StatCard
        title="Active Sessions"
        value="567"
        trend={{ value: -3.2, direction: 'down' }}
        icon={<ActivityIcon />}
      />
      <StatCard
        title="API Calls"
        value="89,012"
        trend={{ value: 8.7, direction: 'up' }}
        icon={<ApiIcon />}
      />
      <StatCard
        title="Error Rate"
        value="0.5%"
        trend={{ value: -1.2, direction: 'down' }}
        icon={<AlertIcon />}
      />
    </div>
  );
}
```

**Props Interface:**

```typescript
interface StatCardProps {
  title: string;
  value: string | number;
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
  icon?: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}
```

### QuickActions Component

The QuickActions component provides quick access to common operations.

```tsx
// Usage Examples
import { QuickActions } from '@/components/dashboard/QuickActions';

function Dashboard() {
  const actions = [
    {
      title: 'Create Provider',
      description: 'Add a new AI provider',
      icon: <PlusIcon />,
      onClick: () => navigate('/providers/new'),
    },
    {
      title: 'Run Analysis',
      description: 'Start a new analysis',
      icon: <AnalysisIcon />,
      onClick: () => runAnalysis(),
    },
    {
      title: 'View Logs',
      description: 'Check system logs',
      icon: <LogsIcon />,
      onClick: () => navigate('/logs'),
    },
  ];

  return (
    <QuickActions actions={actions} />
  );
}
```

**Props Interface:**

```typescript
interface QuickActionsProps {
  actions: {
    title: string;
    description: string;
    icon: React.ReactNode;
    onClick: () => void;
  }[];
}
```

## 🎨 Custom Hooks

### useTheme Hook

Manage theme state across the application.

```tsx
// Usage Examples
import { useTheme } from '@/hooks/useTheme';

function ThemeToggle() {
  const { theme, setTheme, toggleTheme } = useTheme();

  return (
    <button onClick={toggleTheme}>
      {theme === 'light' ? '🌙' : '☀️'}
    </button>
  );
}
```

**Hook Interface:**

```typescript
interface UseThemeReturn {
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;
}
```

### useForm Hook

Handle form state and validation.

```tsx
// Usage Examples
import { useForm } from '@/hooks/useForm';

function UserForm() {
  const { values, errors, handleChange, handleSubmit, isSubmitting } = useForm({
    initialValues: {
      name: '',
      email: '',
      password: '',
    },
    validationSchema: {
      name: (value) => value.length > 0 || 'Name is required',
      email: (value) => /\S+@\S+\.\S+/.test(value) || 'Invalid email',
      password: (value) => value.length >= 8 || 'Password must be at least 8 characters',
    },
    onSubmit: async (values) => {
      // Handle form submission
      await createUser(values);
    },
  });

  return (
    <form onSubmit={handleSubmit}>
      <FormField
        label="Name"
        error={errors.name}
      >
        <Input
          value={values.name}
          onChange={(e) => handleChange('name', e.target.value)}
          placeholder="Enter your name"
        />
      </FormField>
      
      <FormField
        label="Email"
        error={errors.email}
      >
        <Input
          type="email"
          value={values.email}
          onChange={(e) => handleChange('email', e.target.value)}
          placeholder="Enter your email"
        />
      </FormField>
      
      <FormField
        label="Password"
        error={errors.password}
      >
        <Input
          type="password"
          value={values.password}
          onChange={(e) => handleChange('password', e.target.value)}
          placeholder="Enter your password"
        />
      </FormField>
      
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Creating...' : 'Create User'}
      </Button>
    </form>
  );
}
```

**Hook Interface:**

```typescript
interface UseFormOptions<T> {
  initialValues: T;
  validationSchema: Record<keyof T, (value: any) => boolean | string>;
  onSubmit: (values: T) => Promise<void> | void;
}
```

## 🧪 Testing Components

### Component Testing Guidelines

All components should be tested with the following approach:

1. **Unit Tests**: Test component rendering and basic functionality
2. **Integration Tests**: Test component interactions
3. **Accessibility Tests**: Ensure A11y compliance
4. **Visual Tests**: Verify visual consistency

### Example Component Test

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

  it('shows loading state', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('applies correct variant classes', () => {
    const { container } = render(<Button variant="primary">Click me</Button>);
    expect(container.firstChild).toHaveClass('bg-blue-500');
  });
});
```

### Accessibility Testing

```tsx
// Accessibility test example
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('Button Accessibility', () => {
  it('has no accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

## 📚 Storybook Integration

### Creating Stories

All components should have corresponding Storybook stories:

```tsx
// Button.stories.tsx
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
    startIcon: <SaveIcon />,
    children: 'Save',
  },
};

export const Loading: Story = {
  args: {
    loading: true,
    children: 'Loading',
  },
};
```

### Storybook Configuration

```javascript
// .storybook/main.js
module.exports = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-a11y',
    '@storybook/addon-docs',
  ],
  framework: {
    name: '@storybook/nextjs',
    options: {},
  },
};
```

## 🔧 Component Development Guidelines

### Creating New Components

1. **Follow Naming Conventions**:
   - Use PascalCase for component names
   - Use camelCase for props and functions
   - Use kebab-case for CSS classes

2. **TypeScript First**:
   - Always define TypeScript interfaces
   - Use strict typing for all props
   - Export types for external use

3. **Accessibility**:
   - Use semantic HTML elements
   - Add appropriate ARIA attributes
   - Ensure keyboard navigation
   - Test with screen readers

4. **Performance**:
   - Use memoization for expensive calculations
   - Implement virtualization for long lists
   - Optimize image loading
   - Minimize re-renders

5. **Testing**:
   - Write unit tests for all components
   - Test edge cases and error states
   - Include accessibility tests
   - Add visual regression tests

### Component Documentation

Each component should include:

1. **JSDoc Comments**: Document props and usage
2. **TypeScript Types**: Define all interfaces
3. **Storybook Stories**: Visual documentation
4. **Test Coverage**: Comprehensive test suite
5. **Usage Examples**: Real-world usage patterns

### Example Component Template

```tsx
/**
 * Primary UI component for user interaction
 * 
 * @param {Object} props - Component props
 * @param {string} props.variant - Button variant
 * @param {string} props.size - Button size
 * @param {boolean} props.disabled - Disabled state
 * @param {React.ReactNode} props.children - Button content
 * @param {Function} props.onClick - Click handler
 * 
 * @example
 * <Button variant="primary" onClick={() => console.log('clicked')}>
 *   Click me
 * </Button>
 */
export const Button = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  children,
  onClick,
  ...props
}: ButtonProps) => {
  // Component implementation
};
```

## 🎯 Best Practices

### 1. Composition over Inheritance

```tsx
// ✅ Good: Composition
function Card({ children, className, ...props }: CardProps) {
  return (
    <div className={`card ${className}`} {...props}>
      {children}
    </div>
  );
}

// Usage
<Card>
  <Card.Header>Title</Card.Header>
  <Card.Content>Content</Card.Content>
  <Card.Actions>Actions</Card.Actions>
</Card>
```

### 2. Props Interface Design

```tsx
// ✅ Good: Clear, specific props
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost';
  size: 'sm' | 'md' | 'lg';
  disabled: boolean;
  children: React.ReactNode;
  onClick: () => void;
}

// ❌ Avoid: Generic props
interface BadButtonProps {
  config: any;
  options: Record<string, any>;
}
```

### 3. Error Boundaries

```tsx
// ✅ Good: Error boundary for components
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <h1>Something went wrong.</h1>;
    }

    return this.props.children;
  }
}

// Usage
<ErrorBoundary>
  <MyComponent />
</ErrorBoundary>
```

### 4. Loading States

```tsx
// ✅ Good: Explicit loading states
function DataComponent() {
  const { data, loading, error } = useData();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage error={error} />;
  }

  return <DataList data={data} />;
}
```

## 📖 Additional Resources

- [Radix UI Documentation](https://www.radix-ui.com/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [React Accessibility Guide](https://react.dev/learn/accessibility)
- [Storybook Documentation](https://storybook.js.org/docs)
- [Testing Library Documentation](https://testing-library.com/docs/)
