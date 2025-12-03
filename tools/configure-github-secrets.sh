#!/bin/bash
# Configure GitHub Secrets for Goblin Assistant Repositories
# This script helps you set up all required secrets for the multi-repo architecture

set -e

GITHUB_ORG="fuaadabdullah"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 GitHub Secrets Configuration Tool${NC}"
echo -e "${BLUE}=====================================${NC}\n"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is not installed${NC}"
    echo -e "${YELLOW}Install it with: brew install gh${NC}"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with GitHub CLI${NC}"
    echo -e "${YELLOW}Authenticate with: gh auth login${NC}"
    exit 1
fi

echo -e "${GREEN}✓ GitHub CLI authenticated${NC}\n"

# Function to set a secret
set_secret() {
    local repo=$1
    local secret_name=$2
    local secret_value=$3

    if [ -z "$secret_value" ]; then
        echo -e "${YELLOW}  ⊘ Skipping $secret_name (no value provided)${NC}"
        return 0
    fi

    echo "$secret_value" | gh secret set "$secret_name" --repo "$GITHUB_ORG/$repo" 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ Set $secret_name${NC}"
    else
        echo -e "${RED}  ✗ Failed to set $secret_name${NC}"
    fi
}

# Function to prompt for secret value
prompt_secret() {
    local secret_name=$1
    local description=$2
    local optional=$3

    echo -e "${BLUE}$secret_name${NC}"
    echo -e "${YELLOW}  Description: $description${NC}"

    if [ "$optional" = "true" ]; then
        echo -e "${YELLOW}  (Optional - press Enter to skip)${NC}"
    fi

    read -s -p "  Enter value: " secret_value
    echo ""
    echo "$secret_value"
}

# =============================================================================
# BACKEND SECRETS
# =============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 Backend Repository Secrets${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

REPO="goblin-assistant-backend"

echo -e "${YELLOW}Configure secrets for: ${GITHUB_ORG}/${REPO}${NC}\n"

# RENDER_API_KEY
RENDER_API_KEY=$(prompt_secret "RENDER_API_KEY" "API key from https://dashboard.render.com/account/settings" "false")
set_secret "$REPO" "RENDER_API_KEY" "$RENDER_API_KEY"

# RENDER_STAGING_SERVICE_ID
RENDER_STAGING_SERVICE_ID=$(prompt_secret "RENDER_STAGING_SERVICE_ID" "Service ID for staging backend (from Render dashboard)" "false")
set_secret "$REPO" "RENDER_STAGING_SERVICE_ID" "$RENDER_STAGING_SERVICE_ID"

# RENDER_PRODUCTION_SERVICE_ID
RENDER_PRODUCTION_SERVICE_ID=$(prompt_secret "RENDER_PRODUCTION_SERVICE_ID" "Service ID for production backend (from Render dashboard)" "false")
set_secret "$REPO" "RENDER_PRODUCTION_SERVICE_ID" "$RENDER_PRODUCTION_SERVICE_ID"

echo ""

# =============================================================================
# FRONTEND SECRETS
# =============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎨 Frontend Repository Secrets${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

REPO="goblin-assistant-frontend"

echo -e "${YELLOW}Configure secrets for: ${GITHUB_ORG}/${REPO}${NC}\n"

# VERCEL_TOKEN
VERCEL_TOKEN=$(prompt_secret "VERCEL_TOKEN" "API token from https://vercel.com/account/tokens" "false")
set_secret "$REPO" "VERCEL_TOKEN" "$VERCEL_TOKEN"

# VERCEL_ORG_ID
VERCEL_ORG_ID=$(prompt_secret "VERCEL_ORG_ID" "Organization ID from Vercel dashboard" "false")
set_secret "$REPO" "VERCEL_ORG_ID" "$VERCEL_ORG_ID"

# VERCEL_PROJECT_ID
VERCEL_PROJECT_ID=$(prompt_secret "VERCEL_PROJECT_ID" "Project ID from Vercel dashboard" "false")
set_secret "$REPO" "VERCEL_PROJECT_ID" "$VERCEL_PROJECT_ID"

# VITE_API_URL
VITE_API_URL=$(prompt_secret "VITE_API_URL" "Backend API URL (e.g., https://api.goblin-assistant.com)" "false")
set_secret "$REPO" "VITE_API_URL" "$VITE_API_URL"

# CHROMATIC_PROJECT_TOKEN
CHROMATIC_PROJECT_TOKEN=$(prompt_secret "CHROMATIC_PROJECT_TOKEN" "Project token from https://www.chromatic.com/start" "false")
set_secret "$REPO" "CHROMATIC_PROJECT_TOKEN" "$CHROMATIC_PROJECT_TOKEN"

echo ""

# =============================================================================
# CONTRACTS SECRETS
# =============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📜 Contracts Repository Secrets${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

REPO="goblin-assistant-contracts"

