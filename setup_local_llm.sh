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

# Pull a small test model
echo "📥 Pulling test model (llama2:7b)..."
ollama pull llama2:7b

# Test Ollama API
echo "🧪 Testing Ollama API..."
curl -s http://localhost:11434/api/tags | head -20

# Create local proxy config
echo "⚙️  Setting up local proxy configuration..."
cat > local_proxy_config.env << 'ENV_EOF'
LOCAL_LLM_PROXY_URL=http://localhost:8002
LOCAL_LLM_API_KEY=dev-test-key-12345
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
echo "   curl -X POST http://localhost:8002/v1/chat/completions \\
         -H 'Content-Type: application/json' \\
         -H 'Authorization: Bearer dev-test-key-12345' \\
         -d '{\"model\":\"llama2:7b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}'"

