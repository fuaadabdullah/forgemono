# Goblin Subdomains - Quick Reference Card

## 🌐 Production URLs

```
https://goblin.fuaad.ai        → Frontend application
https://api.goblin.fuaad.ai    → Backend API
https://brain.goblin.fuaad.ai  → LLM inference gateway
https://ops.goblin.fuaad.ai    → Admin panel (Zero Trust)
```

## 🚀 Quick Setup (3 commands)

```bash
# 1. Get new API token & update .env
open https://dash.cloudflare.com/profile/api-tokens
code /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare/.env

# 2. Run setup script
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
./setup_subdomains.sh

# 3. Deploy Worker & add custom domain
wrangler deploy
wrangler domains add brain.goblin.fuaad.ai
```

## 📋 Setup Script Answers

| Prompt | Answer |
|--------|--------|
| Domain | `fuaad.ai` |
| Frontend | `goblin-assistant.fly.dev` |
| Backend | `goblin-assistant.fly.dev` |
| Brain | Press Enter (default) |
| Ops | `9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com` |

## ✅ Test Commands

```bash
# Test DNS
dig goblin.fuaad.ai +short
dig api.goblin.fuaad.ai +short
dig brain.goblin.fuaad.ai +short
dig ops.goblin.fuaad.ai +short

# Test HTTPS
curl -I https://goblin.fuaad.ai
curl https://api.goblin.fuaad.ai/health | jq
curl https://brain.goblin.fuaad.ai/health | jq
curl -I https://ops.goblin.fuaad.ai
```

## 📚 Documentation

- `NEXT_STEPS.md` - Complete next steps guide
- `SUBDOMAIN_QUICK_START.md` - Quick automated setup
- `GET_API_TOKEN.md` - Token + manual setup
- `DEPLOYMENT_CHECKLIST.md` - Full checklist

## 🔗 Dashboards

```bash
# Cloudflare
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb

# Zero Trust
open https://one.dash.cloudflare.com/

# Turnstile
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/turnstile
```

---

**Status**: ⏳ Waiting for API token → Run setup script
**Time**: ~10 min setup + 5-30 min DNS propagation
