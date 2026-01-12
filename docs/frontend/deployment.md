# Deployment Guide

This document describes the deployment process, build configuration, and production setup for the GoblinOS Assistant frontend application.

## 🚀 Deployment Overview

The frontend application is built with Next.js and can be deployed to multiple platforms with different configurations for optimal performance and scalability.

## 🎯 Deployment Targets

### 1. Vercel (Recommended)

Vercel provides the best Next.js experience with automatic optimizations and seamless integration.

#### Setup

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Link Project**:
   ```bash
   vercel link
   ```

#### Environment Variables

Set these environment variables in Vercel dashboard:

```env
# API Configuration
NEXT_PUBLIC_API_URL=https://your-backend-api.com
NEXT_PUBLIC_WEBSOCKET_URL=wss://your-backend-api.com

# Authentication
NEXT_PUBLIC_AUTH_DOMAIN=your-auth-domain.com
NEXT_PUBLIC_AUTH_CLIENT_ID=your-client-id

# Analytics
NEXT_PUBLIC_SENTRY_DSN=https://your-sentry-dsn
NEXT_PUBLIC_SEGMENT_WRITE_KEY=your-segment-key

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_DEBUG_MODE=false
```

#### Deployment Commands

```bash
# Deploy to preview environment
vercel

# Deploy to production
vercel --prod

# Deploy specific branch
vercel --prod --branch=main
```

#### Vercel Configuration

```json
// vercel.json
{
  "version": 2,
  "regions": ["sfo1"],
  "env": {
    "NODE_ENV": "production"
  },
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Access-Control-Allow-Origin",
          "value": "*"
        },
        {
          "key": "Access-Control-Allow-Methods",
          "value": "GET, POST, PUT, DELETE, OPTIONS"
        },
        {
          "key": "Access-Control-Allow-Headers",
          "value": "Content-Type, Authorization"
        }
      ]
    },
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        }
      ]
    }
  ],
  "redirects": [
    {
      "source": "/api-docs",
      "destination": "https://your-backend-api.com/docs",
      "permanent": true
    }
  ]
}
```

### 2. Docker

Containerized deployment for consistent environments across different platforms.

#### Dockerfile

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM node:20-alpine AS production

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

#### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NEXT_PUBLIC_WEBSOCKET_URL=ws://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    image: your-backend-image:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/goblin
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=goblin
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

#### Docker Deployment

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f frontend

# Scale application
docker-compose up -d --scale frontend=3
```

### 3. Static Export

For deployment to static hosting services (Netlify, GitHub Pages, etc.).

#### Configuration

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  distDir: 'out',
  images: {
    unoptimized: true, // Disable image optimization for static export
  },
  trailingSlash: true, // Add trailing slashes to all paths
};

module.exports = nextConfig;
```

#### Build and Export

```bash
# Build and export
npm run build
npm run export

# Serve locally
npx serve out

# Deploy to GitHub Pages
npm install --global gh-pages
gh-pages -d out
```

## 🔧 Build Configuration

### Environment-Specific Builds

```javascript
// next.config.js
const getConfig = () => {
  const env = process.env.NODE_ENV || 'development';
  
  const config = {
    development: {
      apiURL: 'http://localhost:8000',
      websocketURL: 'ws://localhost:8000',
      enableAnalytics: false,
      enableDebug: true,
    },
    staging: {
      apiURL: 'https://staging-api.yourapp.com',
      websocketURL: 'wss://staging-api.yourapp.com',
      enableAnalytics: true,
      enableDebug: false,
    },
    production: {
      apiURL: 'https://api.yourapp.com',
      websocketURL: 'wss://api.yourapp.com',
      enableAnalytics: true,
      enableDebug: false,
    },
  };

  return config[env] || config.development;
};

const config = getConfig();

/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    API_URL: config.apiURL,
    WEBSOCKET_URL: config.websocketURL,
    ENABLE_ANALYTICS: config.enableAnalytics,
    ENABLE_DEBUG: config.enableDebug,
  },
  // ... other config
};

module.exports = nextConfig;
```

### Build Optimization

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable SWC minification
  swcMinify: true,
  
  // Enable experimental features
  experimental: {
    appDir: true,
    serverComponentsExternalPackages: [],
  },
  
  // Image optimization
  images: {
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  
  // Compression
  compress: true,
  
  // Bundle analysis
  webpack: (config, { dev, isServer }) => {
    if (!dev && !isServer) {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          openAnalyzer: false,
          reportFilename: '../analyze/client.html',
        })
      );
    }
    
    return config;
  },
};

