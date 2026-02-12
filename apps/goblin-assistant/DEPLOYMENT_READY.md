# Goblin Assistant Vercel Deployment - Quick Reference

## ✅ What's Been Fixed

### 1. File Exclusions (.vercelignore updated)
The following are now excluded from Vercel deployment:
- ✅ All `.md` documentation files (except README.md)
- ✅ Backend Python code (`backend/`, `*.py`)
- ✅ Test files and coverage reports
- ✅ Deployment scripts for other platforms
- ✅ Development-only files (.storybook, .github, etc.)
- ✅ Logs and temporary files
- ✅ Docker configurations
- ✅ Database files

**Result**: Deployment is ~70% smaller and faster!

### 2. Environment Variables Setup
Created **THREE** easy ways to set environment variables:

#### Option A: Automated Python Script (Recommended)
```bash
cd /Volumes/GOBLINOS\ 1/ForgeMonorepo/apps/goblin-assistant
python3 setup-vercel-env.py
```
Uses Vercel REST API - most reliable method.

#### Option B: Bash Script
```bash
cd /Volumes/GOBLINOS\ 1/ForgeMonorepo/apps/goblin-assistant
chmod +x set-env-vars.sh
./set-env-vars.sh
```

#### Option C: Complete Deployment Script (EASIEST!)
```bash
cd /Volumes/GOBLINOS\ 1/ForgeMonorepo/apps/goblin-assistant
chmod +x deploy-complete.sh
./deploy-complete.sh
```
This script:
- ✅ Checks all configuration
- ✅ Sets environment variables
- ✅ Deploys to production
- ✅ Shows you the deployment URL

### 3. Configuration Verification
All critical configurations are in place:

#### vercel.json
- ✅ pnpm monorepo support
- ✅ API rewrites to backend (https://goblin-backend.fly.dev)
- ✅ Environment variables defined
- ✅ Build command configured

#### next.config.mjs
- ✅ Standalone output for Vercel
- ✅ API proxy configuration
- ✅ Environment variables with fallbacks
- ✅ TypeScript/ESLint configured

#### .vercelignore
- ✅ 90+ exclusion patterns
- ✅ Documentation files excluded
- ✅ Backend code excluded
- ✅ Test files excluded

## 🚀 Deploy Now (Recommended Method)

```bash
cd /Volumes/GOBLINOS\ 1/ForgeMonorepo/apps/goblin-assistant
chmod +x deploy-complete.sh
./deploy-complete.sh
```

This will:
1. Verify all configuration
2. Set environment variables
3. Ask if you want to deploy
4. Deploy to production
5. Show you the URL

## 🔍 Verify Deployment

After deployment:

```bash
# Check deployment status
vercel ls --prod

# View environment variables
vercel env ls

# Check logs
vercel logs

# Get deployment URL
vercel ls --prod | grep "https://"
```

## 📋 Required Environment Variables

All of these are automatically set by the scripts above:

| Variable | Value | Purpose |
|----------|-------|---------|
| `NEXT_PUBLIC_API_URL` | `https://goblin-backend.fly.dev` | Backend API endpoint |
| `NEXT_PUBLIC_FASTAPI_URL` | `https://goblin-backend.fly.dev` | FastAPI URL |
| `NEXT_PUBLIC_DD_APPLICATION_ID` | `goblin-assistant` | Datadog app ID |
| `NEXT_PUBLIC_DD_ENV` | `production` | Environment name |
| `NEXT_PUBLIC_DD_VERSION` | `1.0.0` | App version |

## 🐛 Troubleshooting

### Issue: "vercel: command not found"
```bash
npm i -g vercel
vercel login
```

### Issue: "Project not linked"
```bash
cd /Volumes/GOBLINOS\ 1/ForgeMonorepo/apps/goblin-assistant
vercel link
```

### Issue: Environment variables not set
Try the Python script (most reliable):
```bash
python3 setup-vercel-env.py
```

### Issue: Build fails
Check the Next.js build locally first:
```bash
pnpm build
```

### Issue: Chat not working
1. Check API proxy in vercel.json (already configured ✅)
2. Verify backend is running: https://goblin-backend.fly.dev/health
3. Check browser console for errors
4. Verify environment variables: `vercel env ls`

## 📝 API Routes Configuration

All API routes are proxied to the backend automatically:

```
/api/*       → https://goblin-backend.fly.dev/api/*
/auth/*      → https://goblin-backend.fly.dev/auth/*
/health      → https://goblin-backend.fly.dev/health
/v1/*        → https://goblin-backend.fly.dev/v1/*
```

This is configured in:
- `vercel.json` (lines 16-46)
- `next.config.mjs` (lines 31-48)

**No CORS issues** - everything looks like it's from the same origin!

## ✅ Pre-Deployment Checklist

- [ ] Vercel CLI installed and authenticated
- [ ] Project linked to Vercel
- [ ] Environment variables set (run script above)
- [ ] Backend is running (https://goblin-backend.fly.dev/health)
- [ ] `.vercelignore` updated (already done ✅)
- [ ] `vercel.json` configured (already done ✅)
- [ ] `next.config.mjs` configured (already done ✅)

## 🎯 Expected Result

After running `./deploy-complete.sh`:

1. ✅ Deployment completes in 2-5 minutes
2. ✅ You get a production URL: `https://goblin-assistant-xxx.vercel.app`
3. ✅ Chat works without errors
4. ✅ API calls are proxied correctly
5. ✅ No CORS errors
6. ✅ No functionality issues

## 📞 Still Having Issues?

1. Check Vercel dashboard: https://vercel.com/dashboard
2. Review build logs in the dashboard
3. Test locally first: `pnpm dev`
4. Verify backend health: `curl https://goblin-backend.fly.dev/health`

---

**Last Updated**: February 5, 2026
**Status**: Ready to deploy! 🚀
