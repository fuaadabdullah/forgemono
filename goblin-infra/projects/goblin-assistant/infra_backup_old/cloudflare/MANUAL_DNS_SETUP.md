# Manual DNS Setup Guide - 5 Minutes

## 🎯 Goal
Manually create 4 DNS records in Cloudflare Dashboard for your Goblin Assistant subdomains.

## 📋 Records to Create

### Record 1: Frontend
- **Type:** CNAME
- **Name:** `goblin`
- **Target:** `goblin-assistant-backend.onrender.com`
- **Proxy status:** ☁️ Proxied (orange cloud)
- **TTL:** Auto

### Record 2: Backend API
- **Type:** CNAME
- **Name:** `api.goblin`
- **Target:** `goblin-assistant-backend.onrender.com`
- **Proxy status:** ☁️ Proxied (orange cloud)
- **TTL:** Auto

### Record 3: Brain (LLM Gateway)
- **Type:** CNAME
- **Name:** `brain.goblin`
- **Target:** `goblin-assistant-edge.fuaadabdullah.workers.dev`
- **Proxy status:** ☁️ Proxied (orange cloud)
- **TTL:** Auto

### Record 4: Ops (Admin Panel)
- **Type:** CNAME
- **Name:** `ops.goblin`
- **Target:** `9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com`
- **Proxy status:** ☁️ Proxied (orange cloud)
- **TTL:** Auto

## 🔧 Step-by-Step

1. **Open Cloudflare Dashboard** (already opened for you)
   - You should see your account dashboard

2. **Select fuaad.ai domain**
   - Click on the `fuaad.ai` zone

3. **Go to DNS Management**
   - Click "DNS" in the left sidebar
   - You'll see "DNS Records" section

4. **Add Record 1 (Frontend)**
   - Click "Add record" button
   - Type: Select "CNAME"
   - Name: Enter `goblin`
   - Target: Enter `goblin-assistant-backend.onrender.com`
   - Proxy status: Make sure orange cloud is ON (Proxied)
   - TTL: Leave as "Auto"
   - Click "Save"

5. **Add Record 2 (Backend API)**
   - Click "Add record" again
   - Type: CNAME
   - Name: `api.goblin`
   - Target: `goblin-assistant-backend.onrender.com`
   - Proxy: ON ☁️
   - Click "Save"

6. **Add Record 3 (Brain/LLM Gateway)**
   - Click "Add record" again
   - Type: CNAME
   - Name: `brain.goblin`
   - Target: `goblin-assistant-edge.fuaadabdullah.workers.dev`
   - Proxy: ON ☁️
   - Click "Save"

7. **Add Record 4 (Ops/Admin)**
   - Click "Add record" again
   - Type: CNAME
   - Name: `ops.goblin`
   - Target: `9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com`
   - Proxy: ON ☁️
   - Click "Save"

## ✅ Verification

After adding all records, you should see them listed:

```
goblin.fuaad.ai        CNAME  goblin-assistant-backend.onrender.com  ☁️ Proxied
api.goblin.fuaad.ai    CNAME  goblin-assistant-backend.onrender.com  ☁️ Proxied
brain.goblin.fuaad.ai  CNAME  goblin-assistant-edge.fuaadabdullah.workers.dev  ☁️ Proxied
ops.goblin.fuaad.ai    CNAME  9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com  ☁️ Proxied
```

## 🔒 Configure SSL (Important!)

While you're in the Cloudflare Dashboard:

1. Click "SSL/TLS" in left sidebar
2. Set SSL/TLS encryption mode to: **Full (strict)**
3. Click "Edge Certificates" tab
4. Enable "Always Use HTTPS" → ON

## 🧪 Test DNS (Wait 5-10 minutes first)

```bash
# Test DNS resolution
dig goblin.fuaad.ai
dig api.goblin.fuaad.ai
dig brain.goblin.fuaad.ai
dig ops.goblin.fuaad.ai
```

## 🚀 After DNS is Active

### 1. Deploy Worker
```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
wrangler deploy
```

### 2. Add Custom Domain to Worker
```bash
wrangler domains add brain.goblin.fuaad.ai
```

Or in Dashboard:
1. Go to: Workers & Pages → goblin-assistant-edge
2. Click "Settings" tab → "Triggers"
3. Under "Custom Domains", click "Add Custom Domain"
4. Enter: `brain.goblin.fuaad.ai`
5. Click "Add Custom Domain"

### 3. Test Endpoints
```bash
# Wait 15-30 minutes for SSL certs, then:
curl -I https://goblin.fuaad.ai
curl https://api.goblin.fuaad.ai/health | jq
curl https://brain.goblin.fuaad.ai/health | jq
curl -I https://ops.goblin.fuaad.ai
```

## 🎉 Done!

All 4 subdomains should now be configured and routing through Cloudflare's edge network.

**Time:** 5 minutes manual setup + 5-30 minutes DNS propagation

---

**Next:** See `NEXT_STEPS.md` for application configuration and deployment.
