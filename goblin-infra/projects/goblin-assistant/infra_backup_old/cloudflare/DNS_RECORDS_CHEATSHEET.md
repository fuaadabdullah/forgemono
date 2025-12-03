# 🚀 Quick Setup: Add 4 DNS Records

**Cloudflare Dashboard is open for you!**

---

## Copy-Paste These Values

### ✅ Record 1: Frontend
```
Type: CNAME
Name: goblin
Target: goblin-assistant.fly.dev
Proxy: ON (orange cloud)
```

### ✅ Record 2: Backend API
```
Type: CNAME
Name: api.goblin
Target: goblin-assistant.fly.dev
Proxy: ON (orange cloud)
```

### ✅ Record 3: Brain (LLM Gateway)
```
Type: CNAME
Name: brain.goblin
Target: goblin-assistant-edge.fuaadabdullah.workers.dev
Proxy: ON (orange cloud)
```

### ✅ Record 4: Ops (Admin Panel)
```
Type: CNAME
Name: ops.goblin
Target: 9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com
Proxy: ON (orange cloud)
```

---

## Steps

1. Select `fuaad.ai` zone in dashboard
2. Click "DNS" → "Add record"
3. Copy-paste values from above (4 times, once for each record)
4. Make sure orange cloud ☁️ is ON for all
5. Click "Save" for each

---

## After Adding Records

Run these commands:

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare

# Deploy worker
wrangler deploy

# Add custom domain
wrangler domains add brain.goblin.fuaad.ai

# Test (wait 5-10 min first)
dig goblin.fuaad.ai
curl -I https://goblin.fuaad.ai
```

---

**Full instructions:** See `MANUAL_DNS_SETUP.md`
