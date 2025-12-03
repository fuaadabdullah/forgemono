#!/bin/bash

# Cloudflare Turnstile Setup for Goblin Assistant
# Captcha without being annoying - stops bots from spamming your API

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
SITE_NAME="Goblin Assistant"
DOMAIN="${FRONTEND_URL:-app.yourdomain.com}"
TOKEN="${CF_API_TOKEN_TURNSTILE:-${CF_API_TOKEN_WORKERS}}"

if [ -z "$TOKEN" ]; then
    echo "❌ Error: No API token found"
    echo ""
    echo "To create Turnstile widgets, you need an API token with:"
    echo "  - Account > Account Settings > Read"
    echo "  - Account > Turnstile > Edit"
    echo ""
    echo "Create a token at: https://dash.cloudflare.com/profile/api-tokens"
    echo "Then add to .env: CF_API_TOKEN_TURNSTILE=\"your-token\""
    echo ""
    exit 1
fi

echo "🛡️  Setting up Cloudflare Turnstile..."
echo ""

# Function to create Turnstile widget
create_turnstile_widget() {
    local name="$1"
    local domain="$2"
    local mode="$3"  # managed, non-interactive, or invisible

    echo "Creating Turnstile Widget: $name ($mode mode)"

    local response=$(curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/challenges/widgets" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        --data "{
            \"name\": \"$name\",
            \"domains\": [\"$domain\", \"localhost\"],
            \"mode\": \"$mode\",
            \"offlabel\": false,
            \"clearance_level\": \"interactive\"
        }")

    local success=$(echo "$response" | jq -r '.success')

    if [ "$success" = "true" ]; then
        local sitekey=$(echo "$response" | jq -r '.result.sitekey')
        local secret=$(echo "$response" | jq -r '.result.secret')
        local mode_upper=$(echo "$mode" | tr '[:lower:]' '[:upper:]')

        echo "✅ Widget created successfully"
        echo ""
        echo "🔑 Site Key (use in frontend): $sitekey"
        echo "🔐 Secret Key (use in backend): $secret"
        echo ""
        echo "Add these to your .env:"
        echo "TURNSTILE_SITE_KEY_${mode_upper}=\"$sitekey\""
        echo "TURNSTILE_SECRET_KEY_${mode_upper}=\"$secret\""
        echo ""

        # Append to .env if not already there
        if ! grep -q "TURNSTILE_SITE_KEY_${mode_upper}" .env 2>/dev/null; then
            echo "" >> .env
            echo "# Turnstile ($mode mode)" >> .env
            echo "TURNSTILE_SITE_KEY_${mode_upper}=\"$sitekey\"" >> .env
            echo "TURNSTILE_SECRET_KEY_${mode_upper}=\"$secret\"" >> .env
        fi
    else
        echo "❌ Error creating widget:"
        echo "$response" | jq .
    fi
}

# Create widgets for different use cases
echo "Creating Turnstile widgets..."
echo ""

# 1. Managed mode - for login/signup forms (visible challenge)
create_turnstile_widget "$SITE_NAME - Login" "$DOMAIN" "managed"

# 2. Invisible mode - for API calls (no UI, just verification)
create_turnstile_widget "$SITE_NAME - API" "$DOMAIN" "invisible"

echo ""
echo "✅ Turnstile setup complete!"
echo ""
echo "Next steps:"
echo "1. Add site keys to your frontend environment"
echo "2. Add secret keys to your backend environment"
echo "3. Integrate Turnstile in your forms (see TURNSTILE_INTEGRATION.md)"
echo "4. Update Worker to verify tokens (see worker_turnstile.js)"
