# Testing Library Migration Tools

This directory contains automated tools for migrating React tests from Enzyme to Testing Library.

## Available Tools

### 1. Turbo Migrate (`scripts/turbo-migrate.js`)

A fast, pattern-based migration script that automatically converts common Enzyme patterns to Testing Library.

**Usage:**

```bash
# Basic migration
npm run migrate:enzyme-turbo ./src

# With custom options
node scripts/turbo-migrate.js ./src --verbose --report
```

**Features:**

- ⚡ Fast pattern-based migrations
- 🔍 Automatic Enzyme detection
- 📊 JSON report generation
- 🛡️ Safe - only processes files with Enzyme imports

### 2. Migration Toolkit (`tools/migrate-tests.js`)

A comprehensive migration toolkit with advanced analysis and HTML reporting.

**Usage:**

```bash
# Basic migration
npm run migrate:enzyme-toolkit

# Dry run (safe preview)
npm run migrate:enzyme-dry-run

# Custom options
node tools/migrate-tests.js --src ./tests --output ./report.html --verbose
```

**Features:**

- 📈 File complexity analysis
- 🎨 HTML report generation
- 🔧 Pattern application with error handling
- 🧪 Dry-run mode for safe testing

### 3. Parallel Migration by Type (`scripts/migrate-by-type.js`)

Intelligent migration planning based on test complexity and type.

**Usage:**

```bash
# Analyze migration plan
npm run migrate:by-type -- --dry-run

# Migrate specific types
npm run migrate:by-type -- --focus-type utils
npm run migrate:by-type -- --focus-type hooks

# Batch migration with confirmation
npm run migrate:by-type -- --batch-size 3
```

**Migration Order:**

1. **Utils** (Priority 1) - 5min each - Pure functions, no React
2. **Hooks** (Priority 2) - 10min each - Custom hooks, state management
3. **Presentational** (Priority 3) - 15min each - UI components, no complex logic
4. **Container** (Priority 4) - 30min each - State, effects, API calls
5. **Pages** (Priority 5) - 45min each - Page-level components
6. **Integration** (Priority 6) - 60min each - Multi-component workflows

### 4. Component Complexity Analyzer (`scripts/analyze-react-components.js`)

Analyze React component complexity before migration planning.

**Usage:**

```bash
# JSON report
npm run analyze:components

# CSV export
npm run analyze:components-csv
```

**Complexity Categories:**

- **Simple**: Props in, JSX out (easy migration)
- **Medium**: Some state, basic hooks
- **Complex**: Multiple contexts, side effects
- **Monster**: 500+ lines, many dependencies

### 5. VS Code Snippets (`.vscode/migration-snippets.code-snippets`)

Pre-built code snippets for quick Enzyme to Testing Library conversions.

**Available Snippets:**

- `etl` - Complete test conversion template
- `tl-setup` - Testing Library test setup
- `tl-queries` - Common query patterns
- `enzyme-migrate` - Side-by-side migration examples

## Quick Start

1. **Install dependencies:**

   ```bash
   npm install --save-dev glob
   ```

2. **Run turbo migration:**

   ```bash
   npm run migrate:enzyme-turbo
   ```

3. **Review changes and run tests:**

   ```bash
   npm test
   ```

4. **Generate detailed report (optional):**
   ```bash
   npm run migrate:enzyme-toolkit
   ```

## Migration Patterns

The tools automatically handle these common patterns:

### Imports

```javascript
// Before
import { shallow, mount } from 'enzyme';

// After
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
```

### Rendering

```javascript
// Before
const wrapper = shallow(<Component />);

// After
render(<Component />);
```

### Queries

```javascript
// Before
const button = wrapper.find('button');

// After
const button = screen.getByRole('button');
```

### Interactions

```javascript
// Before
button.simulate('click');

// After
await user.click(button);
```

## Manual Migration

For complex patterns not handled automatically, refer to:

- `docs/ENZYME_TO_TESTING_LIBRARY_MIGRATION.md` - Complete migration guide
- Testing Library documentation: https://testing-library.com/

## Troubleshooting

### Common Issues

1. **"glob is not installed"**

   ```bash
   npm install --save-dev glob
   ```

2. **Tests failing after migration**
   - Check that all user interactions use `await`
   - Verify element queries match accessible roles
   - Add `userEvent.setup()` for user interaction tests

3. **Complex Enzyme patterns not migrated**
   - Use the manual migration guide
   - Consider VS Code snippets for complex conversions

### Getting Help

- 📖 [Migration Guide](../docs/ENZYME_TO_TESTING_LIBRARY_MIGRATION.md)
- 🧪 [Testing Library Docs](https://testing-library.com/)
- 💬 Check existing migrated test files for patterns

## Contributing

When adding new migration patterns:

1. Update the `MIGRATION_TEMPLATES.patterns` array in the respective tool
2. Add test cases for the new pattern
3. Update the migration documentation
4. Test on a variety of Enzyme test files
