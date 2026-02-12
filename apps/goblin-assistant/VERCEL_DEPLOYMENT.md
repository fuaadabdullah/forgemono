# Vercel Deployment Guide - Goblin Assistant

## Changes Made

### 1. Fixed Vercel Route Hijacking (vercel.json)

**Issue**: Vercel platform rewrites were proxying frontend page routes (like `/chat`, `/account`, `/sandbox`) to the backend. That breaks Next.js routing and makes the UI feel "mixed" or unclickable.

**Changes**:
- Removed Vercel platform `rewrites` that overlapped Next.js pages routes.
- Switched frontend API base env vars to `/v1` so the browser calls the backend through Next.js rewrites (same-origin), avoiding CORS and route collisions.

## Required Setup Steps

### Step 1: Set Vercel Environment Variables

In your Vercel project dashboard, add these environment variables:

```
NEXT_PUBLIC_API_URL = /v1
NEXT_PUBLIC_FASTAPI_URL = /v1
NEXT_PUBLIC_DD_APPLICATION_ID = goblin-assistant
NEXT_PUBLIC_DD_ENV = production
NEXT_PUBLIC_DD_CLIENT_TOKEN = <your-datadog-token>
NEXT_PUBLIC_DD_VERSION = 1.0.0
```

### Step 2: Link Repository to Vercel

If the repository isn't already linked:

```bash
# Link to Vercel (if not already linked)
vercel link
```

### Step 3: Configure Project Settings

In Vercel Dashboard:

1. Go to **Settings → General**
2. Set **Root Directory** to: `apps/goblin-assistant`
3. Set **Build Command** to: `npm run build`
4. Set **Install Command** to: `npm install --legacy-peer-deps`
5. Set **Output Directory** to: `.next`

### Step 4: Deploy

```bash
# Push changes to trigger automatic deployment
git push

# OR manually deploy with Vercel CLI
vercel deploy --prod
```

## Verification

After deployment, verify:

1. ✅ Frontend loads at deployment URL
2. ✅ API requests to `/v1/*` proxy to the backend via Next.js rewrites
3. ✅ No platform rewrites hijack `/chat`, `/search`, `/account`, or `/sandbox`
4. ✅ No build failures related to dependency resolution
5. ✅ Environment variables are set correctly

## Troubleshooting

### Issue: Build fails with "npm: command not found"

**Solution**: Vercel must use pnpm. Check that:
- vercel.json has correct `installCommand` with pnpm
- Root directory is set correctly
- No npm-specific configurations are present

### Issue: "Module not found" errors during build

**Solution**: 
```bash
# Verify pnpm lockfile is up to date locally
pnpm install

# Ensure vercel.json uses --frozen-lockfile
pnpm install --frozen-lockfile
```

### Issue: API routes not proxying correctly

**Solution**:
- Verify `rewrites` in vercel.json
- Check that backend URL (goblin-backend.fly.dev) is accessible
- Verify NEXT_PUBLIC_API_URL environment variable is set

## Monitoring

After deployment, monitor:
- Vercel build logs for any warnings
- Frontend for console errors
- API proxy for failed requests
- Datadog for inference metrics

---

**Last Updated**: February 5, 2026
**Status**: Vercel configuration fixed for pnpm monorepo support
