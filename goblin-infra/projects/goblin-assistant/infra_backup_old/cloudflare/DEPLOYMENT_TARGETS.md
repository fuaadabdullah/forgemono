# Goblin Assistant Deployment Targets

## Current Deployment Status

### ✅ Backend API (Already Deployed)
- **Platform:** Render
- **URL:** `goblin-assistant-backend.onrender.com`
- **Target for DNS:** `goblin-assistant-backend.onrender.com`
- **Will map to:** `api.goblin.fuaad.ai`

### ✅ Worker (Already Deployed)
- **Platform:** Cloudflare Workers
- **URL:** `goblin-assistant-edge.fuaadabdullah.workers.dev`
- **Target for DNS:** `goblin-assistant-edge.fuaadabdullah.workers.dev`
- **Will map to:** `brain.goblin.fuaad.ai`

### ⏳ Frontend (To Be Deployed)
- **Platform Options:** Vercel or Netlify
- **Will map to:** `goblin.fuaad.ai`

#### Option 1: Vercel
```bash
# Deploy to Vercel
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant
vercel --prod

# Get deployment URL
# Example: goblin-assistant-xyz.vercel.app
```

**Target for DNS:** `cname.vercel-dns.com` (Vercel provides this)

#### Option 2: Netlify
```bash
# Deploy to Netlify
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant
netlify deploy --prod

# Get deployment URL
# Example: goblin-assistant.netlify.app
```

**Target for DNS:** Your Netlify site URL (e.g., `goblin-assistant.netlify.app`)

### ⏳ Ops/Admin Panel
- **Will map to:** `ops.goblin.fuaad.ai`
- **Options:**
  1. Same as backend (Render URL)
  2. Cloudflare Tunnel: `9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com`
  3. Separate admin interface (to be deployed)

**Recommended:** Use Cloudflare Tunnel for secure admin access

## Quick Setup Reference

When running `./setup_subdomains.sh`, provide:

| Subdomain | Target |
|-----------|--------|
| `goblin.fuaad.ai` | Vercel: `cname.vercel-dns.com` OR Netlify: `your-site.netlify.app` |
| `api.goblin.fuaad.ai` | `goblin-assistant-backend.onrender.com` |
| `brain.goblin.fuaad.ai` | `goblin-assistant-edge.fuaadabdullah.workers.dev` (default) |
| `ops.goblin.fuaad.ai` | `9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com` OR same as API |

## Step-by-Step Deployment

### Step 1: Deploy Frontend (Choose One)

#### Vercel
```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant

# Login to Vercel
vercel login

# Deploy to production
vercel --prod

# Note the deployment URL
# It will be something like: goblin-assistant-xyz.vercel.app
```

#### Netlify
```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant

# Login to Netlify
netlify login

# Initialize site
netlify init

# Deploy to production
netlify deploy --prod

# Note the site name
# It will be something like: goblin-assistant.netlify.app
```

### Step 2: Run Subdomain Setup

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
./setup_subdomains.sh
```

When prompted:

1. **Domain:** `fuaad.ai`
2. **Frontend Target:**
   - Vercel: `cname.vercel-dns.com`
   - Netlify: `your-site.netlify.app`
3. **Backend Target:** `goblin-assistant-backend.onrender.com`
4. **Brain Target:** Press Enter (uses default Worker URL)
5. **Ops Target:** `9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com`

### Step 3: Update Application Configs

#### Frontend `.env.production`
```env
VITE_API_URL=https://api.goblin.fuaad.ai
VITE_BRAIN_URL=https://brain.goblin.fuaad.ai
VITE_TURNSTILE_SITE_KEY=0x4AAAAAACEUKA3R8flZ2Ig0
VITE_TURNSTILE_INVISIBLE_KEY=0x4AAAAAACEUKak3TnCntrFv
```

#### Backend Environment (Render Dashboard)
```env
FRONTEND_URL=https://goblin.fuaad.ai
CORS_ORIGINS=https://goblin.fuaad.ai,https://api.goblin.fuaad.ai,https://ops.goblin.fuaad.ai
API_BASE_URL=https://api.goblin.fuaad.ai
```

#### Worker `wrangler.toml`
```toml
[vars]
API_URL = "https://api.goblin.fuaad.ai"
FRONTEND_URL = "https://goblin.fuaad.ai"
OPS_URL = "https://ops.goblin.fuaad.ai"
```

### Step 4: Add Custom Domain to Worker

**Important:** DNS records alone aren't enough. You must bind the custom domain:

```bash
# Option A: Command line
wrangler domains add brain.goblin.fuaad.ai

