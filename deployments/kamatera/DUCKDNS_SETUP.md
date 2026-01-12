# DuckDNS Configuration for Goblin Assistant

## Overview

This guide sets up a public domain for Goblin Assistant using **DuckDNS** - a free dynamic DNS service that gives you a subdomain like `goblinossistant.duckdns.org`.

## Why DuckDNS?

- ✅ **100% Free** - No costs, no credit card required
- ✅ **Easy Setup** - 5-minute configuration
- ✅ **Dynamic IP Support** - Automatic updates every 5 minutes
- ✅ **SSL Compatible** - Works with Let's Encrypt for HTTPS
- ✅ **No Registration Hassles** - Simple OAuth login (Google, GitHub, etc.)

## Available Domain Options

Since you wanted something similar to "GoblinOSAssistant.org", here are the available DuckDNS subdomains you can register:

### Recommended Options:
1. `goblinossistant.duckdns.org` (closest to your request)
2. `goblinai.duckdns.org`
3. `goblinos-assistant.duckdns.org`
4. `goblin-chat.duckdns.org`
5. `goblindev.duckdns.org`
6. `goblinhelper.duckdns.org`

**Note:** `.org` domains cost money through domain registrars like Namecheap or GoDaddy (~$10-15/year). DuckDNS gives you a free `.duckdns.org` subdomain instantly!

## Setup Instructions

### Step 1: Register DuckDNS Account

