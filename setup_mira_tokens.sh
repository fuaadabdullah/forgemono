#!/bin/bash

# Retrieve Mira Tokens from Bitwarden and Setup Integration
# This script retrieves tokens from Bitwarden and sets them up for Mira Linker

set -e

echo "🔐 Retrieving Mira Tokens from Bitwarden"
echo "========================================"

# Check if Bitwarden is unlocked
if ! bw status | grep -q '"status":"unlocked"'; then
    echo "Bitwarden CLI is locked. Please unlock it first:"
    echo "bw unlock"
    echo ""
    echo "Or login if not logged in:"
    echo "bw login"
    exit 1
fi

echo "✅ Bitwarden CLI is unlocked"
echo ""

# Function to get token from Bitwarden
get_bw_token() {
    local item_name=$1
    local field_name=$2
    local description=$3

    echo "Retrieving $description from Bitwarden item: $item_name"

    # Try to get the password field first (most common for tokens)
    token=$(bw get password "$item_name" --session $BW_SESSION 2>/dev/null)

    if [ -z "$token" ]; then
        # Try to get a custom field
        token=$(bw get item "$item_name" --session $BW_SESSION | jq -r ".fields[] | select(.name == \"$field_name\") | .value" 2>/dev/null)
    fi

    if [ -z "$token" ] || [ "$token" = "null" ]; then
        echo "❌ Could not retrieve $description from Bitwarden item '$item_name'"
        echo "   This token needs to be created in Bitwarden first."
        echo "   Item name: '$item_name'"
        echo "   Field: password or custom field '$field_name'"
        return 1
    fi

    echo "✅ Retrieved $description from Bitwarden"
    # Don't echo the actual token value for security
    return 0
}

echo "📋 Retrieving tokens..."
echo ""

# Retrieve GitHub token for Mira
echo "1. GitHub Token for Mira:"
if get_bw_token "Mira GitHub Token" "token" "GitHub Token for Mira"; then
    MIRA_GITHUB_TOKEN=$token
elif get_bw_token "mira-github-token" "password" "GitHub Token for Mira"; then
    MIRA_GITHUB_TOKEN=$token
else
    echo "   💡 To create: Go to GitHub → Settings → Developer settings → Personal access tokens"
    echo "   → Generate new token with 'repo' and 'workflow' permissions"
    echo "   → Save as 'Mira GitHub Token' in Bitwarden"
    MIRA_GITHUB_TOKEN=""
fi
echo ""

# Retrieve Jira token for Mira
echo "2. Jira Token for Mira:"
if get_bw_token "Mira Jira Token" "token" "Jira Token for Mira"; then
    MIRA_JIRA_TOKEN=$token
elif get_bw_token "mira-jira-token" "password" "Jira Token for Mira"; then
    MIRA_JIRA_TOKEN=$token
else
    echo "   💡 To create: Go to Jira → Account settings → Security → API tokens"
    echo "   → Create API token for Mira integration"
    echo "   → Save as 'Mira Jira Token' in Bitwarden"
    MIRA_JIRA_TOKEN=""
fi
echo ""

# Retrieve CircleCI token
echo "3. CircleCI API Token:"
if get_bw_token "CircleCI API Token" "token" "CircleCI API Token"; then
    CIRCLECI_API_TOKEN=$token
elif get_bw_token "circleci-api-token" "password" "CircleCI API Token"; then
    CIRCLECI_API_TOKEN=$token
else
    echo "   💡 To create: Go to CircleCI → User settings → Personal API Tokens"
    echo "   → Create new token with project permissions"
    echo "   → Save as 'CircleCI API Token' in Bitwarden"
    CIRCLECI_API_TOKEN=""
fi
echo ""

# Retrieve Cloudflare token
echo "4. Cloudflare API Token:"
if get_bw_token "Cloudflare API Token CI" "token" "Cloudflare API Token"; then
    CLOUDFLARE_API_TOKEN=$token
elif get_bw_token "cloudflare-api-token-ci" "password" "Cloudflare API Token"; then
    CLOUDFLARE_API_TOKEN=$token
elif get_bw_token "goblin-prod-cloudflare-api" "password" "Cloudflare API Token"; then
    CLOUDFLARE_API_TOKEN=$token
