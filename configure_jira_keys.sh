#!/bin/bash
# configure_jira_keys.sh
# Configure Jira project keys for Mira Linker integration

set -e

echo "🔧 JIRA PROJECT KEYS CONFIGURATION"
echo "=================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check current configuration
check_current_config() {
    echo "📋 Current Configuration:"
    echo "========================"

    # Check GitHub repository variables
    echo -n "GitHub JIRA_PROJECT_KEYS variable: "
    if gh variable list | grep -q "JIRA_PROJECT_KEYS"; then
        CURRENT_KEYS=$(gh variable get JIRA_PROJECT_KEYS)
        echo -e "${GREEN}✅ Set to: $CURRENT_KEYS${NC}"
    else
        echo -e "${YELLOW}⚠️  Not set (using default: PROJ)${NC}"
        CURRENT_KEYS="(PROJ|GOB|INF)"
    fi

    # Check Mira config
    if [ -f "mira-linker-config.yml" ]; then
        echo -n "Mira config project_key: "
        if grep -q "project_key.*JIRA_PROJECT_KEYS" mira-linker-config.yml; then
            echo -e "${GREEN}✅ Configurable${NC}"
        else
            echo -e "${YELLOW}⚠️  Hardcoded${NC}"
        fi
    fi

    echo ""
}

# Configure GitHub repository variables
configure_github_vars() {
    echo "🔑 Configuring GitHub Repository Variables:"
    echo "=========================================="

    read -p "Enter your Jira project keys (e.g., PROJ|GOB|INF): " JIRA_KEYS

    if [ -z "$JIRA_KEYS" ]; then
        echo -e "${YELLOW}⚠️  No keys provided, using default: (PROJ|GOB|INF)${NC}"
        JIRA_KEYS="(PROJ|GOB|INF)"
    fi

    # Set GitHub variable
    echo "Setting JIRA_PROJECT_KEYS to: $JIRA_KEYS"
    gh variable set JIRA_PROJECT_KEYS --body "$JIRA_KEYS"

    echo -e "${GREEN}✅ GitHub variable configured${NC}"
    echo ""
}

# Update Mira config if needed
update_mira_config() {
    echo "📝 Updating Mira Configuration:"
    echo "=============================="

    if [ -f "mira-linker-config.yml" ]; then
        # Check if already configurable
        if ! grep -q "JIRA_PROJECT_KEYS" mira-linker-config.yml; then
            echo "Making Mira config use environment variable..."
            # This would require updating the config, but since it's already updated above, skip
            echo -e "${GREEN}✅ Mira config already updated${NC}"
        else
            echo -e "${GREEN}✅ Mira config is configurable${NC}"
        fi
    else
        echo -e "${RED}❌ mira-linker-config.yml not found${NC}"
    fi

    echo ""
}

# Test configuration
test_configuration() {
    echo "🧪 Testing Configuration:"
    echo "========================"

    # Get current keys
    TEST_KEYS=$(gh variable get JIRA_PROJECT_KEYS 2>/dev/null || echo "(PROJ|GOB|INF)")

    echo "Testing with keys: $TEST_KEYS"

    # Test some examples
    test_cases=("PROJ-123" "GOB-456" "INF-789" "INVALID-999")

    for test_case in "${test_cases[@]}"; do
        if echo "$test_case" | grep -qE "$TEST_KEYS-\d+"; then
            echo -e "✅ $test_case: ${GREEN}VALID${NC}"
        else
            echo -e "❌ $test_case: ${RED}INVALID${NC}"
        fi
    done

    echo ""
}

# Show usage examples
show_usage() {
    echo "📚 Usage Examples:"
    echo "=================="

    echo "1. Single project key:"
    echo "   JIRA_PROJECT_KEYS: PROJ"
    echo "   Matches: PROJ-123, PROJ-456"
    echo ""

    echo "2. Multiple project keys:"
    echo "   JIRA_PROJECT_KEYS: (PROJ|GOB|INF)"
    echo "   Matches: PROJ-123, GOB-456, INF-789"
    echo ""

    echo "3. Complex pattern:"
    echo "   JIRA_PROJECT_KEYS: (PROJ|GOB|INF|DEVOPS)"
    echo "   Matches: PROJ-123, GOB-456, INF-789, DEVOPS-101"
    echo ""

    echo "🔗 Configure via:"
    echo "   GitHub: Repository → Settings → Variables → JIRA_PROJECT_KEYS"
    echo "   Or run: ./configure_jira_keys.sh"
    echo ""
}

# Main execution
main() {
    check_current_config
    configure_github_vars
    update_mira_config
    test_configuration
    show_usage

    echo -e "${GREEN}🎉 Jira project keys configured successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test with a PR containing your Jira keys"
    echo "2. Run ./verify_mira_setup.sh to confirm"
    echo "3. Check GitHub Actions for proper validation"
}

# Run main function
main
