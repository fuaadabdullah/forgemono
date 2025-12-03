#!/bin/bash
# Quick DNS Setup Script
# Run this after creating a DNS API token

echo "🌐 Adding DNS Records for Goblin Assistant"
echo "=========================================="
echo ""

# Check if Zone ID is provided
ZONE_ID="${CF_ZONE_ID:-}"

if [ -z "$ZONE_ID" ]; then
    echo "❌ CF_ZONE_ID not set"
    echo ""
    echo "Please add to .env file:"
    echo 'CF_ZONE_ID="your-zone-id-here"'
    echo ""
    echo "Or run:"
    echo 'export CF_ZONE_ID="your-zone-id-here"'
    exit 1
fi

# Check for DNS API token
DNS_TOKEN="${CF_API_TOKEN_DNS:-}"
if [ -z "$DNS_TOKEN" ]; then
    echo "❌ CF_API_TOKEN_DNS not set"
    echo ""
    echo "Create token at: https://dash.cloudflare.com/profile/api-tokens"
    echo "Template: 'Edit zone DNS'"
    exit 1
fi

echo "✅ Zone ID: $ZONE_ID"
echo "✅ DNS Token configured"
echo ""

# Function to create DNS record
create_dns_record() {
    local name=$1
    local target=$2
    local record_type="CNAME"

    echo "📝 Creating: $name.fuaad.ai → $target"

    # Check if record exists
    EXISTING=$(curl -s -X GET \
        "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=$name.fuaad.ai" \
        -H "Authorization: Bearer $DNS_TOKEN" \
        -H "Content-Type: application/json")

    RECORD_ID=$(echo "$EXISTING" | jq -r '.result[0].id // empty')

    if [ -n "$RECORD_ID" ]; then
        echo "   ⚠️  Record exists, updating..."
        RESPONSE=$(curl -s -X PUT \
            "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
            -H "Authorization: Bearer $DNS_TOKEN" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"$record_type\",\"name\":\"$name\",\"content\":\"$target\",\"proxied\":true,\"ttl\":1}")
    else
        RESPONSE=$(curl -s -X POST \
            "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
            -H "Authorization: Bearer $DNS_TOKEN" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"$record_type\",\"name\":\"$name\",\"content\":\"$target\",\"proxied\":true,\"ttl\":1}")
    fi

    if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        echo "   ✅ Success"
    else
        echo "   ❌ Failed"
        echo "$RESPONSE" | jq '.errors'
    fi
    echo ""
}

# Create the 3 DNS records
echo "Creating DNS records..."
echo ""

create_dns_record "goblin" "goblin-assistant-backend.onrender.com"
create_dns_record "api.goblin" "goblin-assistant-backend.onrender.com"
create_dns_record "ops.goblin" "9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com"

echo "=========================================="
echo "✅ DNS Setup Complete!"
echo ""
echo "Test DNS propagation:"
echo "  dig goblin.fuaad.ai"
echo "  dig api.goblin.fuaad.ai"
echo "  dig ops.goblin.fuaad.ai"
echo ""
echo "Note: DNS may take 5-30 minutes to propagate"
