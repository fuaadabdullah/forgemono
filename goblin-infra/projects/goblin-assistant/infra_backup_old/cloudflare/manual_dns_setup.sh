#!/bin/bash
# Manual DNS setup using Cloudflare API
# This bypasses the token verification and goes straight to DNS record creation

set -e

ACCOUNT_ID="a9c52e892f7361bab3bfd084c6ffaccb"
WORKER_URL="goblin-assistant-edge.fuaadabdullah.workers.dev"

echo "🌐 Manual DNS Setup for Goblin Assistant"
echo "=========================================="
echo ""

# Prompt for zone ID
read -p "Enter your fuaad.ai Zone ID (find it in Cloudflare Dashboard): " ZONE_ID

# Prompt for API token
read -p "Enter your Cloudflare API Token: " API_TOKEN

echo ""
echo "Creating DNS records..."
echo ""

# Function to create DNS record
create_dns() {
    local name=$1
    local type=$2
    local content=$3

    echo "Creating $name.$ROOT_DOMAIN ($type → $content)..."

    response=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
        -H "Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json" \
        --data "{\"type\":\"$type\",\"name\":\"$name\",\"content\":\"$content\",\"proxied\":true,\"ttl\":1}")

    if echo "$response" | jq -e '.success' > /dev/null 2>&1; then
        echo "✅ Success"
    else
        echo "❌ Failed"
        echo "$response" | jq '.errors'
    fi
    echo ""
}

# Get root domain
read -p "Enter your root domain (e.g., fuaad.ai): " ROOT_DOMAIN

echo ""
echo "What are your targets for each subdomain?"
echo ""

# Frontend
read -p "Frontend (goblin.$ROOT_DOMAIN) - CNAME or IP: " FRONTEND_TARGET
FRONTEND_TYPE="CNAME"
if [[ $FRONTEND_TARGET =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    FRONTEND_TYPE="A"
fi

# Backend
read -p "Backend API (api.goblin.$ROOT_DOMAIN) - CNAME or IP: " BACKEND_TARGET
BACKEND_TYPE="CNAME"
if [[ $BACKEND_TARGET =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    BACKEND_TYPE="A"
fi

# Brain (default to Worker)
read -p "Brain/Inference (brain.goblin.$ROOT_DOMAIN) [press Enter for $WORKER_URL]: " BRAIN_TARGET
BRAIN_TARGET=${BRAIN_TARGET:-$WORKER_URL}

# Ops
read -p "Ops/Admin (ops.goblin.$ROOT_DOMAIN) - CNAME or IP: " OPS_TARGET
OPS_TYPE="CNAME"
if [[ $OPS_TARGET =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    OPS_TYPE="A"
fi

echo ""
echo "Creating all DNS records..."
echo ""

# Create records
create_dns "goblin" "$FRONTEND_TYPE" "$FRONTEND_TARGET"
create_dns "api.goblin" "$BACKEND_TYPE" "$BACKEND_TARGET"
create_dns "brain.goblin" "CNAME" "$BRAIN_TARGET"
create_dns "ops.goblin" "$OPS_TYPE" "$OPS_TARGET"

echo "=========================================="
echo "✅ DNS Setup Complete!"
echo ""
echo "Your subdomains:"
echo "  https://goblin.$ROOT_DOMAIN"
echo "  https://api.goblin.$ROOT_DOMAIN"
echo "  https://brain.goblin.$ROOT_DOMAIN"
echo "  https://ops.goblin.$ROOT_DOMAIN"
echo ""
echo "DNS propagation can take 5-30 minutes."
echo ""
