# Turnstile Manual Setup Guide

Since the API token needs specific Turnstile permissions, follow these steps to create widgets manually:

## Step 1: Create API Token (if needed)

1. Go to: https://dash.cloudflare.com/profile/api-tokens
2. Click **"Create Token"**
3. Click **"Create Custom Token"**
4. Configure:
   - **Token name**: "Turnstile Management"
   - **Permissions**:
     - Account > Account Settings > Read
     - Account > Turnstile > Edit
   - **Account Resources**: Include your account
5. Click **"Continue to summary"** → **"Create Token"**
6. Copy the token and add to `.env`:
   ```bash
   CF_API_TOKEN_TURNSTILE="your-new-token-here"
   ```

## Step 2: Create Widgets via Dashboard

### Option A: Via Dashboard (Easier)

1. Go to: https://dash.cloudflare.com/[YOUR_ACCOUNT_ID]/turnstile
2. Click **"Add Site"**

**Widget 1: Login Forms (Managed)**
- **Site name**: Goblin Assistant - Login
- **Domain**: Your domain (e.g., `app.yourdomain.com`) and `localhost`
- **Widget Mode**: Managed
- Click **"Create"**
- Copy the **Site Key** and **Secret Key**

**Widget 2: API Calls (Invisible)**
- **Site name**: Goblin Assistant - API
- **Domain**: Your domain and `localhost`
- **Widget Mode**: Invisible
- Click **"Create"**
- Copy the **Site Key** and **Secret Key**

### Option B: Run Script (Once Token is Ready)

```bash
cd apps/goblin-assistant/infra/cloudflare
./setup_turnstile.sh
```

## Step 3: Add Keys to Environment Files

**Frontend** (`apps/goblin-assistant/.env.local`):
```bash
NEXT_PUBLIC_TURNSTILE_SITE_KEY_MANAGED="1x00000000000000000000AA"
NEXT_PUBLIC_TURNSTILE_SITE_KEY_INVISIBLE="1x00000000000000000000BB"
```

**Backend/Worker** (`apps/goblin-assistant/infra/cloudflare/.env`):
```bash
TURNSTILE_SECRET_KEY_MANAGED="0x4AAF..."
TURNSTILE_SECRET_KEY_INVISIBLE="0x4BBF..."
```

**Worker Config** (`wrangler.toml`):
```toml
[vars]
# ... existing vars
TURNSTILE_SECRET_KEY_MANAGED = "0x4AAF..."
TURNSTILE_SECRET_KEY_INVISIBLE = "0x4BBF..."
```

## Step 4: Deploy Enhanced Worker

```bash
cd apps/goblin-assistant/infra/cloudflare

# Backup current worker
cp worker.js worker_backup.js

# Use Turnstile-enabled worker
cp worker_with_turnstile.js worker.js

# Deploy
wrangler deploy
```

## Testing

After setup, test with:

```bash
# Should succeed (with valid Turnstile token)
curl -X POST https://goblin-assistant-edge.fuaadabdullah.workers.dev/api/chat \
  -H "Content-Type: application/json" \
  -H "X-Turnstile-Token: valid-token-from-frontend" \
  -d '{"message": "Hello"}'

# Should fail (no Turnstile token)
curl -X POST https://goblin-assistant-edge.fuaadabdullah.workers.dev/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
# Response: {"error": "Turnstile token required"}
```

## Quick Links

- **Turnstile Dashboard**: https://dash.cloudflare.com/[ACCOUNT_ID]/turnstile
- **API Tokens**: https://dash.cloudflare.com/profile/api-tokens
- **Integration Guide**: TURNSTILE_INTEGRATION.md
