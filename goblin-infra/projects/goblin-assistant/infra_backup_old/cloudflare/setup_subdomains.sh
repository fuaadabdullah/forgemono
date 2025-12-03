#!/bin/bash
# Cloudflare Subdomain Setup for Goblin Assistant
# Creates DNS records for: goblin.fuaad.ai, api.goblin.fuaad.ai, brain.goblin.fuaad.ai, ops.goblin.fuaad.ai

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🌐 Goblin Assistant Subdomain Setup"
echo "====================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "📄 Loading configuration from .env..."
    export $(grep -v '^#' .env | xargs)
    echo ""
fi

# Check for required tools
check_dependencies() {
    echo "🔍 Checking dependencies..."

    if ! command -v curl &> /dev/null; then
        echo -e "${RED}❌ Error: curl not found${NC}"
        echo "   Install with: brew install curl"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ Error: jq not found${NC}"
        echo "   Install with: brew install jq"
        exit 1
    fi

    echo -e "${GREEN}✅ All dependencies found${NC}"
    echo ""
}

# Get Cloudflare API token
get_api_token() {
    if [ -z "$CF_API_TOKEN" ]; then
        echo "🔑 Cloudflare API Token required"
        echo ""
        echo "Get your token at: https://dash.cloudflare.com/profile/api-tokens"
        echo "Required permissions: Zone.DNS (Edit)"
        echo ""
        read -p "Enter your Cloudflare API Token: " CF_API_TOKEN

        # Save to .env
        if [ ! -f ".env" ]; then
            echo "CF_API_TOKEN=$CF_API_TOKEN" >> .env
        else
            if grep -q "CF_API_TOKEN" .env; then
                sed -i.bak "s|CF_API_TOKEN=.*|CF_API_TOKEN=$CF_API_TOKEN|" .env
            else
                echo "CF_API_TOKEN=$CF_API_TOKEN" >> .env
            fi
        fi
        echo ""
    fi

    # Verify token works
    echo "🔐 Verifying API token..."
    TOKEN_TEST=$(curl -s -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json")

    if echo "$TOKEN_TEST" | jq -e '.success' > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API token is valid${NC}"
        echo ""
    else
        echo -e "${RED}❌ API token is invalid${NC}"
        echo "$TOKEN_TEST" | jq '.'
        exit 1
    fi
}

# List zones and get zone ID
get_zone_id() {
    if [ -z "$CF_ZONE_ID" ]; then
        echo "🌍 Fetching your Cloudflare zones..."

        ZONES=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones" \
            -H "Authorization: Bearer $CF_API_TOKEN" \
            -H "Content-Type: application/json")

        if ! echo "$ZONES" | jq -e '.success' > /dev/null 2>&1; then
            echo -e "${RED}❌ Failed to fetch zones${NC}"
            echo "$ZONES" | jq '.'
            exit 1
        fi

        echo ""
        echo "Available domains:"
        echo "$ZONES" | jq -r '.result[] | "\(.name) - \(.id)"' | nl
        echo ""

        read -p "Enter domain name (e.g., fuaad.ai): " ROOT_DOMAIN

        CF_ZONE_ID=$(echo "$ZONES" | jq -r ".result[] | select(.name==\"$ROOT_DOMAIN\") | .id")

        if [ -z "$CF_ZONE_ID" ]; then
            echo -e "${RED}❌ Domain not found${NC}"
            exit 1
        fi

        echo -e "${GREEN}✅ Zone ID: $CF_ZONE_ID${NC}"

        # Save to .env
        if grep -q "CF_ZONE_ID" .env 2>/dev/null; then
            sed -i.bak "s|CF_ZONE_ID=.*|CF_ZONE_ID=$CF_ZONE_ID|" .env
        else
            echo "CF_ZONE_ID=$CF_ZONE_ID" >> .env
        fi

        if grep -q "ROOT_DOMAIN" .env 2>/dev/null; then
            sed -i.bak "s|ROOT_DOMAIN=.*|ROOT_DOMAIN=$ROOT_DOMAIN|" .env
        else
            echo "ROOT_DOMAIN=$ROOT_DOMAIN" >> .env
        fi

        echo ""
    else
        echo -e "${GREEN}✅ Using Zone ID: $CF_ZONE_ID${NC}"
        echo ""
    fi
}

# Get configuration for subdomains
get_subdomain_config() {
    echo "🎯 Subdomain Configuration"
    echo ""

    # Frontend
    if [ -z "$FRONTEND_TARGET" ]; then
        echo "Frontend (goblin.$ROOT_DOMAIN):"
        read -p "  Target (CNAME or IP): " FRONTEND_TARGET
        echo "FRONTEND_TARGET=$FRONTEND_TARGET" >> .env
    fi

    # Backend API
    if [ -z "$BACKEND_TARGET" ]; then
        echo "Backend API (api.goblin.$ROOT_DOMAIN):"
        read -p "  Target (CNAME or IP): " BACKEND_TARGET
        echo "BACKEND_TARGET=$BACKEND_TARGET" >> .env
    fi

    # Brain (Worker)
    if [ -z "$BRAIN_TARGET" ]; then
        echo "Brain/Inference (brain.goblin.$ROOT_DOMAIN):"
        echo "  Default: goblin-assistant-edge.fuaadabdullah.workers.dev"
        read -p "  Target (or press Enter for default): " BRAIN_TARGET
        BRAIN_TARGET=${BRAIN_TARGET:-goblin-assistant-edge.fuaadabdullah.workers.dev}
        echo "BRAIN_TARGET=$BRAIN_TARGET" >> .env
    fi

    # Ops (Admin)
    if [ -z "$OPS_TARGET" ]; then
        echo "Ops/Admin (ops.goblin.$ROOT_DOMAIN):"
        read -p "  Target (CNAME, IP, or tunnel): " OPS_TARGET
        echo "OPS_TARGET=$OPS_TARGET" >> .env
    fi

    echo ""
}

# Create DNS record
create_dns_record() {
    local name=$1
    local type=$2
    local content=$3
    local proxied=${4:-true}

    echo "  Creating $type record: $name → $content"

    # Check if record exists
    EXISTING=$(curl -s -X GET \
        "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records?name=$name.$ROOT_DOMAIN" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json")

    RECORD_ID=$(echo "$EXISTING" | jq -r '.result[0].id // empty')

    if [ -n "$RECORD_ID" ]; then
        echo "  ⚠️  Record exists (ID: $RECORD_ID), updating..."

        # Update existing record
        RESPONSE=$(curl -s -X PUT \
            "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$RECORD_ID" \
            -H "Authorization: Bearer $CF_API_TOKEN" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"$type\",\"name\":\"$name\",\"content\":\"$content\",\"proxied\":$proxied,\"ttl\":1}")
    else
        # Create new record
        RESPONSE=$(curl -s -X POST \
            "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
            -H "Authorization: Bearer $CF_API_TOKEN" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"$type\",\"name\":\"$name\",\"content\":\"$content\",\"proxied\":$proxied,\"ttl\":1}")
    fi

    if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Success${NC}"
        return 0
    else
        echo -e "  ${RED}❌ Failed${NC}"
        echo "$RESPONSE" | jq '.errors'
        return 1
    fi
}

# Determine record type (A for IP, CNAME for domain)
get_record_type() {
    local target=$1

    # Check if it's an IP address
    if [[ $target =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "A"
    else
        echo "CNAME"
    fi
}

# Create all DNS records
create_all_records() {
    echo "📝 Creating DNS records..."
    echo ""

    # Frontend
    echo "1️⃣  Frontend: goblin.$ROOT_DOMAIN"
    FRONTEND_TYPE=$(get_record_type "$FRONTEND_TARGET")
    create_dns_record "goblin" "$FRONTEND_TYPE" "$FRONTEND_TARGET" true
    echo ""

    # Backend API
    echo "2️⃣  Backend API: api.goblin.$ROOT_DOMAIN"
    BACKEND_TYPE=$(get_record_type "$BACKEND_TARGET")
    create_dns_record "api.goblin" "$BACKEND_TYPE" "$BACKEND_TARGET" true
    echo ""

    # Brain (Inference Gateway)
    echo "3️⃣  Brain/Inference: brain.goblin.$ROOT_DOMAIN"
    BRAIN_TYPE=$(get_record_type "$BRAIN_TARGET")
    create_dns_record "brain.goblin" "$BRAIN_TYPE" "$BRAIN_TARGET" true
    echo ""

    # Ops (Admin)
    echo "4️⃣  Ops/Admin: ops.goblin.$ROOT_DOMAIN"
    OPS_TYPE=$(get_record_type "$OPS_TARGET")
    create_dns_record "ops.goblin" "$OPS_TYPE" "$OPS_TARGET" true
    echo ""
}

# Enable SSL/TLS
configure_ssl() {
    echo "🔒 Configuring SSL/TLS..."

    # Set SSL mode to Full (strict)
    RESPONSE=$(curl -s -X PATCH \
        "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/settings/ssl" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data '{"value":"full"}')

    if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        echo -e "${GREEN}✅ SSL mode set to Full (strict)${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not set SSL mode (may already be configured)${NC}"
    fi

    # Enable Always Use HTTPS
    RESPONSE=$(curl -s -X PATCH \
        "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/settings/always_use_https" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data '{"value":"on"}')

    if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Always Use HTTPS enabled${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not enable Always Use HTTPS${NC}"
    fi

    echo ""
}

# Test DNS propagation
test_dns() {
    echo "🧪 Testing DNS propagation..."
    echo ""

    SUBDOMAINS=("goblin" "api.goblin" "brain.goblin" "ops.goblin")

    for subdomain in "${SUBDOMAINS[@]}"; do
        FULL_DOMAIN="$subdomain.$ROOT_DOMAIN"
        echo "Testing $FULL_DOMAIN..."

        # Try to resolve
        if host "$FULL_DOMAIN" > /dev/null 2>&1; then
            RESOLVED=$(host "$FULL_DOMAIN" | head -1)
            echo -e "${GREEN}✅ $RESOLVED${NC}"
        else
            echo -e "${YELLOW}⏳ Not yet propagated (can take 5-30 minutes)${NC}"
        fi
    done

    echo ""
}

# Print summary
print_summary() {
    echo "====================================="
    echo "✅ Setup Complete!"
    echo "====================================="
    echo ""
    echo "🌐 Your Goblin Assistant subdomains:"
    echo ""
    echo "  Frontend:   https://goblin.$ROOT_DOMAIN"
    echo "  Backend:    https://api.goblin.$ROOT_DOMAIN"
    echo "  Brain:      https://brain.goblin.$ROOT_DOMAIN"
    echo "  Ops:        https://ops.goblin.$ROOT_DOMAIN"
    echo ""
    echo "📋 Next Steps:"
    echo ""
    echo "1. Wait for DNS propagation (5-30 minutes)"
    echo ""
    echo "2. Update your application configuration:"
    echo "   Frontend .env.production:"
    echo "     VITE_API_URL=https://api.goblin.$ROOT_DOMAIN"
    echo "     VITE_BRAIN_URL=https://brain.goblin.$ROOT_DOMAIN"
    echo ""
    echo "   Backend environment:"
    echo "     FRONTEND_URL=https://goblin.$ROOT_DOMAIN"
    echo "     CORS_ORIGINS=https://goblin.$ROOT_DOMAIN"
    echo ""
    echo "   Worker wrangler.toml:"
    echo "     API_URL = \"https://api.goblin.$ROOT_DOMAIN\""
    echo "     FRONTEND_URL = \"https://goblin.$ROOT_DOMAIN\""
    echo ""
    echo "3. Test your subdomains:"
    echo "   curl -I https://goblin.$ROOT_DOMAIN"
    echo "   curl https://api.goblin.$ROOT_DOMAIN/health | jq"
    echo "   curl https://brain.goblin.$ROOT_DOMAIN/health | jq"
    echo ""
    echo "4. Set up Zero Trust for ops.$ROOT_DOMAIN:"
    echo "   https://one.dash.cloudflare.com/access/apps"
    echo ""
    echo "📖 Full documentation: SUBDOMAIN_SETUP.md"
    echo ""
}

# Main execution
main() {
    check_dependencies
    get_api_token
    get_zone_id
    get_subdomain_config
    create_all_records
    configure_ssl
    test_dns
    print_summary
}

# Run main function
main
