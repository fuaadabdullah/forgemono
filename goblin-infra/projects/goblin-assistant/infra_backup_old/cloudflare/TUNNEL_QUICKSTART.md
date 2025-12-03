# Cloudflare Tunnel Quick Start

## What is This?

Cloudflare Tunnel allows you to securely expose your backend API without opening any public ports. All traffic is routed through Cloudflare's network.

## Tunnel Details

- **Tunnel ID**: `9c780bd1-ac63-4d6c-afb1-787a2867e5dd`
- **Tunnel Name**: `goblin-tunnel`
- **Config File**: `tunnel-config.yml`
- **Credentials**: `goblin-tunnel-creds.json` (keep secret!)

## Prerequisites

```bash
# Install cloudflared (if not already installed)
brew install cloudflare/cloudflare/cloudflared

# Verify installation
cloudflared version
```

## Starting the Tunnel

### Option 1: Using Config File

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
cloudflared tunnel --config tunnel-config.yml run
```

### Option 2: Direct Command

```bash
cloudflared tunnel run goblin-tunnel
```

## Configuration

Edit `tunnel-config.yml` to route traffic to your backend:

```yaml
tunnel: 9c780bd1-ac63-4d6c-afb1-787a2867e5dd
credentials-file: /path/to/goblin-tunnel-creds.json

ingress:
  # Route API traffic to your backend
  - hostname: api.yourdomain.com
    service: http://localhost:8000

  # Route admin dashboard
  - hostname: admin.yourdomain.com
    service: http://localhost:3001

  # Catch-all rule (required)
  - service: http_status:404
```

## Common Commands

### Check Tunnel Status

```bash
cloudflared tunnel info goblin-tunnel
```

### List All Tunnels

```bash
cloudflared tunnel list
```

### View Tunnel Connections

```bash
cloudflared tunnel route get
```

### Run in Background

```bash
# Using nohup
nohup cloudflared tunnel --config tunnel-config.yml run > tunnel.log 2>&1 &

# Using systemd (Linux)
sudo cloudflared service install
sudo systemctl start cloudflared
```

## Testing

### 1. Start Your Backend

```bash
# Example: Start FastAPI backend
cd /path/to/backend
uvicorn main:app --port 8000
```

### 2. Start the Tunnel

```bash
cloudflared tunnel --config tunnel-config.yml run
```

### 3. Test Connection

```bash
# Once you have a domain configured:
curl https://api.yourdomain.com/health
```

## Troubleshooting

### Tunnel Won't Start

```bash
# Check credentials file exists
ls -la goblin-tunnel-creds.json

# Verify tunnel exists in Cloudflare
cloudflared tunnel list | grep goblin-tunnel

# Check logs for errors
cloudflared tunnel --config tunnel-config.yml run --loglevel debug
```

### Connection Issues

```bash
# Test local backend is running
curl http://localhost:8000/health

# Check tunnel config is valid
cat tunnel-config.yml

# Verify credentials
cloudflared tunnel info goblin-tunnel
```

## Integration with Worker

Your Worker is already configured to proxy traffic. Once the tunnel is running:

1. Worker receives request at `https://goblin-assistant-edge.fuaadabdullah.workers.dev`
2. Worker performs edge logic (rate limiting, sanitization, caching)
3. Worker forwards valid requests through tunnel to your backend
4. Backend processes request and responds
5. Worker caches response (if GET) and returns to client

## Next Steps

1. **Get a Domain**: Add your domain to Cloudflare
2. **Configure DNS**: Run `./setup_proxy.sh` to create DNS records
3. **Update Tunnel Config**: Point `hostname` to your domain
4. **Start Backend**: Launch your API server
5. **Start Tunnel**: Run `cloudflared tunnel run`
6. **Test End-to-End**: Make requests through your domain

## Security Notes

- ✅ **No open ports** on your server
- ✅ **Encrypted traffic** through Cloudflare
- ✅ **DDoS protection** built-in
- ✅ **Zero Trust Access** ready (once domain configured)
- ❌ **Never commit** `goblin-tunnel-creds.json` to git (already in `.gitignore`)

## Resources

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Configuration Reference](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/configuration/)
- [Troubleshooting Guide](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/troubleshooting/)
