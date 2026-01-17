#!/bin/bash

# Complete Mira Linker Setup Automation
# This script guides through and verifies Mira console setup

set -e

echo "🚀 Mira Linker Complete Setup Automation"
echo "========================================"

# Check if all tokens are configured
echo "📋 Checking token configuration..."
echo ""

if ! gh secret list | grep -q "MIRA_GITHUB_TOKEN\|MIRA_JIRA_TOKEN"; then
    echo "❌ GitHub secrets not configured. Run ./setup_mira_tokens.sh first"
    exit 1
fi

echo "✅ GitHub secrets configured"

if ! circleci context list --org-id bbdc9f2a-17bb-40bb-a3c6-88b58963fdfc | grep -q "circleci-agents"; then
    echo "❌ CircleCI context not configured"
    exit 1
fi

echo "✅ CircleCI context configured"

echo ""
echo "🔗 Webhook Setup Instructions:"
echo "=============================="
echo ""
echo "1. 🌐 Go to Mira Console: https://app.mira.tools"
echo ""
echo "2. 📤 Upload Configuration:"
echo "   - Navigate to 'forgemono' project"
echo "   - Go to Settings → Configuration"
echo "   - Upload: mira-linker-config.yml"
echo ""
echo "3. 🔗 Configure GitHub Webhooks:"
echo "   - Settings → Integrations → GitHub"
echo "   - Click 'Add Webhook' or 'Configure Webhooks'"
echo "   - Repository: fuaadabdullah/forgemono"
echo "   - Events: Pull requests, Push, Branches"
echo "   - Copy the webhook URL from Mira"
echo ""
echo "4. ⚙️ Enable Features:"
echo "   - Auto-assign reviewers: ✅ CODEOWNERS fallback"
echo "   - Ticket transitions: ✅ PR open → In Review"
echo "   - Block merge: ✅ If ticket not in allowed state"
echo "   - Require ticket link: ✅ PROJ-\\d+ pattern"
echo ""

# Generate webhook creation command
echo "📝 After getting webhook URL from Mira, run:"
echo ""
echo "# Replace YOUR_WEBHOOK_URL with the URL from Mira console"
echo "gh api repos/fuaadabdullah/forgemono/hooks -X POST -H 'Accept: application/vnd.github.v3+json' \\"
echo "  -f name='web' \\"
echo "  -f active=true \\"
echo "  -f events='[\"pull_request\",\"push\",\"create\",\"delete\"]' \\"
echo "  -f config='{\"url\":\"YOUR_WEBHOOK_URL\",\"content_type\":\"json\",\"secret\":\"\"}'"
echo ""

echo "🔍 Verification Commands:"
echo "========================"
echo ""
echo "# Check webhook was created:"
echo "gh api repos/fuaadabdullah/forgemono/hooks | jq -r '.[].config.url'"
echo ""
echo "# Test PR with Jira key:"
echo "gh pr create --title 'PROJ-999: Test Mira integration' --body 'Testing complete workflow'"
echo ""
echo "# Check workflow passes:"
echo "gh run list --limit 3"
echo ""

echo "📊 Expected Behavior After Setup:"
echo "================================="
echo ""
echo "✅ PR with 'PROJ-123' in title:"
echo "   - require-jira-key workflow: PASSES ✓"
echo "   - Mira comments on PR with ticket link"
echo "   - Jira ticket transitions to 'In Review'"
echo "   - Auto-assigns reviewers from CODEOWNERS"
echo ""
echo "❌ PR without Jira key:"
echo "   - require-jira-key workflow: FAILS ✗"
echo "   - Cannot merge until Jira key added"
echo ""
echo "✅ PR merged:"
echo "   - Jira ticket transitions to 'Done'"
echo "   - Branch protection enforced"
echo ""

echo "🎯 Quick Test Commands:"
echo "======================"
echo ""
echo "# Create test PR (replace with real Jira ticket):"
echo "gh pr create --title 'PROJ-123: Complete Mira setup test' --body 'Testing full integration'"
echo ""
echo "# Monitor workflow:"
echo "gh run watch"
echo ""
echo "# Check PR comments for Mira activity:"
echo "gh pr view --comments"
echo ""

echo "📞 Support:"
echo "=========="
echo ""
echo "If setup issues occur:"
echo "- Check Mira console logs"
echo "- Verify webhook delivery: https://github.com/fuaadabdullah/forgemono/settings/hooks"
echo "- Test token permissions in respective services"
echo "- Review mira-linker-config.yml syntax"
echo ""

echo "🎉 Setup complete! Complete the web configuration above to activate Mira integration."