else
    echo "   💡 Found existing: goblin-prod-cloudflare-api"
    CLOUDFLARE_API_TOKEN=""
fi
echo ""

# Retrieve Kamatera credentials
echo "5. Kamatera Deploy Key/Token:"
if get_bw_token "Kamatera Deploy Key" "private_key" "Kamatera Deploy Key"; then
    KAMATERA_DEPLOY_KEY=$token
elif get_bw_token "kamatera-deploy-key" "password" "Kamatera Deploy Key"; then
    KAMATERA_DEPLOY_KEY=$token
else
    echo "   💡 Using existing Kamatera items found in vault"
    KAMATERA_DEPLOY_KEY=""
fi

if get_bw_token "Kamatera API Token" "token" "Kamatera API Token"; then
    KAMATERA_TOKEN=$token
elif get_bw_token "kamatera-token" "password" "Kamatera API Token"; then
    KAMATERA_TOKEN=$token
elif get_bw_token "Kamatera LLM API Key" "password" "Kamatera API Token"; then
    KAMATERA_TOKEN=$token
else
    echo "   💡 Using existing: Kamatera LLM API Key"
    KAMATERA_TOKEN=""
fi
echo ""

echo "🚀 Setting up GitHub Secrets..."
echo ""

# Set GitHub secrets
if [ -n "$MIRA_GITHUB_TOKEN" ]; then
    echo "$MIRA_GITHUB_TOKEN" | gh secret set MIRA_GITHUB_TOKEN --body -
    echo "✅ Set MIRA_GITHUB_TOKEN in GitHub secrets"
fi

if [ -n "$MIRA_JIRA_TOKEN" ]; then
    echo "$MIRA_JIRA_TOKEN" | gh secret set MIRA_JIRA_TOKEN --body -
    echo "✅ Set MIRA_JIRA_TOKEN in GitHub secrets"
fi

if [ -n "$CLOUDFLARE_API_TOKEN" ]; then
    echo "$CLOUDFLARE_API_TOKEN" | gh secret set CLOUDFLARE_API_TOKEN_CI --body -
    echo "✅ Set CLOUDFLARE_API_TOKEN_CI in GitHub secrets"
fi

if [ -n "$KAMATERA_DEPLOY_KEY" ]; then
    echo "$KAMATERA_DEPLOY_KEY" | gh secret set KAMATERA_DEPLOY_KEY --body -
    echo "✅ Set KAMATERA_DEPLOY_KEY in GitHub secrets"
fi

if [ -n "$KAMATERA_TOKEN" ]; then
    echo "$KAMATERA_TOKEN" | gh secret set KAMATERA_TOKEN --body -
    echo "✅ Set KAMATERA_TOKEN in GitHub secrets"
fi

echo ""
echo "🚀 Setting up CircleCI Context Secrets..."
echo ""

# Set CircleCI context secrets (requires CircleCI CLI to be configured)
if [ -n "$CIRCLECI_API_TOKEN" ]; then
    echo "Setting CircleCI API token in context..."
    # Use the correct org ID and existing context
    echo "$CIRCLECI_API_TOKEN" | circleci context store-secret --org-id bbdc9f2a-17bb-40bb-a3c6-88b58963fdfc circleci-agents CIRCLECI_API_TOKEN
    echo "✅ Set CIRCLECI_API_TOKEN in CircleCI context 'circleci-agents'"
else
    echo "⚠️  No CircleCI token found - skipping context setup"
fi

echo ""
echo "✅ Token setup complete!"
echo ""
echo "🔒 Security Notes:"
echo "- Tokens are retrieved from Bitwarden securely"
echo "- GitHub secrets are encrypted at rest"
echo "- CircleCI contexts provide secure access to pipelines"
echo "- Never log or expose token values"
echo ""
echo "🧪 Test the integration:"
echo "1. Create a PR with 'PROJ-123' in the title"
echo "2. Check that the require-jira-key workflow passes"
echo "3. Verify Mira comments appear on the PR"
echo ""
echo "📋 Next steps:"
echo "- Complete Mira console setup (upload config, enable features)"
echo "- Test webhook delivery from GitHub to Mira"
echo "- Monitor PRs for automatic Jira transitions"
