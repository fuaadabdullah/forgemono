#!/bin/bash

##############################################################################
# Quick DuckDNS Setup for Goblin Assistant
# 
# This script provides a one-liner setup for DuckDNS on your Kamatera server
##############################################################################

set -e

echo "🚀 Goblin Assistant DuckDNS Quick Setup"
echo ""
echo "Step 1: Register at https://www.duckdns.org"
echo "  - Sign in with Google/GitHub"
echo "  - Register subdomain: goblinossistant (or your choice)"
echo "  - Copy your token"
echo ""
echo "Step 2: Run this on your Kamatera server:"
echo ""
echo "  ssh root@YOUR_SERVER_IP"
echo "  cd /root"
echo "  git clone https://github.com/yourusername/ForgeMonorepo.git || cd ForgeMonorepo && git pull"
echo "  cd ForgeMonorepo/deployments/kamatera"
echo "  chmod +x setup-duckdns.sh"
echo "  export DUCKDNS_DOMAIN=goblinossistant"
echo "  export DUCKDNS_TOKEN=your-token-here"
echo "  sudo -E ./setup-duckdns.sh"
echo ""
echo "Step 3: Install SSL:"
echo ""
echo "  sudo apt-get update"
echo "  sudo apt-get install -y certbot python3-certbot-nginx"
echo "  sudo certbot --nginx -d goblinossistant.duckdns.org"
echo ""
echo "Step 4: Deploy with nginx:"
echo ""
echo "  cd /root/ForgeMonorepo/deployments/kamatera"
echo "  docker-compose -f docker-compose.kamatera.yml up -d"
echo ""
echo "✅ Your site will be live at: https://goblinossistant.duckdns.org"
echo ""
