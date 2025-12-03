#!/bin/bash
set -e

# R2 Bucket Setup Script
# Creates all R2 buckets for Goblin Assistant cheap storage

source "$(dirname "$0")/.env"

ACCOUNT_ID="${CF_ACCOUNT_ID}"
API_TOKEN="${CF_API_TOKEN_WORKERS}"

if [[ -z "$ACCOUNT_ID" || -z "$API_TOKEN" ]]; then
  echo "❌ Missing CF_ACCOUNT_ID or CF_API_TOKEN_WORKERS in .env"
  exit 1
fi

echo "🪣 Creating R2 Buckets for Goblin Assistant"
echo "Account: $ACCOUNT_ID"
echo ""

# Bucket definitions (name:location)
BUCKETS=(
  "goblin-audio:auto"
  "goblin-logs:auto"
  "goblin-uploads:auto"
  "goblin-training:auto"
  "goblin-cache:auto"
  "goblin-audio-preview:auto"
  "goblin-logs-preview:auto"
  "goblin-uploads-preview:auto"
  "goblin-training-preview:auto"
  "goblin-cache-preview:auto"
)

create_bucket() {
  local bucket_name="$1"
  local location="${2:-auto}"

  echo "📦 Creating bucket: $bucket_name (location: $location)"

  response=$(curl -s -X POST \
    "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/r2/buckets" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    --data "{\"name\":\"$bucket_name\",\"locationHint\":\"$location\"}")

  if echo "$response" | grep -q '"success":true'; then
    echo "✅ Created: $bucket_name"
  elif echo "$response" | grep -q "already exists"; then
    echo "⚠️  Already exists: $bucket_name"
  else
    echo "❌ Failed to create $bucket_name"
    echo "Response: $response"
  fi
  echo ""
}

# Create all buckets
for bucket_def in "${BUCKETS[@]}"; do
  IFS=':' read -r name location <<< "$bucket_def"
  create_bucket "$name" "$location"
done

echo "🎉 R2 bucket creation complete!"
echo ""
echo "📊 Verify buckets:"
echo "wrangler r2 bucket list"
echo ""
echo "🔗 Configure CORS (if needed):"
echo "wrangler r2 bucket cors put goblin-audio --config cors_config.json"
echo ""
echo "🚀 Next steps:"
echo "1. Deploy worker: wrangler deploy"
echo "2. Test R2 access in worker code"
echo "3. Configure public access for audio bucket (Dashboard → R2 → goblin-audio → Settings → Public Access)"
