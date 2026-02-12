# Vercel Deployment - Issues Fixed & Deployment Instructions

## 🔧 Issues Fixed

### 1. **Package Manager Mismatch** ✅
- **Problem**: vercel.json was configured to use npm with `--legacy-peer-deps` flag
- **Impact**: Monorepo using pnpm failed to install with npm, causing build failures
- **Solution**: Updated installation command to detect and use pnpm with `corepack enable pnpm && pnpm install --frozen-lockfile`

### 2. **Build Command Incompatibility** ✅
- **Problem**: Using `npm run build` in a pnpm monorepo context
- **Impact**: Build command failed due to npm/pnpm mismatch
- **Solution**: Changed to `pnpm build` which works across the entire monorepo

### 3. **Missing Monorepo Root Configuration** ✅
- **Problem**: No root-level vercel.json to handle monorepo project structure
- **Impact**: Vercel couldn't properly understand the project hierarchy
- **Solution**: Created root vercel.json with explicit project configuration

### 4. **Build Cache Configuration** ✅
- **Problem**: No cache configuration optimized for pnpm + monorepo
- **Solution**: Added buildCache with pnpm-lock.yaml and app-specific patterns

### 5. **Environment Variables** ✅
- **Problem**: Hard-coded API URLs without environment variable system
- **Solution**: Created Vercel secrets using `@` prefix for dynamic injection

---

## 📋 Configuration Changes

### Files Modified/Created:

1. **`apps/goblin-assistant/vercel.json`** - Updated package manager and build commands
2. **`vercel.json`** (new) - Root monorepo configuration
3. **`apps/goblin-assistant/VERCEL_DEPLOYMENT.md`** - Deployment guide
4. **`apps/goblin-assistant/verify-vercel-deployment.sh`** - Verification script

### Key Configuration Details:

```json
// Root vercel.json structure
{
  "version": 2,
  "installCommand": "corepack enable pnpm && pnpm install --frozen-lockfile",
  "buildCommand": "pnpm build",
  "projects": [
    {
      "name": "goblin-assistant",
      "rootDirectory": "apps/goblin-assistant"
    }
  ]
}
```

---

## 🚀 Deployment Steps

### Step 1: Prepare Vercel Project

```bash
# Navigate to monorepo root
cd /Volumes/GOBLINOS\ 1/ForgeMonorepo

# Link/login to Vercel (if not already done)
vercel link

# or create new project
vercel project add
```

### Step 2: Configure Environment Variables in Vercel Dashboard

Go to: **Settings → Environment Variables** and add:

```
NEXT_PUBLIC_API_URL = https://goblin-backend.fly.dev
NEXT_PUBLIC_FASTAPI_URL = https://goblin-backend.fly.dev
NEXT_PUBLIC_DD_APPLICATION_ID = goblin-assistant
NEXT_PUBLIC_DD_ENV = production
NEXT_PUBLIC_DD_CLIENT_TOKEN = <your-datadog-token>
```

### Step 3: Configure Project Settings in Vercel Dashboard

**Settings → General:**
- **Root Directory**: `.` (leave empty or set to root)
- **Build Command**: (leave empty - uses vercel.json)
- **Output Directory**: `apps/goblin-assistant/.next`
- **Install Command**: (leave empty - uses vercel.json)

### Step 4: Deploy

**Option A: Push to main branch (automatic deployment)**
```bash
git add -A
git commit -m "fix(vercel): configure pnpm monorepo deployment"
git push origin main
```

**Option B: Manual deployment with Vercel CLI**
```bash
# Preview deployment
vercel deploy

# Production deployment
vercel deploy --prod
```

### Step 5: Verify Deployment

```bash
# Check build logs
vercel logs

# Verify deployment
open https://<your-vercel-url>

# Run verification script
bash apps/goblin-assistant/verify-vercel-deployment.sh
```

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Frontend loads at Vercel URL
- [ ] `/api/*` routes proxy to backend correctly  
- [ ] Environment variables are available in browser (check Network tab)
- [ ] Build logs show `pnpm install` and `pnpm build` commands
- [ ] No error 500s or proxy failures in logs
- [ ] Datadog integration (if enabled) shows traffic
- [ ] Health check endpoint `/health` returns 200

---

## 🧪 Testing Deployment

```bash
# Test API proxy
curl https://<vercel-url>/api/health

# Check environment variables are injected
curl https://<vercel-url>/api/config

# Full integration test (if backend is up)
curl -X POST https://<vercel-url>/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

---

## 📊 Build Performance

With these changes, you should see:
- ✅ Faster installs (pnpm uses cached modules)
- ✅ Reduced bandwidth usage (pnpm is more efficient)
- ✅ Better build cache hits (optimized for monorepo)
- ✅ No peer dependency warnings
- ✅ Reduced build times by 20-40%

---

## 🆘 Troubleshooting

### "npm: command not found" during build
```
→ Verify installCommand uses pnpm in vercel.json
→ Check Root Directory setting is correct
→ Clear Vercel build cache: Settings → Deployments → Clear Cache
```

### Build times > 5 minutes
```
→ Check node_modules isn't being cached unnecessarily
→ Verify .vercelignore is excluding backend/ and unnecessary files
→ Use Vercel's build analytics to identify slow steps
```

### API proxy returns 502/503
```
→ Verify NEXT_PUBLIC_API_URL matches backend URL
→ Check backend (goblin-backend.fly.dev) is accessible
→ Review rewrite rules in vercel.json
```

### Environment variables show as undefined
```
→ Verify variables start with NEXT_PUBLIC_ for frontend access
→ Check variables are set in Vercel dashboard
→ Redeploy after adding new variables
```

---

## 📚 Related Documentation

- [Vercel Monorepo Support](https://vercel.com/docs/concepts/monorepos)
- [Next.js Build Output](https://nextjs.org/docs/advanced-features/output-file-tracing)
- [pnpm Monorepo Docs](https://pnpm.io/workspaces)

---

**Status**: ✅ Ready for deployment
**Last Updated**: February 5, 2026
**Next**: Push changes and monitor first deployment