echo -e "${YELLOW}Configure secrets for: ${GITHUB_ORG}/${REPO}${NC}\n"

# NPM_TOKEN
NPM_TOKEN=$(prompt_secret "NPM_TOKEN" "Access token from https://www.npmjs.com/settings/~/tokens" "false")
set_secret "$REPO" "NPM_TOKEN" "$NPM_TOKEN"

# PYPI_TOKEN
PYPI_TOKEN=$(prompt_secret "PYPI_TOKEN" "API token from https://pypi.org/manage/account/token/" "false")
set_secret "$REPO" "PYPI_TOKEN" "$PYPI_TOKEN"

echo ""

# =============================================================================
# INFRASTRUCTURE SECRETS
# =============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🏗️  Infrastructure Repository Secrets${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

REPO="goblin-assistant-infra"

echo -e "${YELLOW}Configure secrets for: ${GITHUB_ORG}/${REPO}${NC}\n"

# AWS_ACCESS_KEY_ID
AWS_ACCESS_KEY_ID=$(prompt_secret "AWS_ACCESS_KEY_ID" "AWS access key ID for Terraform" "false")
set_secret "$REPO" "AWS_ACCESS_KEY_ID" "$AWS_ACCESS_KEY_ID"

# AWS_SECRET_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=$(prompt_secret "AWS_SECRET_ACCESS_KEY" "AWS secret access key for Terraform" "false")
set_secret "$REPO" "AWS_SECRET_ACCESS_KEY" "$AWS_SECRET_ACCESS_KEY"

# KUBE_CONFIG_STAGING
echo -e "${YELLOW}For KUBE_CONFIG_STAGING, provide base64-encoded kubeconfig${NC}"
echo -e "${YELLOW}  Tip: cat ~/.kube/staging-config | base64${NC}"
KUBE_CONFIG_STAGING=$(prompt_secret "KUBE_CONFIG_STAGING" "Base64-encoded kubeconfig for staging cluster" "true")
set_secret "$REPO" "KUBE_CONFIG_STAGING" "$KUBE_CONFIG_STAGING"

# KUBE_CONFIG_PRODUCTION
echo -e "${YELLOW}For KUBE_CONFIG_PRODUCTION, provide base64-encoded kubeconfig${NC}"
echo -e "${YELLOW}  Tip: cat ~/.kube/production-config | base64${NC}"
KUBE_CONFIG_PRODUCTION=$(prompt_secret "KUBE_CONFIG_PRODUCTION" "Base64-encoded kubeconfig for production cluster" "true")
set_secret "$REPO" "KUBE_CONFIG_PRODUCTION" "$KUBE_CONFIG_PRODUCTION"

echo ""

# =============================================================================
# OPTIONAL ORGANIZATION-LEVEL SECRETS
# =============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🌐 Optional Organization-Level Secrets${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${YELLOW}These secrets can be shared across all repositories${NC}\n"

read -p "Configure organization-level secrets? (y/N): " configure_org
if [[ "$configure_org" =~ ^[Yy]$ ]]; then
    # SLACK_WEBHOOK_URL
    SLACK_WEBHOOK_URL=$(prompt_secret "SLACK_WEBHOOK_URL" "Slack webhook URL for deployment notifications" "true")
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        echo "$SLACK_WEBHOOK_URL" | gh secret set "SLACK_WEBHOOK_URL" --org "$GITHUB_ORG" 2>&1
        echo -e "${GREEN}  ✓ Set SLACK_WEBHOOK_URL (org-level)${NC}"
    fi

    # INFRACOST_API_KEY
    INFRACOST_API_KEY=$(prompt_secret "INFRACOST_API_KEY" "Infracost API key from https://www.infracost.io" "true")
    if [ ! -z "$INFRACOST_API_KEY" ]; then
        echo "$INFRACOST_API_KEY" | gh secret set "INFRACOST_API_KEY" --org "$GITHUB_ORG" 2>&1
        echo -e "${GREEN}  ✓ Set INFRACOST_API_KEY (org-level)${NC}"
    fi
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ GitHub Secrets Configuration Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Configure GitHub Environments (staging, production)"
echo -e "  2. Set up branch protection rules"
echo -e "  3. Test the CI/CD pipeline with a test commit"
echo ""
echo -e "${YELLOW}View secrets at:${NC}"
echo -e "  Backend:   https://github.com/${GITHUB_ORG}/goblin-assistant-backend/settings/secrets/actions"
echo -e "  Frontend:  https://github.com/${GITHUB_ORG}/goblin-assistant-frontend/settings/secrets/actions"
echo -e "  Contracts: https://github.com/${GITHUB_ORG}/goblin-assistant-contracts/settings/secrets/actions"
echo -e "  Infra:     https://github.com/${GITHUB_ORG}/goblin-assistant-infra/settings/secrets/actions"
echo ""
