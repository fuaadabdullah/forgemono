#!/bin/bash

# Raptor Mini - Deploy to Existing Kamatera Server
# Deploys to your existing Kamatera server at 66.55.77.147

set -e

echo "🚀 Raptor Mini - Deploy to Existing Kamatera Server"
echo "=================================================="
echo "Target: 66.55.77.147 (existing Kamatera VPS)"
echo ""

# Check if we can connect to Kamatera
echo "🔍 Checking connection to Kamatera server..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes root@66.55.77.147 "echo 'SSH connection successful'" 2>/dev/null; then
    echo "❌ Cannot connect to Kamatera server via SSH"
    echo "Make sure:"
    echo "  - SSH key is configured for root@66.55.77.147"
    echo "  - Server is accessible"
    echo "  - SSH agent is running: eval \$(ssh-agent) && ssh-add"
    exit 1
fi

echo "✅ SSH connection to Kamatera confirmed"

# Generate a strong API key if not provided
if [ -z "$API_KEY" ]; then
    API_KEY=$(openssl rand -hex 32)
    echo "🔑 Generated API key: $API_KEY"
    echo "⚠️  Save this key securely! You'll need it for API access."
    echo ""
fi

# Set default model name
MODEL_NAME=${MODEL_NAME:-mistral:latest}

echo "📦 Copying Raptor Mini to Kamatera server..."
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
  /Users/fuaadabdullah/ForgeMonorepo/apps/raptor-mini/ root@66.55.77.147:/opt/raptor-mini/

echo ""
echo "🏗️  Building Raptor Mini container on Kamatera..."
ssh root@66.55.77.147 << EOF
cd /opt/raptor-mini

# Stop existing container if running
docker stop raptor-mini 2>/dev/null || true
docker rm raptor-mini 2>/dev/null || true

# Build new container
docker build -t raptor-mini:latest .

# Start service on port 8080 (different from existing LLM on 8000)
docker run -d --name raptor-mini \
  -p 127.0.0.1:8080:8080 \
  -e API_KEY="$API_KEY" \
  -e MODEL_NAME="$MODEL_NAME" \
  --restart unless-stopped \
  raptor-mini:latest

echo "⏳ Waiting for service to start..."
sleep 10

echo "🏥 Testing health check..."
if curl -f http://127.0.0.1:8080/health; then
    echo "✅ Service is healthy!"
else
    echo "❌ Health check failed. Check logs:"
    echo "docker logs raptor-mini"
    exit 1
fi
EOF

echo ""
echo "🎉 Deployment to Kamatera successful!"
echo ""
echo "📊 Service Details:"
echo "   Server: 66.55.77.147"
echo "   Internal URL: http://127.0.0.1:8080"
echo "   External URL: http://66.55.77.147:8080 (if port forwarded)"
echo "   API Key: $API_KEY"
echo "   Model: $MODEL_NAME"
echo ""
echo "🧪 Test commands (on Kamatera server):"
echo "   curl http://127.0.0.1:8080/health"
echo "   curl -X POST http://127.0.0.1:8080/v1/generate \\"
echo "     -H 'X-API-Key: $API_KEY' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"prompt\": \"Hello world\", \"max_tokens\": 50}'"
echo ""
echo "🔧 Management commands (on Kamatera server):"
echo "   docker logs raptor-mini          # View logs"
echo "   docker restart raptor-mini       # Restart service"
echo "   docker stop raptor-mini          # Stop service"
echo ""
echo "🔒 Security Notes:"
echo "   - Service bound to localhost only (127.0.0.1)"
echo "   - API key authentication required"
echo "   - Existing LLM service on port 8000 unaffected"
echo ""
echo "📈 Monitoring (on Kamatera server):"
echo "   curl http://127.0.0.1:8080/health  # Health check"