module.exports = nextConfig;
```

### Performance Optimization

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable HTTP/2 push preload links
  headers: async () => {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Link',
            value: '</fonts/inter-var.woff2>; rel=preload; as=font; type=font/woff2; crossorigin',
          },
        ],
      },
    ];
  },
  
  // Optimize fonts
  optimizeFonts: true,
  
  // Enable font loading strategy
  fontLoadWait: 250,
  
  // Optimize images
  images: {
    minimumCacheTTL: 31536000, // 1 year
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
};
```

## 🛡️ Security Configuration

### Security Headers

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  headers: async () => {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ];
  },
};
```

### Content Security Policy

```javascript
// lib/security/csp.js
export const getCSPHeaders = () => {
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  const directives = {
    'default-src': ["'self'"],
    'script-src': isDevelopment 
      ? ["'self'", "'unsafe-eval'", "'unsafe-inline'"]
      : ["'self'"],
    'style-src': ["'self'", "'unsafe-inline'"],
    'img-src': ["'self'", 'data:', 'https:'],
    'font-src': ["'self'"],
    'connect-src': [
      "'self'",
      process.env.NEXT_PUBLIC_API_URL || '',
      process.env.NEXT_PUBLIC_WEBSOCKET_URL || '',
    ].filter(Boolean),
    'frame-src': ["'none'"],
    'object-src': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'"],
  };

  return Object.entries(directives)
    .map(([key, values]) => `${key} ${values.join(' ')}`)
    .join('; ');
};
```

## 📊 Monitoring & Analytics

### Error Tracking (Sentry)

```javascript
// sentry.client.config.js
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});
```

### Performance Monitoring

```javascript
// lib/monitoring/performance.js
export const initPerformanceMonitoring = () => {
  if (typeof window !== 'undefined') {
    // Measure Core Web Vitals
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          console.log('FCP:', entry.startTime);
        }
        if (entry.name === 'largest-contentful-paint') {
          console.log('LCP:', entry.startTime);
        }
      }
    }).observe({ entryTypes: ['paint', 'largest-contentful-paint'] });

    // Measure cumulative layout shift
    new PerformanceObserver((list) => {
      let clsValue = 0;
      for (const entry of list.getEntries()) {
        if (!(entry as any).hadRecentInput) {
          clsValue += (entry as any).value;
        }
      }
      console.log('CLS:', clsValue);
    }).observe({ entryTypes: ['layout-shift'] });
  }
};
```

### Analytics (Segment)

```javascript
// lib/analytics/segment.js
export const initSegment = () => {
  const writeKey = process.env.NEXT_PUBLIC_SEGMENT_WRITE_KEY;
  
  if (!writeKey) return;

  // Load Segment script
  const script = document.createElement('script');
  script.innerHTML = `
    !function(){var analytics=window.analytics=window.analytics||[];if(!analytics.initialize)if(analytics.invoked)window.console&&console.error&&console.error("Segment snippet included twice.");else{analytics.invoked=!0;analytics.methods=["trackSubmit","trackClick","trackLink","trackForm","pageview","identify","reset","group","track","ready","alias","debug","page","once","off","on","addSourceMiddleware","addIntegrationMiddleware","setAnonymousId","addDestinationMiddleware"];analytics.factory=function(e){return function(){var t=Array.prototype.slice.call(arguments);t.unshift(e);analytics.push(t);return analytics}};for(var e=0;e<analytics.methods.length;e++){var t=analytics.methods[e];analytics[t]=analytics.factory(t)}analytics.load=function(e,t){var n=document.createElement("script");n.type="text/javascript";n.async=!0;n.src="https://cdn.segment.com/analytics.js/v1/"+e+"/analytics.min.js";var a=document.getElementsByTagName("script")[0];a.parentNode.insertBefore(n,a);analytics._loadOptions=t};analytics.SNIPPET_VERSION="4.13.2";
    analytics.load("${writeKey}");
    analytics.page();
    }}();
  `;
  document.head.appendChild(script);
};

