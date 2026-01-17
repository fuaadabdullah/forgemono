#!/bin/bash

# Token Setup Script for Mira Linker Integration
# This script helps set up all required tokens for the integration
# Run this after creating the tokens in their respective services

set -e

echo "🔐 Token Setup for Mira Linker Integration"
echo "=========================================="
echo ""
echo "This script will guide you through storing tokens in GitHub Secrets and CircleCI contexts."
echo "You need to create the tokens first in their respective services."
echo ""

# Function to set GitHub secret
set_github_secret() {
    local secret_name=$1
    local description=$2

    echo "Setting up GitHub secret: $secret_name"
    echo "Description: $description"
    echo ""

    read -p "Enter the $secret_name value (or press Enter to skip): " secret_value

    if [ -n "$secret_value" ]; then
        echo "Setting GitHub secret..."
        echo "$secret_value" | gh secret set "$secret_name" --body -
        echo "✅ GitHub secret $secret_name set successfully"
    else
        echo "⚠️  Skipped setting $secret_name"
    fi
    echo ""
}

# Function to set CircleCI context secret
set_circleci_secret() {
    local secret_name=$1
    local description=$2

    echo "Setting up CircleCI context secret: $secret_name"
    echo "Description: $description"
    echo ""

    read -p "Enter the $secret_name value (or press Enter to skip): " secret_value

    if [ -n "$secret_value" ]; then
        echo "Setting CircleCI context secret..."
        # Note: This requires CircleCI CLI to be configured
        circleci context store-secret github fuaadabdullah/forgemono "$secret_name" <<< "$secret_value"
        echo "✅ CircleCI context secret $secret_name set successfully"
    else
        echo "⚠️  Skipped setting $secret_name"
    fi
    echo ""
}

echo "📋 Required Tokens:"
echo "==================="
echo ""
echo "1. mira_github_token"
echo "   - Type: GitHub App Installation Token or Personal Access Token"
echo "   - Scopes: repo, admin:repo_hook, pull_requests:write, repo:status"
echo "   - Where: GitHub Settings > Developer settings > GitHub Apps (or Personal Access Tokens)"
echo ""

echo "2. mira_jira_token"
echo "   - Type: Jira API Token"
echo "   - Scopes: issue:read, issue:write, issue:transition"
echo "   - Where: Jira Account Settings > Security > API tokens"
echo ""

echo "3. circleci_api_token"
echo "   - Type: CircleCI Personal API Token"
echo "   - Scopes: Read/Write access to pipelines"
echo "   - Where: CircleCI Account Settings > Personal API Tokens"
echo ""

echo "4. cloudflare_api_token_ci"
echo "   - Type: Cloudflare API Token"
echo "   - Scopes: Workers:Edit, R2:Write"
echo "   - Where: Cloudflare Dashboard > My Profile > API Tokens"
echo ""

echo "5. kamatera_deploy_key or kamatera_token"
echo "   - Type: SSH Private Key or API Token"
echo "   - Scopes: Server access and deployment permissions"
echo "   - Where: Kamatera Console > API/SSH Keys"
echo ""

echo "🚀 Setting up GitHub Secrets:"
echo "=============================="

set_github_secret "MIRA_GITHUB_TOKEN" "GitHub token for Mira Linker integration"
set_github_secret "MIRA_JIRA_TOKEN" "Jira API token for Mira Linker"
set_github_secret "CLOUDFLARE_API_TOKEN_CI" "Cloudflare API token for CI deployments"
set_github_secret "KAMATERA_DEPLOY_KEY" "SSH private key for Kamatera deployments"
set_github_secret "KAMATERA_TOKEN" "API token for Kamatera (alternative to SSH key)"

echo "🚀 Setting up CircleCI Context Secrets:"
echo "========================================"

set_circleci_secret "CIRCLECI_API_TOKEN" "CircleCI API token for pipeline management"

echo "✅ Token setup complete!"
echo ""
echo "Next steps:"
echo "1. Verify tokens are set in GitHub: https://github.com/fuaadabdullah/forgemono/settings/secrets/actions"
echo "2. Verify CircleCI context: Check your CircleCI project settings"
echo "3. Test the integration by creating a PR with a Jira key"
echo ""
echo "🔒 Remember to rotate these tokens regularly and never commit them to the repository!"
