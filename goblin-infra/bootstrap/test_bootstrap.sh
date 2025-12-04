#!/usr/bin/env bash
# Integration test for the bootstrap flow
# This simulates a VM calling the CI bootstrap server and writing secrets

set -e

echo "🧪 Testing bootstrap flow..."

# Start the bootstrap server in background
export CI_SECRETS_FILE="$(dirname "$0")/test_secrets.json"
python "$(dirname "$0")/ci_bootstrap_server.py" &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Test health check
echo "📡 Testing server health..."
curl -s http://localhost:8081/health | jq .

# Simulate VM bootstrap - fetch secrets
echo "🔐 Fetching secrets from CI server..."
curl -s "http://localhost:8081/secrets?instance=test-vm-123" > /tmp/test_env.json

# Write secrets to env file (like bootstrap_secrets.sh does)
echo "📝 Writing secrets to /tmp/test_env..."
jq -r 'to_entries|map("\(.key)=\(.value|tostring)")|.[]' /tmp/test_env.json > /tmp/test_env

# Verify env file was created and has content
echo "✅ Verifying env file..."
if [ ! -f /tmp/test_env ]; then
    echo "❌ Env file not created"
    exit 1
fi

if ! grep -q "DATABASE_URL=" /tmp/test_env; then
    echo "❌ DATABASE_URL not found in env file"
    exit 1
fi

echo "✅ Bootstrap flow test passed!"
echo "📄 Sample env content:"
head -3 /tmp/test_env

# Cleanup
kill $SERVER_PID
rm -f /tmp/test_env.json /tmp/test_env

echo "🧹 Cleanup complete"
