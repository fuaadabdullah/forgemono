#!/bin/bash

# Setup Cloudflare Tunnel (Area 51 Mode)
# This script creates a Cloudflare Tunnel to securely expose your local services
# without opening any public ports.

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "$CF_API_TOKEN_ACCESS" ] && [ -z "$CF_API_TOKEN" ]; then
  echo "Error: CF_API_TOKEN_ACCESS (or CF_API_TOKEN) and CF_ACCOUNT_ID must be set."
  exit 1
fi

# Use specific token if available, otherwise fallback
TOKEN="${CF_API_TOKEN_ACCESS:-$CF_API_TOKEN}"

TUNNEL_NAME="goblin-tunnel"
CREDS_FILE="goblin-tunnel-creds.json"
CONFIG_FILE="tunnel-config.yml"

echo "Creating Cloudflare Tunnel: $TUNNEL_NAME..."

# 1. Generate a random 32-byte secret (base64 encoded)
# OpenSSL is standard on macOS
TUNNEL_SECRET=$(openssl rand -base64 32)

# 2. Create Tunnel via API
RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/tunnels" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data "{\"name\":\"$TUNNEL_NAME\",\"tunnel_secret\":\"$TUNNEL_SECRET\"}")

# Extract Tunnel ID (using python for reliable JSON parsing)
TUNNEL_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('id', ''))")

if [ -z "$TUNNEL_ID" ]; then
  echo "Error creating tunnel. Response:"
  echo $RESPONSE
  exit 1
fi

echo "Tunnel Created! ID: $TUNNEL_ID"

# 3. Create Credentials File
cat > $CREDS_FILE <<EOF
{
  "AccountTag": "$CF_ACCOUNT_ID",
  "TunnelSecret": "$TUNNEL_SECRET",
  "TunnelID": "$TUNNEL_ID"
}
EOF

echo "Credentials saved to $CREDS_FILE"

# 4. Create Tunnel Config
cat > $CONFIG_FILE <<EOF
tunnel: $TUNNEL_ID
credentials-file: $PWD/$CREDS_FILE

ingress:
  # Admin Dashboard (Zero Trust protected)
  - hostname: admin.yourdomain.com
    service: http://localhost:8000
    originRequest:
      access:
        required: true
        teamName: your-team-name
        audTag: [ "your-access-app-aud-tag" ]

  # Backend API
  - hostname: api.yourdomain.com
    service: http://localhost:8000

  # Catch-all
  - service: http_status:404
EOF

echo "Tunnel configuration saved to $CONFIG_FILE"
echo ""
echo "To run the tunnel (Area 51 Mode):"
echo "cloudflared tunnel --config $CONFIG_FILE run"
