# Next Steps: Complete Subdomain Setup

## 🎯 What We've Done

✅ **Worker Configuration Updated**
- Updated `wrangler.toml` with production subdomain URLs:
  - `API_URL = "https://api.goblin.fuaad.ai"`
  - `FRONTEND_URL = "https://goblin.fuaad.ai"`
  - `OPS_URL = "https://ops.goblin.fuaad.ai"`

✅ **Documentation Created**
- `SUBDOMAIN_SETUP_ANSWERS.md` - Quick answers for setup script
- `GET_API_TOKEN.md` - Token creation + manual setup guide
- `DEPLOYMENT_TARGETS.md` - Complete deployment reference
- `SUBDOMAIN_DEPLOYMENT_GUIDE.md` - Full deployment workflow
- `DEPLOYMENT_CHECKLIST.md` - Updated with subdomain status

✅ **GoblinOS Docs Updated**
- `.github/copilot-instructions.md` now includes production URLs

---

## 🚀 What You Need To Do

### Step 1: Get Cloudflare API Token (2 minutes)

The current API token is invalid. Get a new one:

1. **Open Cloudflare API Tokens page** (already opened for you)
   ```bash
   # If not already open:
   open https://dash.cloudflare.com/profile/api-tokens
   ```

2. **Create Custom Token:**
   - Click "Create Token"
   - Click "Use template" next to "Edit zone DNS"
   - OR click "Create Custom Token"

3. **Set Permissions:**
   - `Zone` → `DNS` → `Edit`
   - `Zone` → `Zone` → `Read`
   - Zone Resources: Include → `fuaad.ai`

4. **Generate & Copy Token**

5. **Update .env file:**
   ```bash
   cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare

   # Edit .env and update CF_API_TOKEN
   code .env
   # Replace: CF_API_TOKEN="Pvdp4NUXjL7iUggzgvk8v4tfQTX_28Koxq4t-06w"
   # With: CF_API_TOKEN="your-new-token-here"
   ```

### Step 2: Run Subdomain Setup (3 minutes)

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
./setup_subdomains.sh
```

**When prompted, provide:**

| Prompt | Answer |
|--------|--------|
| Enter domain name | `fuaad.ai` |
| Frontend target | `goblin-assistant-backend.onrender.com` (temporary) |
| Backend target | `goblin-assistant-backend.onrender.com` |
| Brain target | Press **Enter** (uses default Worker URL) |
| Ops target | `9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com` |

**Expected Output:**
```
✅ All dependencies found
✅ API token is valid
✅ Zone ID: <your-zone-id>
✅ Creating DNS records...
  ✅ Frontend: goblin.fuaad.ai
  ✅ Backend: api.goblin.fuaad.ai
  ✅ Brain: brain.goblin.fuaad.ai
  ✅ Ops: ops.goblin.fuaad.ai
✅ SSL/TLS configured
✅ Setup Complete!
```

### Step 3: Deploy Worker (1 minute)

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
wrangler deploy
```

### Step 4: Add Custom Domain to Worker (1 minute)

```bash
wrangler domains add brain.goblin.fuaad.ai
```

**Expected Output:**
```
✅ Successfully added custom domain brain.goblin.fuaad.ai to worker goblin-assistant-edge
```

### Step 5: Wait for DNS Propagation (5-30 minutes)

```bash
# Watch DNS propagation
watch -n 10 'dig goblin.fuaad.ai +short'

# Or check once:
dig goblin.fuaad.ai
dig api.goblin.fuaad.ai
dig brain.goblin.fuaad.ai
dig ops.goblin.fuaad.ai
```

### Step 6: Test Endpoints (2 minutes)

```bash
# Test SSL certificates
curl -I https://goblin.fuaad.ai
curl -I https://api.goblin.fuaad.ai
curl -I https://brain.goblin.fuaad.ai
curl -I https://ops.goblin.fuaad.ai

# Test API health
curl https://api.goblin.fuaad.ai/health | jq
curl https://brain.goblin.fuaad.ai/health | jq
```

**Expected:**
- All return 200 OK
- Valid SSL certificates
- Health endpoints return `{"status": "healthy"}`

---

## 📋 Alternative: Manual DNS Setup

If you prefer not to use the automated script, set up DNS manually in the Cloudflare Dashboard.

**See:** [GET_API_TOKEN.md](./GET_API_TOKEN.md) → Section "Alternative: Use Cloudflare Dashboard"

---

## 🔧 After DNS is Live

### 1. Deploy Frontend (Optional)

When ready to deploy the actual frontend (instead of using backend URL temporarily):

