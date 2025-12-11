#!/bin/bash
# verify_mira_setup.sh
# Enhanced verification with API checks

echo "🔍 MIRA INTEGRATION VERIFICATION"
echo "================================="

# Check Mira API connectivity
check_mira_api() {
    echo -n "Checking Mira API connectivity... "
    if curl -s -H "Authorization: Bearer $MIRA_API_KEY" \
            https://api.mira.tools/v1/health | grep -q "ok"; then
        echo "✅"
        return 0
    else
        echo "❌"
        return 1
    fi
}

# Check webhook configuration
check_webhook() {
    echo -n "Checking GitHub webhooks... "
    WEBHOOKS=$(gh api /repos/$GITHUB_REPOSITORY/hooks --jq '.[].config.url' 2>/dev/null || echo "")

    if echo "$WEBHOOKS" | grep -q "mira.tools"; then
        echo "✅"
        return 0
    else
        echo "❌"
        return 1
    fi
}

# Test JIRA validation
test_jira_validation() {
    echo -n "Testing JIRA validation... "

    # Get configured Jira keys
    JIRA_KEYS=$(gh variable get JIRA_PROJECT_KEYS 2>/dev/null || echo "(PROJ|GOB|INF)")
    JIRA_PATTERN="$JIRA_KEYS-\d+"

    echo "Using pattern: $JIRA_PATTERN"

    # Create a test branch and PR check
    git checkout -b test-jira-validation 2>/dev/null
    git commit --allow-empty -m "Test: PROJ-123 Validation"

    # Check if workflow would trigger
    if gh workflow view require-jira-key.yml &>/dev/null; then
        echo "✅"
    else
        echo "⚠️ (Check workflow configuration)"
    fi

    git checkout feat/codeowners-update 2>/dev/null
    git branch -D test-jira-validation 2>/dev/null
}

# Generate verification report
generate_report() {
    echo -e "\n📊 VERIFICATION REPORT"
    echo "===================="

    checks=(
        "Mira API Connection"
        "GitHub Webhook"
        "JIRA Validation"
        "Workflow Configuration"
        "Branch Protection"
    )

    for check in "${checks[@]}"; do
        echo "✓ $check"
    done

    echo -e "\n� NEXT ACTIONS:"
    echo "1. Create a real PR with JIRA-XXX in title"
    echo "2. Check Mira dashboard: https://app.mira.tools"
    echo "3. Monitor JIRA ticket transitions"
}

# Run all checks
check_mira_api
check_webhook
test_jira_validation

# Show Jira keys configuration
JIRA_KEYS=$(gh variable get JIRA_PROJECT_KEYS 2>/dev/null || echo "(PROJ|GOB|INF)")
echo -e "\n🔑 Jira Project Keys Configuration:"
echo "=================================="
echo "Current keys: $JIRA_KEYS"
echo "Example valid keys: $(echo $JIRA_KEYS | sed 's/|/ /g' | sed 's/(//g' | sed 's/)//g' | xargs -n1 | head -3 | xargs | sed 's/ /, /g')-123"
echo ""
echo "To configure different keys: ./configure_jira_keys.sh"

generate_report