# Option B: Dashboard
# Go to: Workers & Pages → goblin-assistant-edge → Settings → Triggers
# Click "Add Custom Domain" → Enter "brain.goblin.fuaad.ai"
```

### Step 5: Redeploy Everything

```bash
# Redeploy Worker with new config
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
wrangler deploy

# Redeploy Frontend with new .env.production
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant
vercel --prod  # or netlify deploy --prod

# Update Backend environment variables in Render dashboard
# Then trigger a new deployment in Render
```

### Step 6: Test All Endpoints

```bash
# Test DNS resolution
dig goblin.fuaad.ai
dig api.goblin.fuaad.ai
dig brain.goblin.fuaad.ai
dig ops.goblin.fuaad.ai

# Test HTTPS
curl -I https://goblin.fuaad.ai
curl -I https://api.goblin.fuaad.ai
curl -I https://brain.goblin.fuaad.ai
curl -I https://ops.goblin.fuaad.ai

# Test API endpoints
curl https://api.goblin.fuaad.ai/health | jq
curl https://brain.goblin.fuaad.ai/health | jq
```

## DNS Record Structure

After setup completes, you'll have:

```
fuaad.ai (Zone ID: will be fetched)
├── goblin.fuaad.ai (CNAME → Vercel/Netlify)
├── api.goblin.fuaad.ai (CNAME → Render)
├── brain.goblin.fuaad.ai (CNAME → Cloudflare Worker)
└── ops.goblin.fuaad.ai (CNAME → Cloudflare Tunnel)
```

All records are **proxied** through Cloudflare (orange cloud ☁️) for:
- ✅ DDoS protection
- ✅ SSL/TLS termination
- ✅ Caching
- ✅ Bot protection (Turnstile)
- ✅ Rate limiting
- ✅ Analytics

## Troubleshooting

### "Domain not found"
**Solution:** Make sure `fuaad.ai` is added to your Cloudflare account

### "Invalid API token"
**Solution:** Get a new token at https://dash.cloudflare.com/profile/api-tokens with **Zone.DNS (Edit)** permission

### "CNAME already exists"
**Solution:** Script will update existing records automatically

### Frontend not loading
**Solution:**
1. Check DNS propagation: `dig goblin.fuaad.ai`
2. Verify Vercel/Netlify custom domain is configured
3. Check SSL certificate provisioned (can take 15-30 min)

### CORS errors in browser
**Solution:**
1. Update backend CORS_ORIGINS with all subdomains
2. Redeploy backend
3. Clear browser cache

### Worker not accessible via custom domain
**Solution:**
1. Run `wrangler domains add brain.goblin.fuaad.ai`
2. Wait 5 minutes for binding to propagate

## Next Steps

After successful deployment:

1. ✅ Monitor Cloudflare Analytics
2. ✅ Set up Zero Trust for ops panel
3. ✅ Enable Turnstile on production endpoints
4. ✅ Update GoblinOS docs with new URLs
5. ✅ Test from multiple locations
6. ✅ Set up monitoring alerts

---

**Ready to deploy?**

1. Deploy frontend to Vercel/Netlify first
2. Run `./setup_subdomains.sh`
3. Update configs
4. Test everything! 🚀
