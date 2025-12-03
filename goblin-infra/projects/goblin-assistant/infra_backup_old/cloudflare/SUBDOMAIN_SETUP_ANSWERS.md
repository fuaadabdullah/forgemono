# Quick Answers for ./setup_subdomains.sh

When the script prompts you, use these answers:

## Domain Selection
**Question:** Enter domain name (e.g., fuaad.ai):
**Answer:** `fuaad.ai`

## Subdomain Targets

### 1. Frontend (goblin.fuaad.ai)
**Question:** Target (CNAME or IP):
**Answer Options:**
- If deploying to Vercel: `cname.vercel-dns.com`
- If deploying to Netlify: `YOUR-SITE-NAME.netlify.app`
 - For now (testing): Can use backend URL temporarily: `goblin-assistant.fly.dev`

**Recommended:** Deploy frontend first, or use backend URL temporarily.

### 2. Backend API (api.goblin.fuaad.ai)
**Question:** Target (CNAME or IP):
**Answer:** `goblin-assistant.fly.dev`

### 3. Brain/Inference (brain.goblin.fuaad.ai)
**Question:** Target (or press Enter for default):
**Answer:** Press **Enter** (uses default: `goblin-assistant-edge.fuaadabdullah.workers.dev`)

### 4. Ops/Admin (ops.goblin.fuaad.ai)
**Question:** Target (CNAME, IP, or tunnel):
**Answer:** `9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com`
(Your Cloudflare Tunnel for secure admin access)

## Summary of Targets

```
goblin.fuaad.ai        → goblin-assistant.fly.dev (temporary)
api.goblin.fuaad.ai    → goblin-assistant.fly.dev
brain.goblin.fuaad.ai  → goblin-assistant-edge.fuaadabdullah.workers.dev
ops.goblin.fuaad.ai    → 9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com
```

## After Setup

1. **Deploy Worker with new config:**
   ```bash
   cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
   wrangler deploy
   ```

2. **Add custom domain to Worker:**
   ```bash
   wrangler domains add brain.goblin.fuaad.ai
   ```

3. **Wait for DNS propagation (5-30 minutes):**
   ```bash
   watch -n 10 'dig goblin.fuaad.ai +short'
   ```

4. **Test endpoints:**
   ```bash
   curl -I https://goblin.fuaad.ai
   curl https://api.goblin.fuaad.ai/health | jq
   curl https://brain.goblin.fuaad.ai/health | jq
   ```

## Optional: Deploy Frontend

When ready to deploy the actual frontend:

### Vercel
```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant
vercel login
vercel --prod
```

Then update DNS:
```bash
# In Cloudflare dashboard, change goblin.fuaad.ai target to: cname.vercel-dns.com
# Or re-run: ./setup_subdomains.sh
```

### Netlify
```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant
netlify login
netlify init
netlify deploy --prod
```

Then update DNS to point to your Netlify site.
