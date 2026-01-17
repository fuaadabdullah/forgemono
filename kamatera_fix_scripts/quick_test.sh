#!/bin/bash
# Kamatera Quick Test Script

echo "🧪 Testing Kamatera Network..."

INFERENCE_IP="192.175.23.150"
ROUTER_IP="45.61.51.220"
INFERENCE_PORT="8002"
ROUTER_PORT="8000"

echo "Testing connectivity..."
ping -c 1 $INFERENCE_IP >/dev/null 2>&1 && echo "✅ Inference server reachable" || echo "❌ Inference server unreachable"
ping -c 1 $ROUTER_IP >/dev/null 2>&1 && echo "✅ Router server reachable" || echo "❌ Router server unreachable"

echo "Testing HTTP endpoints..."
curl -s -m 5 "http://$INFERENCE_IP:$INFERENCE_PORT/api/tags" | grep -q "models" && echo "✅ Inference API working" || echo "❌ Inference API failed"
curl -s -m 5 "http://$ROUTER_IP:$ROUTER_PORT/health" | grep -q "ok" && echo "✅ Router health working" || echo "❌ Router health failed"

echo "Testing full chat flow..."
RESPONSE=$(curl -s -m 30 -X POST \
  -H "x-api-key: cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765" \
  -H "Content-Type: application/json" \
  -d '{"model":"phi3:latest","messages":[{"role":"user","content":"Hello"}]}' \
  "http://$ROUTER_IP:$ROUTER_PORT/v1/chat/completions")

echo "$RESPONSE" | grep -q "content" && echo "✅ Full chat flow working" || echo "❌ Full chat flow failed"
echo "$RESPONSE" | head -c 200