#!/bin/bash
# Test chat API endpoint

curl -X POST http://localhost:8004/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello, test message"}],
    "model": "gpt-3.5-turbo",
    "provider": "openai"
  }'
