#!/bin/bash

# Comprehensive Cloudflare Infrastructure Test
# Tests all components: Worker, KV, D1, Turnstile, Zero Trust

echo "🧪 Testing Cloudflare Infrastructure..."
echo ""

WORKER_URL="https://goblin-assistant-edge.fuaadabdullah.workers.dev"
PASSED=0
FAILED=0

# Helper functions
pass() {
    echo "✅ PASS: $1"
    ((PASSED++))
}

fail() {
    echo "❌ FAIL: $1"
    ((FAILED++))
}

# Test 1: Health Check
echo "1️⃣ Testing Health Endpoint..."
HEALTH=$(curl -s "$WORKER_URL/health")
if echo "$HEALTH" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    VERSION=$(echo "$HEALTH" | jq -r '.version')
    pass "Health check (version $VERSION)"
else
    fail "Health check failed"
fi
echo ""

# Test 2: Feature Flags
echo "2️⃣ Testing Feature Flags..."
if echo "$HEALTH" | jq -e '.features.turnstile == true' > /dev/null 2>&1; then
    pass "Turnstile feature enabled"
else
    fail "Turnstile feature not enabled"
fi

if echo "$HEALTH" | jq -e '.features.rate_limiting == true' > /dev/null 2>&1; then
    pass "Rate limiting feature enabled"
else
    fail "Rate limiting feature not enabled"
fi
echo ""

# Test 3: Turnstile Protection
echo "3️⃣ Testing Turnstile Bot Protection..."
BOT_RESPONSE=$(curl -s -X POST "$WORKER_URL/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "test"}')

if echo "$BOT_RESPONSE" | jq -e '.error == "Bot verification failed"' > /dev/null 2>&1; then
    pass "Turnstile blocks requests without token"
else
    fail "Turnstile not blocking bot requests"
fi
echo ""

# Test 4: Response Headers
echo "4️⃣ Testing Response Headers..."
HEADERS=$(curl -s -I "$WORKER_URL/health")

if echo "$HEADERS" | grep -q "x-goblin-edge: active"; then
    pass "X-Goblin-Edge header present"
else
    fail "X-Goblin-Edge header missing"
fi

if echo "$HEADERS" | grep -q "x-response-time"; then
    pass "X-Response-Time header present"
else
    fail "X-Response-Time header missing"
fi
echo ""

# Test 5: D1 Database
echo "5️⃣ Testing D1 Database..."
D1_OUTPUT=$(wrangler d1 execute goblin-assistant-db --remote --command "SELECT COUNT(*) as count FROM feature_flags" 2>&1)

if echo "$D1_OUTPUT" | grep -q "count"; then
    pass "D1 database accessible"
else
    fail "D1 database not accessible"
fi
echo ""

# Test 6: KV Namespace
echo "6️⃣ Testing KV Namespace..."
KV_OUTPUT=$(wrangler kv key list --namespace-id=9e1c27d3eda84c759383cb2ac0b15e4c 2>&1)

if [ $? -eq 0 ]; then
    pass "KV namespace accessible"
else
    fail "KV namespace not accessible"
fi
echo ""

# Test 7: Turnstile Widgets
echo "7️⃣ Testing Turnstile Configuration..."
if grep -q "TURNSTILE_SITE_KEY_MANAGED" .env; then
    pass "Managed widget configured"
else
    fail "Managed widget not configured"
fi

if grep -q "TURNSTILE_SITE_KEY_INVISIBLE" .env; then
    pass "Invisible widget configured"
else
    fail "Invisible widget not configured"
fi
echo ""

# Test 8: Zero Trust Access Group
echo "8️⃣ Testing Zero Trust Configuration..."
ZT_RESPONSE=$(curl -s "https://api.cloudflare.com/client/v4/accounts/a9c52e892f7361bab3bfd084c6ffaccb/access/groups/1eac441b-55ad-4be9-9259-573675e2d993" \
    -H "Authorization: Bearer $(grep CF_API_TOKEN_ACCESS .env | cut -d'"' -f2)")

if echo "$ZT_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    pass "Zero Trust Access Group exists"
else
    fail "Zero Trust Access Group not found"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All tests passed! Infrastructure is fully operational."
    exit 0
else
    echo "⚠️  Some tests failed. Check output above for details."
    exit 1
fi
