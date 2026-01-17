# Cloudflare DNS Configuration Guide

## Overview

This guide provides step-by-step instructions for configuring DNS records in Cloudflare for the Goblin Assistant hybrid infrastructure.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLOUDFLARE (Security Layer)                         │
│   • DNS Management  • DDoS Protection  • Tunnel to Kamatera  • WAF/CDN     │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────────────────────────┐
│    VERCEL     │    │    FLY.IO     │    │           KAMATERA                │
│   (Frontend)  │───▶│   (Backend)   │───▶│  Server 1: LLM Inference (24GB)   │
│               │    │               │    │  Server 2: Data/Heavy Compute     │
│ • React/Vite  │    │ • FastAPI     │    │  • Local LLMs (Ollama)           │
│ • Static CDN  │    │ • Auth/API    │    │  • PostgreSQL/Redis              │
│ • Edge Cache  │    │ • Routing     │    │  • Vector DB                     │
└───────────────┘    │ • Caching     │    │  • Background Workers            │
                     └───────────────┘    └───────────────────────────────────┘
```

## Server Information

### Kamatera Server 1 (LLM Inference)
- **IP Address**: 192.175.23.150
- **Hostname**: 192-175-23-150.cloud-xip.com
- **Private IP**: 172.16.0.1
- **Configuration**: 4 CPU, 24GB RAM, 80GB Storage
- **Services**: Ollama (port 8002), Llama.cpp (port 8003)

### Kamatera Server 2 (Data/Compute)
- **IP Address**: 45.61.51.220
- **Hostname**: 45-61-51-220.cloud-xip.com
- **Private IP**: 172.16.0.2
- **Configuration**: 2 CPU, 12GB RAM, 120GB Storage
- **Services**: PostgreSQL (port 5432), Redis (port 6379), Goblin Router (port 8000)

### Fly.io Backend
- **URL**: https://goblin-assistant.fly.dev
- **Region**: IAD (Washington D.C.)
- **Services**: FastAPI backend, Authentication, API routing

### Vercel Frontend
- **URL**: https://goblin-assistant.vercel.app
- **Framework**: Vite/React
- **Services**: Static site hosting, CDN distribution

## DNS Records Configuration

### Step 1: Access Cloudflare Dashboard

1. Log into your Cloudflare account
2. Select your domain (e.g., `goblin-assistant.dev`)
3. Navigate to **DNS** → **Records**

### Step 2: Configure Primary Records

#### A. Root Domain (A Record)
```
Type: A
Name: @
Content: 192.175.23.150
TTL: Auto
Proxy: 🟡 Proxied (orange cloud)
```

#### B. www Subdomain (CNAME)
```
Type: CNAME
Name: www
Content: goblin-assistant.dev
TTL: Auto
Proxy: 🟡 Proxied (orange cloud)
```

### Step 3: Configure Cloudflare Tunnel Records

After running the tunnel setup script, create these CNAME records:

#### Server 1 Tunnels
```
Type: CNAME
Name: server1
Content: server1.cfargotunnel.com
TTL: Auto
Proxy: 🟡 Proxied (orange cloud)
```

```
Type: CNAME
Name: ollama
Content: server1.cfargotunnel.com
TTL: Auto
Proxy: 🟡 Proxied (orange cloud)
```

#### Server 2 Tunnels
```
Type: CNAME
Name: server2
Content: server2.cfargotunnel.com
TTL: Auto
Proxy: 🟡 Proxied (orange cloud)
```

```
Type: CNAME
Name: api
Content: server2.cfargotunnel.com
TTL: Auto
Proxy: 🟡 Proxied (orange cloud)
```

```
Type: CNAME
Name: redis
Content: server2-redis.cfargotunnel.com
TTL: Auto
Proxy: 🟡 Proxied (orange cloud)
```

```
Type: CNAME
Name: postgres
Content: server2-postgres.cfargotunnel.com
TTL: Auto
Proxy: 🟡 Proxied (orange cloud)
```

### Step 4: Configure Fly.io Backend

```
Type: CNAME
Name: api
Content: goblin-assistant.fly.dev
TTL: Auto
Proxy: 🟡 Proxied (orange cloud)
```

### Step 5: Configure Vercel Frontend

```
Type: CNAME
Name: app
Content: goblin-assistant.vercel.app
TTL: Auto
Proxy: 🟡 Proxied (orange cloud)
```

## SSL/TLS Configuration

### Step 1: SSL/TLS Settings

1. Navigate to **SSL/TLS** → **Overview**
2. Set encryption mode to **Full (strict)**
3. Enable **Always Use HTTPS**
4. Enable **Automatic HTTPS Rewrites**

### Step 2: Certificate Settings

1. Go to **SSL/TLS** → **Edge Certificates**
2. Enable **Always Use HTTPS**
3. Enable **HTTP Strict Transport Security (HSTS)**
4. Set **Minimum TLS Version** to **1.2**

### Step 3: Origin Server Settings

1. Go to **SSL/TLS** → **Origin Server**
2. Enable **Authenticated Origin Pulls** (recommended for security)
3. Configure origin certificates if needed

## Security Configuration

### Step 1: Web Application Firewall (WAF)

1. Navigate to **Security** → **WAF**
2. Enable **Managed Rules**
3. Configure custom rules:

#### Rate Limiting Rule
```
Expression: (http.request.uri.path contains "/api/")
Action: Challenge
Sensitivity: Medium
```

#### Bot Protection
```
Expression: (cf.threat_score gt 14)
Action: Challenge
```

### Step 2: DDoS Protection

1. Go to **Security** → **DDoS**
2. Enable **DDoS protection for HTTP**
3. Set protection level to **Medium**
4. Enable **Always Online** (for static content)

### Step 3: Security Level

1. Go to **Security** → **Settings**
2. Set **Security Level** to **Medium**
3. Enable **Browser Integrity Check**
4. Configure **Challenge Passage** settings

## Speed & Performance Optimization

### Step 1: Auto Minify

1. Go to **Speed** → **Optimization**
2. Enable **Auto Minify** for:
   - HTML
   - CSS
   - JavaScript

### Step 2: Compression

1. Enable **Brotli compression**
2. Enable **Gzip compression** (as fallback)

### Step 3: Caching

1. Go to **Caching** → **Configuration**
2. Set **Browser Cache TTL** to **4 hours**
3. Enable **Always Online**
4. Configure **Cache Level**: **Standard**

### Step 4: Page Rules (Optional)

For specific optimization:

```
URL Pattern: goblin-assistant.dev/static/*
Settings:
- Cache Level: Cache Everything
- Edge Cache TTL: 1 month
- Browser Cache TTL: 1 week
```

## Monitoring & Analytics

### Step 1: Cloudflare Analytics

1. Go to **Analytics & Logs** → **Analytics**
2. Enable **Web Analytics**
3. Configure retention settings

### Step 2: Log Settings

1. Go to **Analytics & Logs** → **Logs**
2. Enable **Logpush** for detailed logging
3. Configure log retention period

### Step 3: Alerts

1. Go to **Notifications** → **Destinations**
2. Create email/webhook notifications for:
   - DDoS alerts
   - SSL certificate expiration
   - High error rates
   - Security events

## DNS Records Summary

After completing all configurations, your DNS records should look like this:

| Type | Name | Content | Proxy | TTL |
|------|------|---------|-------|-----|
| A | @ | 192.175.23.150 | 🟡 | Auto |
| CNAME | www | goblin-assistant.dev | 🟡 | Auto |
| CNAME | server1 | server1.cfargotunnel.com | 🟡 | Auto |
| CNAME | ollama | server1.cfargotunnel.com | 🟡 | Auto |
| CNAME | server2 | server2.cfargotunnel.com | 🟡 | Auto |
| CNAME | api | server2.cfargotunnel.com | 🟡 | Auto |
| CNAME | redis | server2-redis.cfargotunnel.com | 🟡 | Auto |
| CNAME | postgres | server2-postgres.cfargotunnel.com | 🟡 | Auto |

## Testing DNS Configuration

### Step 1: Verify DNS Propagation

Use these commands to verify DNS configuration:

```bash
# Check A record
dig goblin-assistant.dev

# Check CNAME records
dig api.goblin-assistant.dev
dig server1.goblin-assistant.dev
dig server2.goblin-assistant.dev

# Check tunnel endpoints
dig ollama.goblin-assistant.dev
dig redis.goblin-assistant.dev
dig postgres.goblin-assistant.dev
```

### Step 2: Test SSL/TLS

```bash
# Test SSL certificate
curl -I https://goblin-assistant.dev

# Test specific tunnel endpoints
curl -I https://api.goblin-assistant.dev/health
curl -I https://server1.goblin-assistant.dev/health
curl -I https://server2.goblin-assistant.dev/health
```

### Step 3: Test Performance

```bash
# Test response times
curl -w "@curl-format.txt" -o /dev/null -s https://goblin-assistant.dev
```

Create `curl-format.txt`:
```
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
```

## Troubleshooting

### Common Issues

1. **DNS Not Propagating**
   - Wait 24-48 hours for full propagation
   - Check DNS status with online tools
   - Verify record configuration

2. **SSL Certificate Errors**
   - Ensure origin servers have valid certificates
   - Check "Full (strict)" mode is enabled
   - Verify tunnel configuration

3. **Tunnel Not Connecting**
   - Check tunnel service status: `systemctl status cloudflared-*`
   - Review tunnel logs: `journalctl -u cloudflared-*`
   - Verify Cloudflare authentication

4. **High Error Rates**
   - Check origin server health
   - Review WAF rules for false positives
   - Monitor Cloudflare Analytics

### Support Resources

- **Cloudflare Documentation**: https://developers.cloudflare.com/
- **Tunnel Documentation**: https://developers.cloudflare.com/cloudflare-one/
- **DNS Configuration**: https://developers.cloudflare.com/dns/
- **SSL/TLS Settings**: https://developers.cloudflare.com/ssl/

## Security Best Practices

1. **Keep Certificates Updated**
   - Monitor certificate expiration
   - Set up automated renewal
   - Use Cloudflare's managed certificates

2. **Regular Security Audits**
   - Review WAF rules monthly
   - Monitor security events
   - Update security settings as needed

3. **Monitor Performance**
   - Set up alerts for high latency
   - Monitor cache hit rates
   - Review analytics regularly

4. **Backup Configuration**
   - Export DNS records regularly
   - Document custom rules
   - Keep tunnel configurations backed up

This configuration provides a secure, high-performance DNS setup for the Goblin Assistant hybrid infrastructure with Cloudflare as the security and performance layer.
