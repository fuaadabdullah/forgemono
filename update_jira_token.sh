#!/bin/bash

# Automated Jira Token Replacement Script
# This script updates the Jira token in Bitwarden and re-runs setup

set -e

echo "🔐 Jira Token Replacement Automation"
echo "===================================="

# Check if Bitwarden is unlocked
if ! bw status | grep -q '"status":"unlocked"'; then
    echo "❌ Bitwarden CLI is locked. Please unlock it first:"
    echo "bw unlock"
    exit 1
fi

echo "✅ Bitwarden CLI is unlocked"
echo ""

# Check if Jira token was provided as argument
if [ $# -eq 0 ]; then
    echo "❌ No Jira token provided!"
    echo ""
    echo "Usage: $0 <jira-api-token>"
    echo ""
    echo "To get your Jira API token:"
    echo "1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens"
    echo "2. Create a new API token for Mira integration"
    echo "3. Copy the token and run:"
    echo "   $0 <your-jira-token-here>"
    exit 1
fi

JIRA_TOKEN="$1"

echo "🔄 Updating Jira token in Bitwarden..."
echo ""

# Update the existing Jira token item
echo "Updating 'Mira Jira Token' in Bitwarden..."
bw edit item "Mira Jira Token" --session $BW_SESSION --password "$JIRA_TOKEN"

echo "✅ Jira token updated in Bitwarden"
echo ""

echo "🚀 Re-running token setup..."
echo ""

# Re-run the main setup script
./setup_mira_tokens.sh

echo ""
echo "🎉 Jira integration is now fully configured!"
echo ""
echo "🧪 Test the integration:"
echo "1. Create a PR with 'PROJ-123' in the title"
echo "2. Check that the require-jira-key workflow passes"
echo "3. Verify Mira comments appear on the PR with Jira ticket linking"
