# ⚠️ Global API Key vs API Token

## The Issue

Your **Global API Key** (`d95ca35932900677d155c0d2632a31b87cac3`) doesn't work with modern Cloudflare tools like `wrangler`. You need a proper **API Token** instead.

## Quick Fix: Create API Token (2 minutes)

**I've opened the API Tokens page for you!**

### Create Token for Workers

1. Click **"Create Token"**
2. Find **"Edit Cloudflare Workers"** template → Click **"Use template"**
3. Review permissions (should already be set correctly):
   - Account → Workers Scripts → Edit
   - Account → Account Settings → Read
4. Under "Account Resources":
   - Include → Your account (should be pre-selected)
5. Under "Zone Resources":
   - Include → All zones
6. Click **"Continue to summary"**
7. Click **"Create Token"**
8. **COPY THE TOKEN** (you'll only see it once!)

### Update .env File

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
code .env
```

Replace this line:
```env
CF_API_TOKEN_WORKERS="Pvdp4NUXjL7iUggzgvk8v4tfQTX_28Koxq4t-06w"
```

With your new token:
```env
CF_API_TOKEN_WORKERS="your-new-token-here"
```

### Deploy Worker

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
wrangler deploy
```

---

## Meanwhile: Set Up DNS Manually

While you're in the Cloudflare Dashboard, you can add the DNS records:

1. Go back to main dashboard
2. Select `fuaad.ai` zone
3. Click "DNS" → Add these 4 CNAME records:

See **`DNS_RECORDS_CHEATSHEET.md`** for exact values to copy-paste!

---

## Why Global API Key Doesn't Work

- **Global API Key**: Legacy, full account access, insecure
- **API Token**: Modern, scoped permissions, secure, works with wrangler

Cloudflare deprecated Global API Keys for API/CLI tools. You need proper API Tokens.

---

## Next Steps

1. ✅ Create Workers API Token (page is open)
2. ✅ Update `CF_API_TOKEN_WORKERS` in `.env`
3. ✅ Run `wrangler deploy`
4. ✅ Add DNS records manually (see `DNS_RECORDS_CHEATSHEET.md`)
5. ✅ Add custom domain: `wrangler domains add brain.goblin.fuaad.ai`
6. ✅ Test endpoints

**Time:** 5 minutes total
