#!/bin/bash
# Integration test for privacy features in Goblin Assistant
# Run this to verify all privacy features are working

set -e

echo "════════════════════════════════════════════════════════════════"
echo "  GOBLIN ASSISTANT - PRIVACY FEATURES INTEGRATION TEST"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd "$(dirname "$0")/../apps/goblin-assistant/api" || exit 1

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_module() {
    local name=$1
    local test_code=$2
    
    echo -n "Testing $name... "
    if python3 -c "$test_code" 2>/dev/null; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "1️⃣  Testing Core Privacy Modules"
echo "────────────────────────────────────────────────────────────────"

test_module "Sanitization" "
from services.sanitization import sanitize_input_for_model
text = 'test@example.com'
sanitized, pii = sanitize_input_for_model(text)
assert 'REDACTED' in sanitized and 'email' in pii
"

test_module "Telemetry" "
from services.telemetry import log_inference_metrics
log_inference_metrics('test', 'gpt-4', 100, 50, 0.002, 200)
"

test_module "Rate Limiter" "
from middleware.rate_limiter import RateLimiter
limiter = RateLimiter()
"

test_module "Safe Vector Store" "
from services.safe_vector_store import SafeVectorStore
store = SafeVectorStore()
"

echo ""
echo "2️⃣  Testing Privacy Router Integration"
echo "────────────────────────────────────────────────────────────────"

if [ -f "privacy_router.py" ]; then
    echo -e "${GREEN}✅${NC} privacy_router.py exists"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌${NC} privacy_router.py not found"
    ((TESTS_FAILED++))
fi

# Check if privacy router is imported in main.py
if grep -q "from .privacy_router import router as privacy_router" main.py; then
    echo -e "${GREEN}✅${NC} Privacy router imported in main.py"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌${NC} Privacy router not imported in main.py"
    ((TESTS_FAILED++))
fi

# Check if privacy router is included
if grep -q "app.include_router(privacy_router)" main.py; then
    echo -e "${GREEN}✅${NC} Privacy router included in app"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌${NC} Privacy router not included in app"
    ((TESTS_FAILED++))
fi

echo ""
echo "3️⃣  Testing Configuration Files"
echo "────────────────────────────────────────────────────────────────"

if [ -f ".env.privacy.example" ]; then
    echo -e "${GREEN}✅${NC} .env.privacy.example exists"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC}  .env.privacy.example not found"
fi

if [ -f "requirements-privacy.txt" ]; then
    echo -e "${GREEN}✅${NC} requirements-privacy.txt exists"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌${NC} requirements-privacy.txt not found"
    ((TESTS_FAILED++))
fi

echo ""
echo "4️⃣  Testing Database Migrations"
echo "────────────────────────────────────────────────────────────────"

if [ -f "../supabase/migrations/20260110_privacy_rls.sql" ]; then
    echo -e "${GREEN}✅${NC} RLS migration file exists"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC}  RLS migration not found (create if needed)"
fi

echo ""
echo "5️⃣  Testing Documentation"
echo "────────────────────────────────────────────────────────────────"

if [ -f "docs/PRIVACY_IMPLEMENTATION.md" ]; then
    echo -e "${GREEN}✅${NC} PRIVACY_IMPLEMENTATION.md exists"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC}  PRIVACY_IMPLEMENTATION.md not found"
fi

if [ -f "../PRIVACY_QUICK_REFERENCE.md" ]; then
    echo -e "${GREEN}✅${NC} PRIVACY_QUICK_REFERENCE.md exists"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC}  PRIVACY_QUICK_REFERENCE.md not found"
fi

echo ""
echo "6️⃣  Testing Redis Connection"
echo "────────────────────────────────────────────────────────────────"

if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Redis is running"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC}  Redis not running (required for rate limiting)"
    echo "   Start with: redis-server"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  TEST RESULTS"
echo "════════════════════════════════════════════════════════════════"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Privacy features are integrated and ready to deploy!"
    echo ""
    echo "Next steps:"
    echo "  1. Review main.py and uncomment rate limiting if desired"
    echo "  2. Set environment variables in .env"
    echo "  3. Deploy Supabase migrations"
    echo "  4. Test endpoints in staging"
    echo "  5. Monitor Datadog metrics"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please fix the issues above before deploying."
    exit 1
fi
