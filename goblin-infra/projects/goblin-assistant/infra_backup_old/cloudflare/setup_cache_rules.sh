#!/bin/bash
# Setup Cloudflare Cache Rules for Frontend Performance
# Makes your Goblin Assistant feel like it was built by a trillion-dollar startup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Cloudflare Cache Rules Setup"
echo "=================================="
echo ""

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check for required variables
if [ -z "$CF_ZONE_ID" ]; then
    echo "❌ CF_ZONE_ID not set"
    echo ""
    echo "Once you add fuaad.ai to Cloudflare, update .env:"
    echo 'CF_ZONE_ID="your-zone-id-here"'
    exit 1
fi

# Use Workers token for now (can access zones too)
API_TOKEN="${CF_API_TOKEN_WORKERS:-${CF_API_TOKEN}}"
if [ -z "$API_TOKEN" ]; then
    echo "❌ No API token found"
    exit 1
fi

echo "✅ Zone ID: $CF_ZONE_ID"
echo "✅ API Token configured"
echo ""

echo "📋 Cache Rules Overview:"
echo ""
echo "1. Static Assets (JS/CSS/Images) → Cache 1 year (immutable)"
echo "2. Versioned Bundles → Cache 1 year (immutable)"
echo "3. Build Chunks (/assets/, /chunks/) → Cache 1 year"
echo "4. Fonts → Cache 1 year"
echo "5. Animations & Effects → Cache 24h (smooth goblin typing!)"
echo "6. HTML Pages → Cache 5min (quick deploys)"
echo "7. API Endpoints → No cache (handled by brain worker)"
echo ""

read -p "Deploy these cache rules? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

echo ""
echo "🔧 Creating cache rules..."
echo ""

# Get existing rulesets
echo "Fetching existing rulesets..."
RULESETS=$(curl -s -X GET \
    "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/rulesets" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json")

# Check if cache rules phase exists
CACHE_RULESET_ID=$(echo "$RULESETS" | jq -r '.result[] | select(.phase=="http_request_cache_settings") | .id')

if [ -z "$CACHE_RULESET_ID" ] || [ "$CACHE_RULESET_ID" == "null" ]; then
    echo "Creating new cache ruleset..."

    # Create new ruleset
    RESPONSE=$(curl -s -X POST \
        "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/rulesets" \
        -H "Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json" \
        --data '{
          "name": "Goblin Assistant Cache Rules",
          "description": "Performance-optimized caching for frontend",
          "kind": "zone",
          "phase": "http_request_cache_settings",
          "rules": []
        }')

    CACHE_RULESET_ID=$(echo "$RESPONSE" | jq -r '.result.id')
fi

echo "✅ Cache ruleset ID: $CACHE_RULESET_ID"
echo ""

# Deploy cache rules
echo "Deploying cache rules..."

RESPONSE=$(curl -s -X PUT \
    "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/rulesets/$CACHE_RULESET_ID" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    --data @cache_rules_payload.json)

if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "✅ Cache rules deployed successfully!"
    echo ""
    echo "📊 Rules active:"
    echo "$RESPONSE" | jq -r '.result.rules[] | "  ✅ \(.description)"'
else
    echo "❌ Failed to deploy cache rules"
    echo "$RESPONSE" | jq '.errors'
    exit 1
fi

echo ""
echo "=================================="
echo "🎉 Cache Rules Deployed!"
echo "=================================="
echo ""
echo "Your frontend will now be BLAZING FAST:"
echo ""
echo "⚡ Static assets cached for 1 year"
echo "⚡ Instant page loads from edge"
echo "⚡ Smooth goblin typing animations"
echo "⚡ Sub-50ms response times globally"
echo ""
echo "Test it:"
echo "  curl -I https://goblin.fuaad.ai/assets/main.js"
echo "  # Look for: cf-cache-status: HIT"
echo ""
echo "Monitor in Cloudflare Dashboard:"
echo "  Zone → Analytics → Caching"
echo ""