export const trackEvent = (event, properties = {}) => {
  if (typeof window !== 'undefined' && window.analytics) {
    window.analytics.track(event, properties);
  }
};
```

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [ main, staging ]
  pull_request:
    branches: [ main ]

env:
  NODE_VERSION: '20.x'

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      build-artifacts: ${{ steps.build.outputs.artifacts }}
      cache-key: ${{ steps.cache.outputs.key }}

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: ${{ env.NODE_VERSION }}
        cache: 'pnpm'

    - name: Install dependencies
      run: pnpm install

    - name: Run linting
      run: pnpm lint

    - name: Run type checking
      run: pnpm type-check

    - name: Run tests
      run: pnpm test:coverage

    - name: Build application
      run: pnpm build
      env:
        NODE_ENV: production

    - name: Upload build artifacts
      uses: actions/upload-artifact@v3
      with:
        name: build-artifacts
        path: |
          .next/
          package.json
          package-lock.json
        retention-days: 7

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/staging'

    steps:
    - name: Download build artifacts
      uses: actions/download-artifact@v3
      with:
        name: build-artifacts
        path: .

    - name: Deploy to staging
      uses: akhileshns/heroku-deploy@v3.12.14
      with:
        heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
        heroku_app_name: "goblin-assistant-staging"
        heroku_email: "your-email@example.com"

  deploy-production:
    needs: [build, deploy-staging]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
    - name: Download build artifacts
      uses: actions/download-artifact@v3
      with:
        name: build-artifacts
        path: .

    - name: Deploy to production (Vercel)
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
        working-directory: .
        prod: true

    - name: Notify deployment
      run: |
        echo "Production deployment completed successfully!"

  e2e-tests:
    needs: [deploy-staging, deploy-production]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: ${{ env.NODE_VERSION }}
        cache: 'pnpm'

    - name: Install dependencies
      run: pnpm install

    - name: Install Playwright
      run: pnpm playwright install

    - name: Run E2E tests
      run: pnpm test:e2e
      env:
        BASE_URL: ${{ github.ref == 'refs/heads/main' && 'https://your-production-url.com' || 'https://your-staging-url.com' }}
```

### Build Scripts

```json
// package.json
{
  "scripts": {
    "build": "next build",
    "start": "next start",
    "build:analyze": "ANALYZE=true next build",
    "build:staging": "cross-env NODE_ENV=staging next build",
    "build:production": "cross-env NODE_ENV=production next build",
    "export": "next export",
    "serve:build": "next start -p 3000",
    "docker:build": "docker build -t goblin-assistant-frontend .",
    "docker:run": "docker run -p 3000:3000 goblin-assistant-frontend"
  }
}
```

## 🔍 Performance Monitoring

### Lighthouse CI

```javascript
// lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000'],
      startServerCommand: 'npm run start',
      startServerReadyPattern: 'started server',
      startServerReadyTimeout: 20000,
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.9 }],
        'categories:pwa': ['warn', { minScore: 0.8 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
```

### Bundle Analysis

```bash
# Analyze bundle size
pnpm build:analyze

# Generate bundle report
open .next/analyze/client.html
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Environment Variables Not Available

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  // OR use publicRuntimeConfig for runtime access
  publicRuntimeConfig: {
    apiUrl: process.env.NEXT_PUBLIC_API_URL,
  },
};
```

#### 2. Build Failures

```bash
# Clear build cache
rm -rf .next
pnpm build

# Check for TypeScript errors
pnpm type-check

# Check for ESLint errors
pnpm lint
```

#### 3. Performance Issues

```bash
# Analyze bundle
pnpm build:analyze

# Check for large dependencies
npm ls --depth=0

# Enable compression
# Add to next.config.js
compress: true,
```

#### 4. Deployment Failures

```bash
# Check build logs
pnpm build 2>&1 | tee build.log

# Verify environment variables
echo $NEXT_PUBLIC_API_URL

# Test locally
pnpm start
```

### Health Checks

```typescript
// lib/health.ts
export const healthCheck = async () => {
  try {
    const response = await fetch('/api/health');
    const data = await response.json();
    
    if (response.ok) {
      console.log('Health check passed:', data);
      return true;
    } else {
      console.error('Health check failed:', data);
      return false;
    }
  } catch (error) {
    console.error('Health check error:', error);
    return false;
  }
};

// Usage in _app.tsx
useEffect(() => {
  const interval = setInterval(healthCheck, 60000); // Check every minute
  return () => clearInterval(interval);
}, []);
```

## 📚 Additional Resources

- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Vercel Documentation](https://vercel.com/docs)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Web Performance Optimization](https://web.dev/fast/)
- [Security Headers Guide](https://securityheaders.com/)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
