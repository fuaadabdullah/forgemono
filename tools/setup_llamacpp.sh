#!/bin/bash
# llama.cpp Setup Script for Separate Deployment

echo "🦙 Setting up llama.cpp as separate deployment..."
echo "📍 Will run on localhost:8080 (separate from LMStudio on :1234)"
echo ""

# Create models directory
mkdir -p ~/llama_models
cd ~/llama_models

echo "📥 Downloading TinyLlama 1.1B model (small, fast)..."
curl -L -o tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
    "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

if [ $? -eq 0 ]; then
    echo "✅ Model downloaded successfully!"
    echo ""
    echo "🚀 Starting llama.cpp server on localhost:8080..."
    echo "📋 Server will be available at: http://localhost:8080"
    echo "🧪 Test with: curl http://localhost:8080/v1/models"
    echo ""
    echo "⚠️  Keep this terminal open. Server will run in foreground."
    echo "🔄 Press Ctrl+C to stop the server."
    echo ""

    # Start server
    /usr/local/bin/llama-server \
        --model ~/llama_models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
        --host 127.0.0.1 \
        --port 8080 \
        --ctx-size 2048 \
        --threads $(sysctl -n hw.ncpu) \
        --n-gpu-layers 0
else
    echo "❌ Model download failed. Please check your internet connection."
    exit 1
fi
