#!/bin/bash
# Privacy & Security Deployment Script for Goblin Assistant
# Run this before deploying privacy features to production

set -e

echo "🔒 Goblin Assistant Privacy Feature Deployment"
echo "=============================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track pass/fail
CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to check something
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} $1"
        ((CHECKS_FAILED++))
    fi
}

echo "1️⃣  Running RLS Audit..."
bash scripts/ops/supabase_rls_check.sh
check "RLS policies verified"
echo ""

echo "2️⃣  Checking for secrets in codebase..."
# Check for common secret patterns
if git grep -i "service_role" -- '*.py' '*.ts' '*.js' | grep -v ".example" | grep -v "# Store in Bitwarden" > /dev/null; then
    echo -e "${RED}✗${NC} Found potential secrets in code!"
    ((CHECKS_FAILED++))
else
    echo -e "${GREEN}✓${NC} No hardcoded secrets found"
    ((CHECKS_PASSED++))
fi
echo ""

echo "3️⃣  Verifying environment files..."
if [ -f "apps/goblin-assistant/api/.env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} .env file missing - copy from .env.privacy.example"
    ((CHECKS_FAILED++))
fi
echo ""

echo "4️⃣  Testing sanitization module..."
cd apps/goblin-assistant/api
python3 -c "
from services.sanitization import sanitize_input_for_model, is_sensitive_content

# Test PII detection
test_email = 'Contact me at test@example.com'
sanitized, pii = sanitize_input_for_model(test_email)
assert 'REDACTED' in sanitized, 'Email not sanitized'
assert 'email' in pii, 'Email not detected'

# Test sensitive content
assert is_sensitive_content('my password is 12345'), 'Password not detected'

print('Sanitization tests passed!')
"
check "Sanitization module working"
cd ../../..
echo ""

echo "5️⃣  Checking Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is running"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC}  Redis not running - rate limiting will fail"
    echo "   Start with: redis-server"
    ((CHECKS_FAILED++))
fi
echo ""

echo "6️⃣  Verifying Supabase migrations..."
if [ -d "apps/goblin-assistant/supabase/migrations" ]; then
    migration_count=$(ls -1 apps/goblin-assistant/supabase/migrations/*.sql 2>/dev/null | wc -l)
    if [ "$migration_count" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Found $migration_count migration(s)"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} No SQL migrations found"
        ((CHECKS_FAILED++))
    fi
else
    echo -e "${RED}✗${NC} Migrations directory not found"
    ((CHECKS_FAILED++))
fi
echo ""

echo "7️⃣  Checking Cloudflare Worker configuration..."
if [ -f "goblin-infra/projects/goblin-assistant/infra/cloudflare/wrangler.toml" ]; then
    echo -e "${GREEN}✓${NC} Cloudflare Worker config found"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC}  Cloudflare Worker config not found"
fi
echo ""

echo "8️⃣  Testing privacy endpoints..."
echo "   (Skipping - requires running server)"
echo -e "${YELLOW}⚠${NC}  Manual test required after deployment"
echo ""

# Summary
echo "=============================================="
echo "📊 Deployment Readiness Summary"
echo "=============================================="
echo -e "Passed: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Failed: ${RED}$CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Ready for deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Deploy Supabase migrations: supabase db push"
    echo "  2. Deploy Cloudflare Worker: cd goblin-infra/... && wrangler deploy"
    echo "  3. Deploy backend: fly deploy (or your deployment method)"
    echo "  4. Test privacy endpoints: /api/privacy/export, /api/privacy/delete"
    echo "  5. Monitor Datadog for telemetry"
    exit 0
else
    echo -e "${RED}❌ Fix issues before deploying${NC}"
    exit 1
fi
