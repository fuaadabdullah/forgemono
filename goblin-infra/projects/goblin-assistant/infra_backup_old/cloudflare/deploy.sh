#!/bin/bash
# Deploy Worker with API Token from .env

set -e

cd "$(dirname "$0")"

# Load API token from .env
source .env

if [[ -z "$CF_API_TOKEN_WORKERS" ]]; then
  echo "❌ Missing CF_API_TOKEN_WORKERS in .env"
  exit 1
fi

echo "🚀 Deploying Goblin Assistant Worker..."
echo "Account: $CF_ACCOUNT_ID"
echo ""

# Deploy with API token
CLOUDFLARE_API_TOKEN="$CF_API_TOKEN_WORKERS" wrangler deploy

echo ""
echo "✅ Deployment complete!"
echo "🔗 Worker URL: https://goblin-assistant-edge.fuaadabdullah.workers.dev"
