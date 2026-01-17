# Kamatera Deployment for Goblin Assistant

This folder contains deployment configurations and scripts for running Goblin Assistant on Kamatera infrastructure.

## Quick Start

### 1. DuckDNS Setup (Public Domain)

Give your Goblin Assistant a public domain like `goblinossistant.duckdns.org`:

```bash
# See DUCKDNS_SETUP.md for full instructions
chmod +x setup-duckdns.sh
sudo ./setup-duckdns.sh
```

**Quick reference:** Run `./quick-duckdns-setup.sh` to see one-liner setup commands.

### 2. Deploy Services

```bash
# Start all services with nginx reverse proxy
docker-compose -f docker-compose.kamatera.yml up -d

# Check status
docker-compose -f docker-compose.kamatera.yml ps
```

### 3. Verify Deployment

```bash
# Run verification script
./verify_kamatera_deployment.sh

# Check your public domain
curl https://goblinossistant.duckdns.org/health
```

## Files

- **docker-compose.kamatera.yml**: Main deployment configuration
- **nginx.conf**: Reverse proxy with SSL support
- **setup-duckdns.sh**: DuckDNS dynamic DNS setup script
- **DUCKDNS_SETUP.md**: Complete DuckDNS setup guide
- **quick-duckdns-setup.sh**: Quick reference for DuckDNS setup
- **verify_kamatera_deployment.sh**: Infrastructure verification
- **.env**: Environment variables (update with your DuckDNS settings)

## Public Access

After DuckDNS setup, your Goblin Assistant will be available at:

🌐 **https://goblinossistant.duckdns.org**

(or your chosen subdomain)

## Architecture

```
Internet → DuckDNS → Kamatera Server → Nginx → Services
                                         ├── Frontend (Port 3000)
                                         ├── Backend API (Port 8000)
                                         └── WebSocket (Port 8000/ws)
```

## Documentation

- [DuckDNS Setup Guide](./DUCKDNS_SETUP.md) - Complete setup instructions
- [Cloudflare Tunnel Setup](./cloudflare-tunnel-setup.sh) - Alternative to DuckDNS
- [Server 1 LLM Setup](./server1-llm-setup.sh) - LLM server configuration
- [Server 2 Data Setup](./server2-data-setup.sh) - Data server configuration
