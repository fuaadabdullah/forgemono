#!/bin/bash
# Model Gateway Setup Script
# Deploys Worker with intelligent routing and initializes D1 schema

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Cloudflare Model Gateway Setup"
echo "=================================="
echo ""

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "❌ Error: wrangler CLI not found"
    echo "   Install with: npm install -g wrangler"
    exit 1
fi

echo "✅ wrangler CLI found"
echo ""

# Step 1: Backup existing worker
echo "📦 Step 1: Backing up existing worker..."
if [ -f "worker.js" ]; then
    cp worker.js worker.backup.js
    echo "   ✓ Backup created: worker.backup.js"
fi
echo ""

# Step 2: Deploy model gateway schema to D1
echo "📊 Step 2: Deploying D1 schema for model gateway..."
wrangler d1 execute goblin-assistant-db --remote --file=schema_model_gateway.sql
echo "   ✓ Schema deployed successfully"
echo ""

# Step 3: Update wrangler.toml with model gateway config
echo "⚙️  Step 3: Checking wrangler.toml configuration..."
if ! grep -q "OLLAMA_ENDPOINT" wrangler.toml; then
    echo ""
    echo "⚠️  Model gateway endpoints not configured in wrangler.toml"
    echo "   Add these variables to wrangler.toml [vars] section:"
    echo ""
    cat << 'EOF'
# Model Gateway Endpoints
OLLAMA_ENDPOINT = "http://localhost:11434"
LLAMACPP_ENDPOINT = "http://localhost:8080"
KAMATERA_ENDPOINT = "https://your-kamatera-server.com:8080"

# Cloud Fallbacks
OPENAI_ENDPOINT = "https://api.openai.com/v1"
ANTHROPIC_ENDPOINT = "https://api.anthropic.com/v1"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1"

# Routing Strategy
DEFAULT_ROUTING_STRATEGY = "cost-optimized" # cost-optimized, latency-optimized, local-first, balanced, quality-optimized
ENABLE_FAILOVER = "true"
MAX_FAILOVER_ATTEMPTS = "3"
HEALTH_CHECK_INTERVAL_SEC = "60"
EOF
    echo ""
    echo "   Update wrangler.toml manually and re-run this script"
    exit 1
else
    echo "   ✓ Model gateway config found in wrangler.toml"
fi
echo ""

# Step 4: Set API keys as secrets (optional, check if already set)
echo "🔐 Step 4: Checking API key secrets..."
echo "   If you want to enable cloud fallbacks, set these secrets:"
echo ""
echo "   echo 'YOUR_KEY' | wrangler secret put OPENAI_API_KEY"
echo "   echo 'YOUR_KEY' | wrangler secret put ANTHROPIC_API_KEY"
echo "   echo 'YOUR_KEY' | wrangler secret put GROQ_API_KEY"
echo "   echo 'YOUR_TOKEN' | wrangler secret put KAMATERA_AUTH_TOKEN"
echo ""
echo "   (Skip if using local-only mode)"
echo ""

# Step 5: Deploy worker
echo "🚀 Step 5: Deploying model gateway worker..."
read -p "   Deploy worker_with_model_gateway.js as active worker? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Copy model gateway worker to worker.js
    cp worker_with_model_gateway.js worker.js

    # Deploy
    wrangler deploy

    echo "   ✓ Worker deployed successfully"
    echo ""

    # Test deployment
    echo "🧪 Step 6: Testing deployment..."
    WORKER_URL=$(wrangler deployments list --name goblin-assistant-edge 2>/dev/null | grep "https://" | head -1 | awk '{print $1}')

    if [ -z "$WORKER_URL" ]; then
        WORKER_URL="https://goblin-assistant-edge.fuaadabdullah.workers.dev"
    fi

    echo "   Testing health endpoint: $WORKER_URL/health"

    HEALTH_RESPONSE=$(curl -s "$WORKER_URL/health")

    if echo "$HEALTH_RESPONSE" | grep -q "model_gateway"; then
        echo "   ✅ Model gateway is ACTIVE!"
        echo ""
        echo "   Response:"
        echo "$HEALTH_RESPONSE" | jq '.' || echo "$HEALTH_RESPONSE"
    else
        echo "   ⚠️  Deployment successful but model_gateway feature not detected"
        echo "   Check worker logs: wrangler tail goblin-assistant-edge"
    fi
else
    echo "   Deployment cancelled"
    echo "   To deploy manually:"
    echo "   cp worker_with_model_gateway.js worker.js && wrangler deploy"
fi

echo ""
echo "=================================="
echo "✅ Model Gateway Setup Complete!"
echo "=================================="
echo ""
echo "📚 Next Steps:"
echo ""
echo "1. Test routing strategies:"
echo "   curl -X POST $WORKER_URL/v1/chat/completions \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -H 'X-Routing-Strategy: cost-optimized' \\"
echo "     -d '{\"model\":\"llama3.2\",\"messages\":[{\"role\":\"user\",\"content\":\"Hi\"}]}'"
echo ""
echo "2. Monitor inference logs:"
echo "   wrangler d1 execute goblin-assistant-db --remote \\"
echo "     --command 'SELECT * FROM inference_logs ORDER BY timestamp DESC LIMIT 10'"
echo ""
echo "3. Check provider health:"
echo "   wrangler d1 execute goblin-assistant-db --remote \\"
echo "     --command 'SELECT * FROM provider_health'"
echo ""
echo "4. View cost analysis:"
echo "   wrangler d1 execute goblin-assistant-db --remote \\"
echo "     --command 'SELECT provider, COUNT(*) as requests, SUM(cost_usd) as total_cost FROM inference_logs GROUP BY provider'"
echo ""
echo "📖 Full documentation: MODEL_GATEWAY_SETUP.md"
echo ""
