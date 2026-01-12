# Frontend Setup & Configuration

This guide will help you set up the development environment for the GoblinOS Assistant frontend application.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### Required Tools

- **Node.js**: Version 20.0.0 or higher
- **pnpm**: Version 9.0.0 or higher
- **Git**: Version 2.30 or higher
- **TypeScript**: Version 5.7 or higher (global installation recommended)

### Optional but Recommended

- **Docker**: For containerized development
- **VS Code**: With recommended extensions
- **Git LFS**: For large file handling

### Version Check

Verify your installations:

```bash
node --version    # Should be 20.0.0+
pnpm --version    # Should be 9.0.0+
git --version     # Should be 2.30+
tsc --version     # Should be 5.7+
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/fuaadabdullah/forgemono.git
cd forgemono
```

### 2. Install Dependencies

```bash
# Install monorepo dependencies
pnpm install

# Navigate to the frontend application
cd apps/goblin-assistant

# Install frontend-specific dependencies (if needed)
pnpm install
```

### 3. Environment Configuration

#### Copy Environment Variables

```bash
# Copy the example environment file
cp .env.example .env.local
```

#### Configure Environment Variables

Edit `.env.local` with your configuration:

```env
# Backend API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8000

# Authentication
NEXT_PUBLIC_AUTH_DOMAIN=your-auth-domain.com
NEXT_PUBLIC_AUTH_CLIENT_ID=your-client-id

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_DEBUG_MODE=false

# Third-party Services
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn
NEXT_PUBLIC_SEGMENT_WRITE_KEY=your-segment-key

# Development
NEXT_PUBLIC_API_MOCKING=disabled
```

**Note**: For a complete list of environment variables, see the [Environment Variables Reference](#environment-variables-reference) section.

### 4. Start Development Server

```bash
# Start the development server
pnpm dev

# The application will be available at:
# http://localhost:3000
```

### 5. Run Tests

```bash
# Run all tests
pnpm test

# Run tests with coverage
pnpm test:coverage

# Run tests in watch mode
pnpm test:ui
```

### 6. Build for Production

```bash
# Build the application
pnpm build

# Start production server
pnpm start
```

## 🔧 Detailed Configuration

### Development Environment

#### VS Code Setup

For the best development experience, install these VS Code extensions:

```json
{
  "recommendations": [
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-json",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense",
    "ms-vscode.vscode-eslint",
    "streetsidesoftware.code-spell-checker"
  ]
}
```

#### Editor Configuration

The project includes `.vscode/settings.json` with recommended settings:

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "files.associations": {
    "*.css": "tailwindcss"
  }
}
```

### Backend Integration

#### Local Backend Setup

1. **Start the Backend Server**:

```bash
# In a separate terminal
cd apps/goblin-assistant/backend
source .venv/bin/activate  # Or your preferred method
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

2. **Verify Connection**:

```bash
# Test the API connection
curl http://localhost:8000/api/health
```

#### Docker Setup

For containerized development:

```bash
# Build and run all services
docker-compose up --build

# Or run only the frontend
docker-compose up frontend
```

### Testing Configuration

#### Jest Configuration

The project uses Jest with the following configuration:

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
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

#### Playwright Configuration

For E2E testing:

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30 * 1000,
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    video: 'on-first-retry',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
});
```

### Build Configuration

#### Next.js Configuration

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
  images: {
    domains: ['localhost'],
  },
  env: {
    NEXT_PUBLIC_VERSION: process.env.npm_package_version,
  },
};

module.exports = nextConfig;
```

#### TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES6",
    "lib": ["dom", "dom.iterable", "ES6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

## 🌍 Environment Variables Reference

### Required Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` | `https://api.example.com` |
| `NEXT_PUBLIC_WEBSOCKET_URL` | WebSocket URL for real-time updates | `ws://localhost:8000` | `wss://api.example.com` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NEXT_PUBLIC_AUTH_DOMAIN` | Authentication domain | - | `auth.example.com` |
| `NEXT_PUBLIC_AUTH_CLIENT_ID` | OAuth client ID | - | `your-client-id` |
| `NEXT_PUBLIC_ENABLE_ANALYTICS` | Enable analytics tracking | `false` | `true` |
| `NEXT_PUBLIC_ENABLE_DEBUG_MODE` | Enable debug mode | `false` | `true` |
| `NEXT_PUBLIC_SENTRY_DSN` | Sentry DSN for error tracking | - | `https://...` |
| `NEXT_PUBLIC_SEGMENT_WRITE_KEY` | Segment write key | - | `your-write-key` |
| `NEXT_PUBLIC_API_MOCKING` | Enable API mocking | `disabled` | `enabled` |

### Development Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NEXT_PUBLIC_MSW` | Enable Mock Service Worker | `false` | `true` |
| `NEXT_PUBLIC_STORYBOOK` | Enable Storybook integration | `false` | `true` |
| `NEXT_PUBLIC_VITE_DEBUG` | Enable Vite debug mode | `false` | `true` |

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pnpm test

# Run tests in watch mode
pnpm test:ui

# Run tests with coverage
pnpm test:coverage

# Run specific test file
pnpm test -- --testPathPattern=Button

# Run tests with verbose output
pnpm test -- --verbose
```

### E2E Testing

```bash
# Install Playwright browsers
pnpm playwright install

# Run E2E tests
pnpm test:e2e

# Run E2E tests in headed mode
pnpm test:e2e --headed

# Run specific test
pnpm test:e2e --grep="login"
```

### Visual Regression Testing

```bash
# Start Storybook
pnpm storybook

# Build Storybook
pnpm build-storybook

# Run Chromatic (requires setup)
npx chromatic --project-token=<project-token>
```

## 🔍 Linting & Formatting

### ESLint

```bash
# Run ESLint
pnpm lint

# Fix ESLint errors
pnpm lint:fix

# Check ESLint without fixing
pnpm lint:check
```

### Prettier

```bash
# Format code
pnpm format

# Check formatting
pnpm format:check
```

### Type Checking

```bash
# Run TypeScript type checking
pnpm type-check
```

## 🚀 Deployment

### Vercel Deployment

1. **Install Vercel CLI**:

```bash
npm install -g vercel
```

2. **Deploy to Vercel**:

```bash
# Deploy to preview environment
vercel

# Deploy to production
vercel --prod
```

3. **Environment Variables**:

Set environment variables in Vercel dashboard:
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_AUTH_DOMAIN`
- `NEXT_PUBLIC_AUTH_CLIENT_ID`

### Docker Deployment

```bash
# Build Docker image
docker build -t goblin-assistant-frontend .

# Run Docker container
docker run -p 3000:3000 goblin-assistant-frontend
```

### Static Export

```bash
# Export static site
pnpm export

# Serve exported site
pnpm serve
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Find process using port 3000
lsof -ti:3000

# Kill the process
kill -9 <PID>
```

#### 2. Module Not Found

```bash
# Clear cache and reinstall
rm -rf node_modules .next
pnpm install
```

#### 3. TypeScript Errors

```bash
# Check TypeScript configuration
pnpm type-check

# Clear TypeScript cache
rm -rf .next/tsconfig.tsbuildinfo
```

#### 4. ESLint/TypeScript Conflicts

```bash
# Check for conflicts
pnpm lint
pnpm type-check

# Fix automatically fixable issues
pnpm lint:fix
```

### Getting Help

- **Documentation**: Check this README and project docs
- **Issues**: Search existing GitHub issues
- **Community**: Join our Discord/Slack community
- **Support**: Create a new issue with detailed information

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Jest Testing Framework](https://jestjs.io/docs/getting-started)
- [Playwright E2E Testing](https://playwright.dev/docs/intro)
- [ESLint Configuration](https://eslint.org/docs/user-guide/configuring/)
- [Prettier Formatting](https://prettier.io/docs/en/index.html)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

For detailed contribution guidelines, see [Contributing Guidelines](./contributing.md).
