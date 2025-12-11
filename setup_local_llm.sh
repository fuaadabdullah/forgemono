#!/bin/bash
set -e

echo "🧪 Setting up Local LLM Development Environment"

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "✅ Ollama already installed"
fi

# Start Ollama service (background)
echo "🚀 Starting Ollama service..."
ollama serve &
sleep 3

# Pull a recommended Raptor Mini model
echo "📥 Pulling test model (raptor-mini)..."
ollama pull raptor-mini

# Test Ollama API
echo "🧪 Testing Ollama API..."
curl -s http://localhost:11434/api/tags | head -20

# Create local proxy config
echo "⚙️  Setting up local proxy configuration..."
cat > local_proxy_config.env << 'ENV_EOF'
LOCAL_LLM_PROXY_URL=http://localhost:8002
# Optional API key for local proxy; leave empty to disable auth for development
LOCAL_LLM_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
ENV_EOF

echo "✅ Local LLM environment ready!"
echo ""
echo "📋 Next steps:"
echo "1. Start the local LLM proxy:"
echo "   cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/backend"
echo "   python3 local_llm_proxy.py"
echo ""
echo "2. In another terminal, start the backend:"
echo "   source venv/bin/activate"
echo "   python3 start_server.py"
echo ""
echo "3. Test the integration:"
echo "   curl http://localhost:8002/health"
echo "   curl http://localhost:8001/health"
echo ""
echo "4. Test chat completion:"
echo "   curl -X POST http://localhost:8002/v1/chat/completions \\"
echo "         -H 'Content-Type: application/json' \\"
echo "         -H 'Authorization: Bearer <LOCAL_LLM_API_KEY>' \\"
echo "         -d '{\"model\":\"raptor-mini\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}'"