1. Visit [https://www.duckdns.org](https://www.duckdns.org)
2. Sign in with Google, GitHub, or other OAuth provider
3. Register your preferred subdomain (e.g., `goblinossistant`)
4. Copy your **token** from the top of the page

### Step 2: Run Setup Script on Kamatera Server

SSH into your Kamatera server and run:

```bash
# Navigate to deployment directory
cd /root/ForgeMonorepo/deployments/kamatera

# Make script executable
chmod +x setup-duckdns.sh

# Run setup (will prompt for token and domain)
sudo ./setup-duckdns.sh
```

Or set environment variables first:

```bash
export DUCKDNS_DOMAIN="goblinossistant"
export DUCKDNS_TOKEN="your-token-from-duckdns-org"
sudo -E ./setup-duckdns.sh
```

### Step 3: Install SSL Certificate

Once DuckDNS is configured, secure your domain with SSL:

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d goblinossistant.duckdns.org

# Follow the prompts:
# - Enter email address
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (recommended)
```

Certbot will:
- Generate SSL certificates
- Automatically configure nginx
- Set up auto-renewal

### Step 4: Update Docker Compose

Edit your docker-compose file to include nginx with the new configuration:

```bash
cd /root/ForgeMonorepo/deployments/kamatera

# Copy the nginx.conf
cp nginx.conf /etc/nginx/nginx.conf

# Or update docker-compose to mount it
```

Update `docker-compose.kamatera.yml`:

```yaml
  nginx:
    image: nginx:alpine
    container_name: goblin-nginx
    restart: unless-stopped
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - /var/www/certbot:/var/www/certbot:ro
    depends_on:
      - goblin-router
      - goblin-frontend
```

### Step 5: Update Environment Variables

Update your `.env` file with the new domain:

```bash
# Edit .env file
nano /root/ForgeMonorepo/deployments/kamatera/.env

# Update these values:
BACKEND_URL=https://goblinossistant.duckdns.org
FRONTEND_URL=https://goblinossistant.duckdns.org
API_BASE_URL=https://goblinossistant.duckdns.org/api
```

### Step 6: Restart Services

```bash
# Restart nginx
sudo systemctl restart nginx

# Restart docker containers
cd /root/ForgeMonorepo/deployments/kamatera
docker-compose -f docker-compose.kamatera.yml restart

# Verify everything is running
docker-compose -f docker-compose.kamatera.yml ps
```

## Verification

### Test DuckDNS Updates

```bash
# Check DuckDNS update log
tail -f /var/log/duckdns.log

# Manually trigger update
sudo /usr/local/bin/duckdns-update.sh

# Verify DNS resolution
dig goblinossistant.duckdns.org
nslookup goblinossistant.duckdns.org
```

### Test HTTPS Access

```bash
# Test from server
curl -I https://goblinossistant.duckdns.org

# Test health endpoint
curl https://goblinossistant.duckdns.org/health

# Test API
curl https://goblinossistant.duckdns.org/api/health
```

### Test from Browser

1. Visit `https://goblinossistant.duckdns.org`
2. Verify SSL certificate is valid (green padlock)
3. Test chat functionality
4. Check browser console for errors

## Troubleshooting

### DuckDNS Not Updating

```bash
# Check cron job is running
crontab -l | grep duckdns

# Check update log
tail -n 50 /var/log/duckdns.log

# Manually test update
curl "https://www.duckdns.org/update?domains=goblinossistant&token=YOUR_TOKEN&ip="
```

### SSL Certificate Issues

```bash
# Test nginx configuration
sudo nginx -t

# Check certificate expiry
sudo certbot certificates

# Force certificate renewal
sudo certbot renew --force-renewal
```

### Nginx Not Starting

```bash
# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Verify configuration
sudo nginx -t

# Check if ports are in use
sudo netstat -tlnp | grep -E ':80|:443'
```

### Domain Not Resolving

```bash
# Check public IP
curl https://api.ipify.org

# Verify DuckDNS has correct IP
dig goblinossistant.duckdns.org

# Force DNS cache clear
sudo systemd-resolve --flush-caches  # Ubuntu/Debian
```

## Maintenance

### Automatic Updates

DuckDNS updates automatically every 5 minutes via cron:

```bash
# View cron job
crontab -l

# Edit if needed
crontab -e
```

### SSL Certificate Renewal

Certbot auto-renews certificates. To verify:

```bash
# Test renewal process
sudo certbot renew --dry-run

# Check renewal timer
sudo systemctl status certbot.timer
```

### Monitor Updates

```bash
# Real-time log monitoring
tail -f /var/log/duckdns.log

# Check recent updates
tail -n 20 /var/log/duckdns.log
```

## Custom Domain Upgrade (Optional)

If you later want a custom `.org` domain like `goblinossistant.org`:

1. **Purchase domain** from Namecheap, GoDaddy, etc. (~$10-15/year)
2. **Point DNS** to your Kamatera server IP
3. **Update nginx** server_name
4. **Get new SSL certificate** for the custom domain
5. **Keep DuckDNS** as a backup/development domain

## Architecture

```
Internet
    │
    ↓
DuckDNS (goblinossistant.duckdns.org)
    │
    ↓
Kamatera Server (Your Public IP)
    │
    ↓
Nginx (Port 80/443)
    ├─→ Frontend (React) → Port 3000
    ├─→ Backend API → Port 8000
    └─→ WebSocket → Port 8000/ws
```

## Security Considerations

### Firewall Rules

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block direct access to backend
sudo ufw deny 8000/tcp
sudo ufw deny 3000/tcp
```

### Rate Limiting

The nginx.conf includes:
- **10 requests/second** per IP for API endpoints
- **20 burst requests** allowed
- **10 concurrent connections** per IP

### SSL Configuration

- ✅ TLS 1.2 and 1.3 only
- ✅ Strong cipher suites
- ✅ HSTS enabled
- ✅ Certificate auto-renewal

## Cost Comparison

| Service | Cost | Features |
|---------|------|----------|
| DuckDNS | **$0/year** | Free subdomain, dynamic DNS, SSL compatible |
| .org domain | $10-15/year | Custom branding, professional appearance |
| Cloudflare (with domain) | $10-15/year | Domain + CDN + DDoS protection |
| AWS Route 53 | $0.50/month | Hosted DNS service |

**Recommendation:** Start with DuckDNS (free), upgrade to custom domain later if needed.

## Files Created

- `/deployments/kamatera/setup-duckdns.sh` - DuckDNS setup script
- `/deployments/kamatera/nginx.conf` - Nginx reverse proxy configuration
- `/usr/local/bin/duckdns-update.sh` - Auto-update script (on server)
- `/var/log/duckdns.log` - Update log (on server)
- `/root/goblin-assistant/.env.duckdns` - DuckDNS environment variables (on server)

## Next Steps

1. ✅ Run `setup-duckdns.sh` on your Kamatera server
2. ✅ Install SSL certificate with Certbot
3. ✅ Update nginx configuration
4. ✅ Restart services
5. ✅ Test access via browser
6. 📱 Update mobile app to use new domain
7. 📝 Update documentation with new URL
8. 🔐 Configure CORS for new domain

## Support

If you encounter issues:
1. Check logs: `/var/log/duckdns.log` and `/var/log/nginx/error.log`
2. Verify DuckDNS dashboard shows correct IP
3. Test DNS resolution: `dig goblinossistant.duckdns.org`
4. Check SSL: `curl -vI https://goblinossistant.duckdns.org`

---

**Your Goblin Assistant will be publicly accessible at:**
## 🌐 https://goblinossistant.duckdns.org

