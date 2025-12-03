# Cloudflare Setup Status & Instructions

## Token Status

We have configured the `.env` file with the provided tokens. Here is the status of each:

1. **Workers Token** (`Pvdp4NUX...`): **✅ VALID**.
   * Used for `wrangler deploy`.
   * You can deploy your edge logic immediately.

2. **DNS Token** (`g4U33sF0...`): **❌ INVALID (Future Date)**.
   * Error: `This API Token can not be used before 2026-04-02`.
   * **Action Required**: Please recreate this token with a start date of "Today" (or 2024/2025).

3. **Account Access Token** (`CHYjlYdsq...`): **⚠️ INSUFFICIENT PERMISSIONS**.
   * Valid, but lacks `Account:Access:Edit` or `Account:Cloudflare Tunnel:Edit`.
   * **Action Required**: Update this token's permissions to include "Account > Cloudflare Tunnel > Edit" and "Account > Access: Apps and Policies > Edit".

## How to Fix & Finish Setup

### 1. Fix DNS Token

Create a new token for **Zone > DNS > Edit** and update `CF_API_TOKEN_DNS` in `.env`.

### 2. Fix Access Token

Update the permissions for the "Account Access" token (or create a new one) with:

* `Account > Cloudflare Tunnel > Edit`
* `Account > Access: Apps and Policies > Edit`

Update `CF_API_TOKEN_ACCESS` in `.env`.

### 3. Run Setup Scripts

Once tokens are fixed:

```bash
# 1. Setup Proxy (DNS)
./setup_proxy.sh

# 2. Setup Zero Trust & Tunnel
./setup_zerotrust.sh
./setup_tunnel.sh
```

### 4. Deploy Workers

The Workers token is valid, so you can deploy now:

```bash
export CLOUDFLARE_API_TOKEN="Pvdp4NUXjL7iUggzgvk8v4tfQTX_28Koxq4t-06w"
wrangler deploy
```
