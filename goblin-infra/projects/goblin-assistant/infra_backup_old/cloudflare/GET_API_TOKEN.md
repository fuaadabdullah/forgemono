# Getting a Cloudflare API Token for DNS Management

Your current API token is invalid. Follow these steps to get a new one:

## Quick Steps

1. **Go to Cloudflare API Tokens page:**
   ```bash
   open https://dash.cloudflare.com/profile/api-tokens
   ```

2. **Create Custom Token:**
   - Click "Create Token"
   - Click "Use template" next to "Edit zone DNS"
   - OR click "Create Custom Token"

3. **Configure Permissions:**
   - **Permissions:**
     - `Zone` → `DNS` → `Edit`
     - `Zone` → `Zone` → `Read`
   - **Zone Resources:**
     - `Include` → `Specific zone` → `fuaad.ai`
   - **TTL:** Leave default (no expiration) or set your preference

4. **Generate Token:**
   - Click "Continue to summary"
   - Click "Create Token"
   - **COPY THE TOKEN** (you'll only see it once!)

5. **Update .env file:**
   ```bash
   cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare

   # Edit .env and replace CF_API_TOKEN with your new token
   nano .env
   # or
   code .env
   ```

6. **Run setup again:**
   ```bash
   ./setup_subdomains.sh
   ```

## Alternative: Use Cloudflare Dashboard

If you prefer to set up DNS manually instead of using the script:

### Step 1: Go to DNS Management
```bash
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb
```

### Step 2: Select fuaad.ai domain
Click on the `fuaad.ai` zone

### Step 3: Add DNS Records
Go to DNS → Records → Add record

**Record 1: Frontend**
- Type: `CNAME`
- Name: `goblin`
- Target: `goblin-assistant-backend.onrender.com` (temporary)
- Proxy status: Proxied (orange cloud)
- TTL: Auto

**Record 2: Backend API**
- Type: `CNAME`
- Name: `api.goblin`
- Target: `goblin-assistant-backend.onrender.com`
- Proxy status: Proxied (orange cloud)
- TTL: Auto

**Record 3: Brain (Worker)**
- Type: `CNAME`
- Name: `brain.goblin`
- Target: `goblin-assistant-edge.fuaadabdullah.workers.dev`
- Proxy status: Proxied (orange cloud)
- TTL: Auto

**Record 4: Ops (Admin)**
- Type: `CNAME`
- Name: `ops.goblin`
- Target: `9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com`
- Proxy status: Proxied (orange cloud)
- TTL: Auto

### Step 4: Configure SSL
Go to SSL/TLS → Overview
- Set mode to: **Full (strict)**
- Enable: **Always Use HTTPS**

### Step 5: Add Custom Domain to Worker
```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
wrangler domains add brain.goblin.fuaad.ai
```

### Step 6: Test DNS
```bash
dig goblin.fuaad.ai
dig api.goblin.fuaad.ai
dig brain.goblin.fuaad.ai
dig ops.goblin.fuaad.ai
```

## Which Method Should I Use?

**Use the Script (Recommended):**
- ✅ Faster (automated)
- ✅ Less error-prone
- ✅ Idempotent (safe to re-run)
- ✅ Saves config to .env
- ❌ Requires valid API token

**Use Dashboard (Backup):**
- ✅ No API token needed
- ✅ Visual interface
- ✅ Works when token issues occur
- ❌ Manual process
- ❌ More time-consuming

## Next Steps After DNS is Set Up

1. **Deploy Worker with new config:**
   ```bash
   cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
   wrangler deploy
   ```

2. **Add custom domain to Worker:**
   ```bash
   wrangler domains add brain.goblin.fuaad.ai
   ```

3. **Wait for DNS propagation (5-30 minutes)**

4. **Test all endpoints:**
   ```bash
   curl -I https://goblin.fuaad.ai
   curl https://api.goblin.fuaad.ai/health | jq
   curl https://brain.goblin.fuaad.ai/health | jq
   curl -I https://ops.goblin.fuaad.ai
   ```

## Troubleshooting

### "Invalid API Token"
- Token may have expired
- Token may not have DNS edit permissions
- Token may not include the fuaad.ai zone

**Solution:** Create a new token with the correct permissions

### Can't find fuaad.ai in Cloudflare
**Solution:** Make sure fuaad.ai is added to your Cloudflare account first

### DNS not propagating
**Solution:** DNS can take 5-30 minutes. Check with: `dig @1.1.1.1 goblin.fuaad.ai`
