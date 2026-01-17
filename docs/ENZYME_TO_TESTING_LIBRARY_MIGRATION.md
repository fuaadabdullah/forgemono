---
title: "ENZYME TO TESTING LIBRARY MIGRATION"
description: "Enzyme to Testing Library Migration Guide"
---

# Enzyme to Testing Library Migration Guide

This guide provides comprehensive strategies for migrating React component tests from Enzyme to Testing Library, including automated tools and best practices.

## Table of Contents

1. [Automated Code Mods (Codemods)](#automated-code-mods-codemods)
2. [Batch Migration Scripts](#batch-migration-scripts)
3. [AI-Powered Migration (VS Code + GPT)](#ai-powered-migration-vs-code--gpt)
4. [Pre-built Migration Packages](#pre-built-migration-packages)
5. [Manual Migration Patterns](#manual-migration-patterns)
6. [Testing Best Practices](#testing-best-practices)

## Smart Migration Strategies

### Strategy 1: Parallel Migration by Test Type

The `scripts/migrate-by-type.js` script enables intelligent parallel migration based on test complexity and type:

```bash
# Analyze and plan migration by test type
npm run migrate:by-type -- --dry-run

# Migrate specific test types
npm run migrate:by-type -- --focus-type utils
npm run migrate:by-type -- --focus-type hooks

# Migrate in batches with confirmation
npm run migrate:by-type -- --batch-size 3
```

**Migration Order by Priority:**

1. **Utils** (Priority 1) - Pure functions, no React - 5min each
2. **Hooks** (Priority 2) - Custom hooks, state management - 10min each
3. **Presentational** (Priority 3) - UI components, no complex logic - 15min each
4. **Container** (Priority 4) - State, effects, API calls - 30min each
5. **Pages** (Priority 5) - Page-level components - 45min each
6. **Integration** (Priority 6) - Multi-component workflows - 60min each

### Strategy 2: Component Classification

Analyze component complexity before migration:

```bash
# Generate JSON complexity report
npm run analyze:components

# Generate CSV report for analysis
npm run analyze:components-csv
```

**Complexity Categories:**

- **Simple**: Props in, JSX out (easy migration)
- **Medium**: Some state, basic hooks
- **Complex**: Multiple contexts, side effects
- **Monster**: 500+ lines, many dependencies

### Strategy 3: Fast Migration Templates

Cookie-cutter patterns for common component types:

#### Button Component (1-minute migration):

**Before (Enzyme):**

```javascript
import { shallow } from 'enzyme';
import Button from './Button';

test('click', () => {
  const onClick = jest.fn();
  const wrapper = shallow(<Button onClick={onClick} />);
  wrapper.find('button').simulate('click');
  expect(onClick).toHaveBeenCalled();
});
```

**After (Testing Library):**

```javascript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

test('calls onClick when clicked', async () => {
  const user = userEvent.setup();
  const onClick = jest.fn();

  render(<Button onClick={onClick}>Click me</Button>);

  const button = screen.getByRole('button', { name: /click me/i });
  await user.click(button);

  expect(onClick).toHaveBeenCalled();
});
```

#### VS Code Snippets for Fast Migration

Use these snippets in VS Code for instant migration patterns:

- `migrate-button` - Button component migration
- `migrate-input` - Input component migration
- `migrate-form` - Form component migration
- `migrate-hook` - Hook-based component migration
- `migrate-async` - Async component migration

## Automated Code Mods (Codemods)

### Installation

```bash
# Install migration tools
npm install --save-dev @testing-library/react-codemod jest-codemods
```

### Automated Migrations

```bash
# Run automated migrations
npx react-codemod rename-unsafe-lifecycles
npx react-codemod update-react-imports
npx jscodemod --parser tsx -t jest-codemods/transforms/enzyme-to-testing-library.js <your-test-files>

# For specific patterns
npx @testing-library/react-codemod --force enzyme-to-testing-library ./src
```

## Batch Migration Scripts

### Turbo Migrate Script

The `scripts/turbo-migrate.js` script provides automated pattern-based migrations:

````bash
# Run turbo migration on src directory
node scripts/turbo-migrate.js ./src

# Run with verbose output
node scripts/turbo-migrate.js ./src --verbose

# Generate migration report
node scripts/turbo-migrate.js ./src --report migration-report.json

**Features:**

- Pattern-based automatic migrations
- Enzyme import detection and conversion
- UserEvent setup injection
- Migration report generation
- Dry-run capability

### Migration Toolkit

The comprehensive `tools/migrate-tests.js` toolkit offers advanced migration features:

```bash
# Basic migration
node tools/migrate-tests.js

# Dry run to preview changes
node tools/migrate-tests.js --dry-run

# Verbose output with detailed analysis
node tools/migrate-tests.js --verbose

# Custom source directory
node tools/migrate-tests.js --src ./tests

# Generate HTML report
node tools/migrate-tests.js --output ./migration-report.html

**Features:**

- File analysis and complexity assessment
- Automated pattern application
- HTML report generation
- Error handling and recovery
- Dry-run mode for safe preview

## AI-Powered Migration (VS Code + GPT)

### VS Code Snippets

Install the migration snippets from `.vscode/migration-snippets.code-snippets`:

**`etl` - Enzyme to Testing Library conversion:**
```typescript
// Migrate from:
// const wrapper = shallow(<Component />);
// wrapper.find('button').simulate('click');
//
// To:
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('${1:test name}', async () => {
  const user = userEvent.setup();
  render(<Component />);
  const button = screen.getByRole('button', { name: /${2:button text}/i });
  await user.click(button);
  ${3:// expectations}
});
````

**`tl-setup` - Testing Library test setup:**

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

describe('${1:ComponentName}', () => {
  test('${2:test description}', async () => {
    const user = userEvent.setup();
    ${3:// test implementation}
  });
});
```

**`tl-queries` - Common Testing Library queries:**

```typescript
// Common queries:
const button = screen.getByRole('button', { name: /${1:button text}/i });
const input = screen.getByRole('textbox', { name: /${2:label text}/i });
const link = screen.getByRole('link', { name: /${3:link text}/i });
const heading = screen.getByRole('heading', { name: /${4:heading text}/i });

// Alternative queries:
// const element = screen.getByText(/${5:text}/i);
// const element = screen.getByTestId('${6:test-id}');

// User interactions:
await user.click(button);
await user.type(input, '${7:input value}');
await user.clear(input);
```

## Pre-built Migration Packages

### Ready-to-use Migration Scripts

```bash
# 1. Install migration toolkit
npm install --save-dev @skovy/jest-enzyme-transformer testing-library-migration-helper

# 2. Run with automatic fixes
npx migrate-tests --src ./src --transform enzyme-to-testing-library --write

# 3. Generate migration report
npx test-migration-analyzer --output ./migration-report.html
```

## Manual Migration Patterns

### Before/After Examples

#### Basic Component Rendering

**Before (Enzyme):**

```javascript
import { shallow } from 'enzyme';

describe('MyComponent', () => {
  it('renders correctly', () => {
    const wrapper = shallow(<MyComponent />);
    expect(wrapper.exists()).toBe(true);
  });
});
```

**After (Testing Library):**

```javascript
import { render, screen } from '@testing-library/react';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByRole('generic')).toBeInTheDocument();
  });
});
```

#### Finding Elements

**Before (Enzyme):**

```javascript
const wrapper = shallow(<MyComponent />);
const button = wrapper.find('button');
const input = wrapper.find('input');
```

**After (Testing Library):**

```javascript
render(<MyComponent />);
const button = screen.getByRole('button');
const input = screen.getByRole('textbox');
```

#### User Interactions

**Before (Enzyme):**

```javascript
const wrapper = shallow(<MyComponent />);
const button = wrapper.find('button');
button.simulate('click');

const input = wrapper.find('input');
input.simulate('change', { target: { value: 'new value' } });
```

**After (Testing Library):**

```javascript
const user = userEvent.setup();
render(<MyComponent />);

const button = screen.getByRole('button');
await user.click(button);

const input = screen.getByRole('textbox');
await user.type(input, 'new value');
```

#### Assertions

**Before (Enzyme):**

```javascript
expect(wrapper.text()).toContain('Hello World');
expect(wrapper.find('.error')).toHaveLength(1);
expect(wrapper.prop('disabled')).toBe(true);
```

**After (Testing Library):**

```javascript
expect(screen.getByText('Hello World')).toBeInTheDocument();
expect(screen.getByText(/error/i)).toBeInTheDocument();
expect(button).toBeDisabled();
```

## Testing Best Practices

### Testing Library Principles

1. **Test user behavior, not implementation details**
2. **Query elements the way users interact with them**
3. **Write maintainable tests that don't break with refactoring**

### Common Patterns

#### Testing User Interactions

```typescript
test('allows user to submit form', async () => {
  const user = userEvent.setup();
  const handleSubmit = jest.fn();

  render(<ContactForm onSubmit={handleSubmit} />);

  await user.type(screen.getByLabelText(/name/i), 'John Doe');
  await user.type(screen.getByLabelText(/email/i), 'john@example.com');
  await user.click(screen.getByRole('button', { name: /submit/i }));

  expect(handleSubmit).toHaveBeenCalledWith({
    name: 'John Doe',
    email: 'john@example.com'
  });
});
```

#### Testing Async Behavior

```typescript
test('loads data asynchronously', async () => {
  render(<AsyncComponent />);

  expect(screen.getByText(/loading/i)).toBeInTheDocument();

  await waitFor(() => {
    expect(screen.getByText('Data loaded')).toBeInTheDocument();
  });
});
```

#### Testing Accessibility

```typescript
test('is accessible', async () => {
  const { container } = render(<AccessibleComponent />);
  expect(await axe(container)).toHaveNoViolations();
});
```

### Migration Checklist

- [ ] Replace Enzyme imports with Testing Library imports
- [ ] Convert `shallow`/`mount` to `render`
- [ ] Replace `wrapper.find()` with `screen.getBy*` queries
- [ ] Convert `simulate()` calls to `userEvent` actions
- [ ] Update assertions to use Testing Library matchers
- [ ] Add `userEvent.setup()` for user interaction tests
- [ ] Run tests and fix any failures
- [ ] Consider adding `@testing-library/jest-dom` for additional matchers

### Tools and Resources

- **Testing Library Documentation**: https://testing-library.com/
- **Migration Guide**: https://testing-library.com/docs/react-testing-library/migrate-from-enzyme/
- **Cheat Sheet**: https://testing-library.com/docs/react-testing-library/cheatsheet/
- **VS Code Extension**: Testing Library Snippets

### Troubleshooting

**Common Issues:**

1. **Test timeouts**: Add `await` to user interactions
2. **Element not found**: Use more specific queries or `waitFor`
3. **Async assertions**: Use `waitFor` or `findBy*` queries
4. **Custom matchers**: Install `@testing-library/jest-dom`

**Debugging Tips:**

```javascript
// Debug current DOM state
screen.debug();

// Log available roles
console.log(screen.getAllByRole('button'));

// Wait for element to appear
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});
```

This migration guide provides both automated tools and manual patterns to help you transition from Enzyme to Testing Library effectively. The automated scripts can handle most common patterns, while the manual examples help with complex cases.
