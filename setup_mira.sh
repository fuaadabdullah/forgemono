#!/bin/bash

# Mira Linker Setup Script for forgemono
# This script provides commands and steps to set up Mira Linker integration
# Run this after creating tokens and configuring Mira workspace

set -e

echo "Mira Linker Setup for fuaadabdullah/forgemono"
echo "=============================================="
echo ""
echo "Manual Steps (do these in Mira console first):"
echo "1. Create a new workspace/integration for GitHub"
echo "2. Connect mira_github_token (GitHub App/PAT) to fuaadabdullah/forgemono"
echo "3. Add Jira integration using mira_jira_token"
echo "4. Map Jira project pattern PROJ -> repo forgemono"
echo "5. Upload mira-linker-config.yml or configure manually:"
echo "   - Auto-assign fallback: @fuaadabdullah"
echo "   - Enable auto transitions and block-merge rules"
echo "   - Enable webhooks from GitHub to Mira"
echo "   - Set Mira to write back Jira transitions and add PR comments"
echo ""
echo "Then run this script for webhook setup."
echo ""

# Step 1: Create GitHub webhook for Mira (if Mira doesn't auto-create)
echo "Step 1: Creating GitHub webhook for Mira"
echo "Note: Replace <mira-endpoint> with your actual Mira webhook URL"
echo ""

# GitHub CLI command to create webhook
# Usage: ./setup_mira.sh <mira-endpoint>
# Example: ./setup_mira.sh https://my-mira-instance.com

if [ $# -eq 0 ]; then
    echo "Usage: $0 <mira-endpoint>"
    echo "Example: $0 https://my-mira-instance.com"
    exit 1
fi

MIRA_ENDPOINT=$1
WEBHOOK_URL="$MIRA_ENDPOINT/webhook"
WEBHOOK_SECRET=""  # Set this if Mira provides a secret

echo "Creating webhook with URL: $WEBHOOK_URL"

gh api repos/fuaadabdullah/forgemono/hooks \
  -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -f name=web \
  -f active=true \
  -f events='["push","pull_request","pull_request_review","status"]' \
  -f config="{\"url\":\"$WEBHOOK_URL\",\"content_type\":\"json\",\"secret\":\"$WEBHOOK_SECRET\"}"

echo ""
echo "Webhook created. Configure the secret in Mira and update the URL."
echo ""

# Step 2: Verify branch protection (run after setting up CI checks)
echo "Step 2: Verifying branch protection rules"
gh api repos/fuaadabdullah/forgemono/branches/main/protection

echo ""
echo "Branch protection verified."
echo ""

# Step 3: Test integration (optional)
echo "Step 3: Testing integration"
echo "Create a test PR with PROJ-123 in title/branch to verify Jira linking."
echo "Check that Mira comments on PRs and transitions Jira tickets."
echo ""

echo "Setup complete! Monitor Mira dashboard for integration status."
echo ""
echo "Final Steps in Mira Console:"
echo "1. Upload the mira-linker-config.yml file to your Mira workspace"
echo "2. Enable 'write back Jira transitions' in Mira settings"
echo "3. Enable 'add PR comments (backlinks)' in Mira settings"
echo "4. Test with a sample PR containing 'PROJ-123' to verify Jira linking and transitions"
echo ""
echo "The config file is located at: $(pwd)/mira-linker-config.yml"
