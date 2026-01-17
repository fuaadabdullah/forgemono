#!/bin/bash
# Simple test script for Goblin Assistant Chat API

echo "🧪 Testing Goblin Assistant Chat API"
echo "===================================="

# API endpoint and key
API_URL="http://45.61.51.220:8000/v1/chat/completions"
API_KEY="cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765"

# Test function
test_chat() {
    local model=$1
    local message=$2
    local description=$3

    echo ""
    echo "🔍 Testing $description ($model model):"
    echo "Message: '$message'"

    response=$(curl -s -X POST "$API_URL" \
        -H 'Content-Type: application/json' \
        -H "X-API-Key: $API_KEY" \
        -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"$message\"}],\"temperature\":0.7,\"max_tokens\":100}")

    if [[ $? -eq 0 ]] && echo "$response" | jq -e '.choices[0].message.content' >/dev/null 2>&1; then
        content=$(echo "$response" | jq -r '.choices[0].message.content')
        echo "✅ SUCCESS: $content"
    else
        echo "❌ FAILED: $response"
    fi
}

# Run tests
test_chat "goblin-simple" "Hello! How are you?" "Simple Greeting"
test_chat "goblin-simple" "What is 2+2?" "Simple Math"
test_chat "goblin-medium" "Explain what AI is in simple terms" "Medium Explanation"
test_chat "goblin-medium" "Tell me about machine learning" "Medium Topic"

echo ""
echo "🎉 Testing complete!"
echo "If all tests show SUCCESS, the Goblin Assistant is working perfectly!"