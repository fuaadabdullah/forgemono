#!/bin/bash

# Setup Cloudflare Proxy (DNS)
# This script helps configure Cloudflare DNS records to proxy traffic (Orange Cloud).

# Prerequisites:
# - Cloudflare API Token with DNS:Edit permissions
# - Zone ID for your domain

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "$CF_API_TOKEN_DNS" ] && [ -z "$CF_API_TOKEN" ]; then
  echo "Error: CF_API_TOKEN_DNS (or CF_API_TOKEN) and CF_ZONE_ID environment variables must be set."
  echo "Usage: CF_API_TOKEN_DNS=... CF_ZONE_ID=... ./setup_proxy.sh"
  echo "Or set them in .env file"
  exit 1
fi

# Use specific token if available, otherwise fallback
TOKEN="${CF_API_TOKEN_DNS:-$CF_API_TOKEN}"

DOMAIN="yourdomain.com"
FRONTEND_CNAME="cname.vercel-dns.com" # Example for Vercel
BACKEND_IP="1.2.3.4" # Example IP or CNAME for Backend

echo "Configuring Cloudflare DNS for $DOMAIN..."

# Function to create/update DNS record
update_dns() {
  local type=$1
  local name=$2
  local content=$3
  local proxied=$4

  echo "Setting $name.$DOMAIN ($type) -> $content (Proxied: $proxied)"

  curl -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     --data "{\"type\":\"$type\",\"name\":\"$name\",\"content\":\"$content\",\"proxied\":$proxied}"
}

# 1. Frontend (Vercel)
# update_dns "CNAME" "app" "$FRONTEND_CNAME" true

# 2. Backend API
# update_dns "A" "api" "$BACKEND_IP" true

# 3. Goblin Brain
# update_dns "A" "brain" "$BACKEND_IP" true

echo "DNS configuration complete. Verify in Cloudflare Dashboard."
