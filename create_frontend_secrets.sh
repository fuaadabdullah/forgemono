#!/bin/bash

# Script to create missing Bitwarden secrets for goblin-frontend deployment
# Run this after unlocking Bitwarden CLI: bw unlock --passwordenv BW_PASSWORD

set -e

echo "Creating missing Bitwarden secrets for goblin-frontend deployment..."

#!/bin/bash

# Script to create missing Bitwarden secrets for goblin-frontend deployment
# Run this after unlocking Bitwarden CLI: bw unlock --passwordenv BW_PASSWORD

set -e

echo "Creating missing Bitwarden secrets for goblin-frontend deployment..."

#!/bin/bash

# Script to create missing Bitwarden secrets for goblin-frontend deployment
# Run this after unlocking Bitwarden CLI: bw unlock --passwordenv BW_PASSWORD

set -e

echo "Creating missing Bitwarden secrets for goblin-frontend deployment..."

# Check if Bitwarden is unlocked
if ! bw status | grep -q "unlocked"; then
    echo "❌ Bitwarden CLI is not unlocked."

    # Try to unlock automatically if BW_PASSWORD is set
    if [ -n "$BW_PASSWORD" ]; then
        echo "🔓 Attempting to unlock with BW_PASSWORD..."
        export BW_SESSION=$(bw unlock --passwordenv BW_PASSWORD --raw 2>/dev/null)
        if [ $? -eq 0 ] && [ -n "$BW_SESSION" ]; then
            echo "✅ Successfully unlocked Bitwarden"
        else
            echo "❌ Failed to unlock with BW_PASSWORD"
            echo "🔓 Attempting interactive unlock..."
            bw unlock
            exit 1
        fi
    else
        echo "🔓 Attempting interactive unlock..."
        bw unlock
        exit 1
    fi
fi

#!/bin/bash

# Script to create missing Bitwarden secrets for goblin-frontend deployment
# Run this after unlocking Bitwarden CLI: bw unlock --passwordenv BW_PASSWORD

set -e

echo "Creating missing Bitwarden secrets for goblin-frontend deployment..."

# Check if Bitwarden is unlocked
if ! bw status | grep -q "unlocked"; then
    echo "❌ Bitwarden CLI is not unlocked."

    # Try to unlock automatically if BW_PASSWORD is set
    if [ -n "$BW_PASSWORD" ]; then
        echo "🔓 Attempting to unlock with BW_PASSWORD..."
        export BW_SESSION=$(bw unlock --passwordenv BW_PASSWORD --raw 2>/dev/null)
        if [ $? -eq 0 ] && [ -n "$BW_SESSION" ]; then
            echo "✅ Successfully unlocked Bitwarden"
        else
            echo "❌ Failed to unlock with BW_PASSWORD"
            echo "🔓 Attempting interactive unlock..."
            bw unlock
            exit 1
        fi
    else
        echo "🔓 Attempting interactive unlock..."
        bw unlock
        exit 1
    fi
fi

echo "✅ Bitwarden CLI is unlocked"

# Function to create item (skip if exists)
create_item() {
    local name="$1"
    local username="$2"
    local password="$3"
    local notes="$4"

    # Check if item exists
    if bw get item "$name" &>/dev/null; then
        echo "✅ Item already exists: $name (skipping)"
        return 0
    fi

    echo "➕ Creating item: $name"
    # Use printf to avoid heredoc issues with special characters
    printf '{
  "type": 1,
  "name": "%s",
  "notes": "%s",
  "login": {
    "username": "%s",
    "password": "%s"
  }
}' "$name" "$notes" "$username" "$password" | bw create item
}

# Create secrets for goblin-frontend
echo "Creating goblin-prod-google-client-id..."
create_item "goblin-prod-google-client-id" "goblin-frontend-prod" "REPLACE_WITH_ACTUAL_GOOGLE_CLIENT_ID" "Google OAuth Client ID for goblin-frontend production"

echo "Creating goblin-prod-supabase-url..."
create_item "goblin-prod-supabase-url" "goblin-frontend-prod" "REPLACE_WITH_ACTUAL_SUPABASE_URL" "Supabase URL for goblin-frontend production"

echo "Creating goblin-prod-supabase-anon-key..."
create_item "goblin-prod-supabase-anon-key" "goblin-frontend-prod" "REPLACE_WITH_ACTUAL_SUPABASE_ANON_KEY" "Supabase Anonymous Key for goblin-frontend production"

echo "✅ All required secrets created!"
echo ""
echo "Next steps:"
echo "1. Edit each secret in Bitwarden and replace the placeholder values with actual credentials"
echo "2. Run the deployment: cd goblin-infra/projects/goblin-assistant/frontend && ./deploy-vercel.sh"
echo ""
echo "Required values to replace:"
echo "- goblin-prod-google-client-id: Your Google OAuth client ID"
echo "- goblin-prod-supabase-url: Your Supabase project URL (e.g., https://xxxxx.supabase.co)"
echo "- goblin-prod-supabase-anon-key: Your Supabase anon/public key"