#### Vercel
```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant
vercel login
vercel --prod
```

Then update DNS:
- Go to Cloudflare Dashboard
- Edit `goblin.fuaad.ai` record
- Change target to: `cname.vercel-dns.com`

#### Netlify
```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant
netlify login
netlify init
netlify deploy --prod
```

Then update DNS:
- Change `goblin.fuaad.ai` target to your Netlify site URL

### 2. Update Application Configs

**Frontend `.env.production`:**
```env
VITE_API_URL=https://api.goblin.fuaad.ai
VITE_BRAIN_URL=https://brain.goblin.fuaad.ai
VITE_TURNSTILE_SITE_KEY=0x4AAAAAACEUKA3R8flZ2Ig0
VITE_TURNSTILE_INVISIBLE_KEY=0x4AAAAAACEUKak3TnCntrFv
```

**Backend Environment (Render Dashboard):**
```env
FRONTEND_URL=https://goblin.fuaad.ai
CORS_ORIGINS=https://goblin.fuaad.ai,https://api.goblin.fuaad.ai,https://ops.goblin.fuaad.ai
```

**Backend `main.py` CORS:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://goblin.fuaad.ai",
        "https://api.goblin.fuaad.ai",
        "https://ops.goblin.fuaad.ai",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Set Up Zero Trust for Ops Panel

1. Go to: https://one.dash.cloudflare.com/
2. Access → Applications → Add application
3. Configure:
   - Type: Self-hosted
   - Name: `Goblin Assistant Ops`
   - Domain: `ops.goblin.fuaad.ai`
   - Policy: Allow `Goblin Admins` group (ID: `1eac441b-55ad-4be9-9259-573675e2d993`)

---

## 📚 Documentation Reference

All documentation is in: `/apps/goblin-assistant/infra/cloudflare/`

| File | Purpose |
|------|---------|
| `README.md` | Complete infrastructure overview |
| `SUBDOMAIN_QUICK_START.md` | Quick setup guide (automated) |
| `SUBDOMAIN_SETUP.md` | Detailed manual setup instructions |
| `SUBDOMAIN_SETUP_ANSWERS.md` | Quick answers for script prompts |
| `SUBDOMAIN_DEPLOYMENT_GUIDE.md` | Full deployment workflow |
| `DEPLOYMENT_TARGETS.md` | Deployment options and targets |
| `GET_API_TOKEN.md` | Token creation + manual DNS setup |
| `DEPLOYMENT_CHECKLIST.md` | Complete deployment checklist |
| `MODEL_GATEWAY_SETUP.md` | LLM routing and model gateway |
| `TURNSTILE_INTEGRATION.md` | Bot protection setup |

---

## 🐛 Troubleshooting

### DNS Not Resolving
```bash
# Check Cloudflare's DNS directly
dig @1.1.1.1 goblin.fuaad.ai

# Clear local DNS cache (macOS)
sudo dscacheutil -flushcache
```

**Solution:** DNS can take 5-30 minutes. Be patient!

### SSL Certificate Error
```bash
curl -vI https://goblin.fuaad.ai
```

**Solution:** SSL certs provision automatically within 15-30 minutes after DNS is active.

### Worker Not Accessible via Custom Domain
```bash
# Check if domain is bound
wrangler domains list
```

**Solution:** Run `wrangler domains add brain.goblin.fuaad.ai` again

### CORS Errors
**Solution:** Update backend CORS config with all subdomain URLs

---

## ✅ Success Checklist

- [ ] New API token created
- [ ] `.env` updated with new token
- [ ] `./setup_subdomains.sh` completed successfully
- [ ] All 4 DNS records created (goblin, api.goblin, brain.goblin, ops.goblin)
- [ ] Worker deployed with new config
- [ ] Custom domain added to Worker (`brain.goblin.fuaad.ai`)
- [ ] DNS propagated (all subdomains resolve)
- [ ] SSL certificates active (all subdomains HTTPS)
- [ ] Health endpoints responding
- [ ] Frontend deployed (optional)
- [ ] Application configs updated (optional)
- [ ] Zero Trust configured for ops panel (optional)

---

## 🎉 You're Almost There!

**Current Status:**
- ✅ Worker config updated
- ✅ Documentation complete
- ✅ GoblinOS docs updated
- ⏳ Waiting for you to get new API token
- ⏳ Waiting to run subdomain setup

**Time Estimate:** 10-15 minutes total (excluding DNS propagation wait time)

**Start here:** Get your Cloudflare API token → Run `./setup_subdomains.sh`

---

**Questions?** Check the documentation files or the deployment checklist!
