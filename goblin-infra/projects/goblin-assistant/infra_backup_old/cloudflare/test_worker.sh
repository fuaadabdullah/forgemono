#!/bin/bash

WORKER_URL="https://goblin-assistant-edge.fuaadabdullah.workers.dev"

echo "🧪 Testing Cloudflare Worker..."
echo ""

# Test 1: Health Check
echo "1️⃣ Health Check:"
curl -s "$WORKER_URL/health" | jq .
echo ""

# Test 2: Headers Check
echo "2️⃣ Response Headers:"
curl -s -I "$WORKER_URL/health" | grep -E "(x-goblin|x-response-time|x-cache)"
echo ""

# Test 3: Rate Limiting (make 10 requests)
echo "3️⃣ Rate Limiting Test (10 requests):"
for i in {1..10}; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "$WORKER_URL/health")
  echo "Request $i: HTTP $status"
done
echo ""

# Test 4: Check KV Storage
echo "4️⃣ KV Storage (rate limit keys):"
wrangler kv key list --namespace-id=9e1c27d3eda84c759383cb2ac0b15e4c | jq -r '.[] | select(.name | startswith("ratelimit")) | .name'
echo ""

# Test 5: Feature Flags
echo "5️⃣ Feature Flags (D1):"
wrangler d1 execute goblin-assistant-db --remote --command "SELECT flag_name, enabled FROM feature_flags WHERE enabled=1" 2>/dev/null | tail -n +8
echo ""

echo "✅ Tests complete!"
