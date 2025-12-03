#!/bin/bash

# Setup Cloudflare Zero Trust Access
# This script helps configure Access Applications and Policies.

# Prerequisites:
# - Cloudflare API Token with Access:Edit permissions
# - Account ID

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "$CF_API_TOKEN_ACCESS" ] && [ -z "$CF_API_TOKEN" ]; then
  echo "Error: CF_API_TOKEN_ACCESS (or CF_API_TOKEN) and CF_ACCOUNT_ID environment variables must be set."
  echo "Usage: CF_API_TOKEN_ACCESS=... CF_ACCOUNT_ID=... ./setup_zerotrust.sh"
  echo "Or set them in .env file"
  exit 1
fi

# Use specific token if available, otherwise fallback
TOKEN="${CF_API_TOKEN_ACCESS:-$CF_API_TOKEN}"

ZONE_ID="$CF_ZONE_ID" # Optional if setting up per-zone access

echo "Configuring Cloudflare Zero Trust..."

# Function to create Access Group (Defines WHO can access)
create_access_group() {
  local name=$1
  local email=$2

  echo "Creating Access Group: $name (for $email)"

  local response=$(curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/access/groups" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     --data "{\"name\":\"$name\",\"include\":[{\"email\":{\"email\":\"$email\"}}]}")

  local success=$(echo "$response" | jq -r '.success')

  if [ "$success" = "true" ]; then
    echo "✅ Access Group created successfully"
    echo "$response" | jq .
  else
    local error_code=$(echo "$response" | jq -r '.errors[0].code')
    if [ "$error_code" = "12130" ]; then
      echo "ℹ️  Access Group '$name' already exists, fetching..."
      curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/access/groups" \
        -H "Authorization: Bearer $TOKEN" | jq --arg name "$name" '.result[] | select(.name == $name)'
    else
      echo "❌ Error creating Access Group:"
      echo "$response" | jq .
    fi
  fi
}

# Function to create Access Application (Requires Domain - Skipped if no domain)
create_access_app() {
  local name=$1
  local domain=$2

  if [ -z "$CF_ZONE_ID" ]; then
      echo "Skipping Access App '$name' (No Zone ID/Domain configured)"
      return
  fi

  echo "Creating Access Application: $name ($domain)"

  curl -X POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/access/apps" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     --data "{\"name\":\"$name\",\"domain\":\"$domain\",\"session_duration\":\"24h\"}"
}

# 1. Create Admin Group (The "Identity Rule")
# Replace with your actual email
ADMIN_EMAIL="Fuaadabdullah@gmail.com"
create_access_group "Goblin Admins" "$ADMIN_EMAIL"

# 2. Create Access Apps (Only if Domain exists)
# create_access_app "Goblin Admin" "admin.yourdomain.com"
# create_access_app "Ops Control" "ops.yourdomain.com"

echo "Zero Trust configuration updated. Access Groups created."
