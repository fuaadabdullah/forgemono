# 🔐 GitHub Secrets Configuration Guide

This guide walks you through configuring all required GitHub Secrets for the Goblin Assistant multi-repo architecture.

---

## 📋 Quick Setup Options

### Option 1: Automated Setup (Recommended)
Use the provided script to configure all secrets interactively:

```bash
chmod +x tools/configure-github-secrets.sh
./tools/configure-github-secrets.sh
```

### Option 2: Manual Configuration
Follow the step-by-step instructions below for each repository.

---

## 🎯 Prerequisites

Before you begin, gather these credentials:

### Backend (Render)
- [ ] Render API key from https://dashboard.render.com/account/settings
- [ ] Staging service ID (create backend service on Render first)
- [ ] Production service ID (create backend service on Render first)

### Frontend (Vercel)
- [ ] Vercel API token from https://vercel.com/account/tokens
- [ ] Vercel Organization ID (found in team settings)
- [ ] Vercel Project ID (create project on Vercel first)
- [ ] Backend API URL (e.g., `https://api.goblin-assistant.com`)
- [ ] Chromatic project token from https://www.chromatic.com/start

### Contracts (npm + PyPI)
- [ ] npm access token from https://www.npmjs.com/settings/~/tokens
- [ ] PyPI API token from https://pypi.org/manage/account/token/

### Infrastructure (AWS + Kubernetes)
- [ ] AWS Access Key ID (IAM user with appropriate permissions)
- [ ] AWS Secret Access Key
- [ ] Kubernetes staging config (base64-encoded)
- [ ] Kubernetes production config (base64-encoded)

### Optional (Organization-Level)
- [ ] Slack webhook URL for notifications
- [ ] Infracost API key from https://www.infracost.io

---

## 📦 Backend Repository Secrets

**Repository**: https://github.com/fuaadabdullah/goblin-assistant-backend

### Navigate to Secrets Settings
```
https://github.com/fuaadabdullah/goblin-assistant-backend/settings/secrets/actions
```

### Required Secrets

#### 1. RENDER_API_KEY
**Purpose**: Authenticate with Render API for deployments
**How to get it**:
1. Go to https://dashboard.render.com/account/settings
2. Scroll to "API Keys"
3. Click "Generate New API Key"
4. Copy the key (starts with `rnd_`)

**Set via GitHub CLI**:
```bash

echo "rnd_YOUR_API_KEY_HERE" | gh secret set RENDER_API_KEY \
  --repo fuaadabdullah/goblin-assistant-backend
```

**Set via Web UI**:

1. Click "New repository secret"
2. Name: `RENDER_API_KEY`
3. Value: `rnd_YOUR_API_KEY_HERE`
4. Click "Add secret"

---

#### 2. RENDER_STAGING_SERVICE_ID
**Purpose**: Deploy to staging backend service
**How to get it**:

1. Create a backend service on Render for staging
2. Go to service settings
3. Copy the Service ID from the URL (e.g., `srv-xxxxx`)

**Set via GitHub CLI**:

```bash
echo "srv-staging-id" | gh secret set RENDER_STAGING_SERVICE_ID \
  --repo fuaadabdullah/goblin-assistant-backend
```

---

#### 3. RENDER_PRODUCTION_SERVICE_ID
**Purpose**: Deploy to production backend service
**How to get it**:
1. Create a backend service on Render for production
2. Go to service settings
3. Copy the Service ID from the URL (e.g., `srv-xxxxx`)

**Set via GitHub CLI**:
```bash

echo "srv-production-id" | gh secret set RENDER_PRODUCTION_SERVICE_ID \
  --repo fuaadabdullah/goblin-assistant-backend
```

---

## 🎨 Frontend Repository Secrets

**Repository**: <https://github.com/fuaadabdullah/goblin-assistant-frontend>

### Navigate to Secrets Settings
```
<https://github.com/fuaadabdullah/goblin-assistant-frontend/settings/secrets/actions>
```

### Required Secrets

#### 1. VERCEL_TOKEN
**Purpose**: Authenticate with Vercel API for deployments
**How to get it**:

1. Go to <https://vercel.com/account/tokens>
2. Click "Create Token"
3. Name it "GitHub Actions"
4. Select expiration (recommend "No Expiration" for CI/CD)
5. Copy the token

**Set via GitHub CLI**:

```bash
echo "your-vercel-token" | gh secret set VERCEL_TOKEN \
  --repo fuaadabdullah/goblin-assistant-frontend
```

---

#### 2. VERCEL_ORG_ID
**Purpose**: Identify your Vercel organization
**How to get it**:
1. Go to https://vercel.com/account
2. Click on your team/organization
3. Go to "Settings"
4. Copy the "Team ID" (starts with `team_`)

**Set via GitHub CLI**:
```bash

echo "team_xxxxx" | gh secret set VERCEL_ORG_ID \
  --repo fuaadabdullah/goblin-assistant-frontend
```

---

#### 3. VERCEL_PROJECT_ID
**Purpose**: Identify your Vercel project
**How to get it**:

**Option A - From existing project**:

1. Go to your project on Vercel
2. Go to "Settings"
3. Copy the "Project ID" (starts with `prj_`)

**Option B - From CLI**:

```bash
# Link project first
cd /tmp/goblin-repos/goblin-assistant-frontend
vercel link

# Get project ID
vercel project ls --json | jq '.projects[] | select(.name=="goblin-assistant-frontend") | .id'
```

**Set via GitHub CLI**:
```bash

echo "prj_xxxxx" | gh secret set VERCEL_PROJECT_ID \
  --repo fuaadabdullah/goblin-assistant-frontend
```

---

#### 4. VITE_API_URL
**Purpose**: Backend API endpoint for frontend to connect to
**Value**: Your backend API URL

**Examples**:

- Production: `<https://api.goblin-assistant.com`>
- Staging: `<https://staging-api.goblin-assistant.com`>
- Development: `<http://localhost:8000`>

**Set via GitHub CLI**:

```bash
echo "https://api.goblin-assistant.com" | gh secret set VITE_API_URL \
  --repo fuaadabdullah/goblin-assistant-frontend
```

---

#### 5. CHROMATIC_PROJECT_TOKEN
**Purpose**: Visual regression testing with Chromatic
**How to get it**:
1. Go to https://www.chromatic.com
2. Sign in with GitHub
3. Click "Choose from GitHub" and select `goblin-assistant-frontend`
4. Copy the project token (starts with `chpt_`)

**Set via GitHub CLI**:
```bash

echo "chpt_xxxxx" | gh secret set CHROMATIC_PROJECT_TOKEN \
  --repo fuaadabdullah/goblin-assistant-frontend
```

---

## 📜 Contracts Repository Secrets

**Repository**: <https://github.com/fuaadabdullah/goblin-assistant-contracts>

### Navigate to Secrets Settings
```
<https://github.com/fuaadabdullah/goblin-assistant-contracts/settings/secrets/actions>
```

### Required Secrets

#### 1. NPM_TOKEN
**Purpose**: Publish packages to npm registry
**How to get it**:

1. Go to <https://www.npmjs.com/settings/~/tokens>
2. Click "Generate New Token"
3. Select "Automation" (for CI/CD)
4. Copy the token (starts with `npm_`)

**Set via GitHub CLI**:

```bash
echo "npm_xxxxx" | gh secret set NPM_TOKEN \
  --repo fuaadabdullah/goblin-assistant-contracts
```

---

#### 2. PYPI_TOKEN
**Purpose**: Publish packages to PyPI registry
**How to get it**:
1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Token name: "GitHub Actions"
4. Scope: "Entire account" or specific project
5. Copy the token (starts with `pypi-`)

**Set via GitHub CLI**:
```bash

echo "pypi-xxxxx" | gh secret set PYPI_TOKEN \
  --repo fuaadabdullah/goblin-assistant-contracts
```

---

## 🏗️ Infrastructure Repository Secrets

**Repository**: <https://github.com/fuaadabdullah/goblin-assistant-infra>

### Navigate to Secrets Settings
```
<https://github.com/fuaadabdullah/goblin-assistant-infra/settings/secrets/actions>
```

### Required Secrets

#### 1. AWS_ACCESS_KEY_ID
**Purpose**: Terraform access to AWS
**How to get it**:

1. Go to AWS IAM Console
2. Create a new user or use existing
3. Attach policy: `AdministratorAccess` (or more restrictive for production)
4. Create access key
5. Copy the Access Key ID

**Set via GitHub CLI**:

```bash
echo "AKIAIOSFODNN7EXAMPLE" | gh secret set AWS_ACCESS_KEY_ID \
  --repo fuaadabdullah/goblin-assistant-infra
```

---

#### 2. AWS_SECRET_ACCESS_KEY
**Purpose**: Terraform authentication to AWS
**How to get it**:
1. Same as AWS_ACCESS_KEY_ID process
2. Copy the Secret Access Key (only shown once!)

**Set via GitHub CLI**:
```bash

echo "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" | gh secret set AWS_SECRET_ACCESS_KEY \
  --repo fuaadabdullah/goblin-assistant-infra
```

---

#### 3. KUBE_CONFIG_STAGING
**Purpose**: Deploy to staging Kubernetes cluster
**How to get it**:

1. Get your staging kubeconfig file
2. Base64 encode it:

   ```bash
   cat ~/.kube/staging-config | base64 | tr -d '\n'
   ```
3. Copy the output

**Set via GitHub CLI**:
```bash

cat ~/.kube/staging-config | base64 | tr -d '\n' | \
  gh secret set KUBE_CONFIG_STAGING \
  --repo fuaadabdullah/goblin-assistant-infra
```

---

#### 4. KUBE_CONFIG_PRODUCTION
**Purpose**: Deploy to production Kubernetes cluster
**How to get it**:

1. Get your production kubeconfig file
2. Base64 encode it:

   ```bash
   cat ~/.kube/production-config | base64 | tr -d '\n'
   ```
3. Copy the output

**Set via GitHub CLI**:
```bash

cat ~/.kube/production-config | base64 | tr -d '\n' | \
  gh secret set KUBE_CONFIG_PRODUCTION \
  --repo fuaadabdullah/goblin-assistant-infra
```

---

## 🌐 Optional: Organization-Level Secrets

These secrets can be shared across all repositories in your organization.

### Navigate to Organization Secrets Settings
```
<https://github.com/organizations/YOUR_ORG/settings/secrets/actions>
```

### Optional Secrets

#### 1. SLACK_WEBHOOK_URL
**Purpose**: Send deployment notifications to Slack
**How to get it**:

1. Go to <https://api.slack.com/apps>
2. Create a new app or select existing
3. Go to "Incoming Webhooks"
4. Activate incoming webhooks
5. Create a webhook for your channel
6. Copy the webhook URL

**Set via GitHub CLI**:

```bash
echo "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX" | \
  gh secret set SLACK_WEBHOOK_URL --org fuaadabdullah
```

---

#### 2. INFRACOST_API_KEY
**Purpose**: Cost estimation for infrastructure changes
**How to get it**:
1. Go to https://www.infracost.io
2. Sign up for free account
3. Go to "Settings" → "API Keys"
4. Copy the API key

**Set via GitHub CLI**:
```bash

echo "ico-xxxxx" | gh secret set INFRACOST_API_KEY --org fuaadabdullah
```

---

## ✅ Verification

After configuring all secrets, verify they are set correctly:

### Backend

```bash
gh secret list --repo fuaadabdullah/goblin-assistant-backend
```

**Expected output**:
```
RENDER_API_KEY                Updated 2025-12-03
RENDER_PRODUCTION_SERVICE_ID  Updated 2025-12-03
RENDER_STAGING_SERVICE_ID     Updated 2025-12-03
```

### Frontend
```bash

gh secret list --repo fuaadabdullah/goblin-assistant-frontend
```

**Expected output**:
```
CHROMATIC_PROJECT_TOKEN  Updated 2025-12-03
VERCEL_ORG_ID            Updated 2025-12-03
VERCEL_PROJECT_ID        Updated 2025-12-03
VERCEL_TOKEN             Updated 2025-12-03
VITE_API_URL             Updated 2025-12-03
```

### Contracts

```bash
gh secret list --repo fuaadabdullah/goblin-assistant-contracts
```

**Expected output**:
```
NPM_TOKEN   Updated 2025-12-03
PYPI_TOKEN  Updated 2025-12-03
```

### Infrastructure
```bash

gh secret list --repo fuaadabdullah/goblin-assistant-infra
```

**Expected output**:
```
AWS_ACCESS_KEY_ID        Updated 2025-12-03
AWS_SECRET_ACCESS_KEY    Updated 2025-12-03
KUBE_CONFIG_PRODUCTION   Updated 2025-12-03
KUBE_CONFIG_STAGING      Updated 2025-12-03
```

---

## 🧪 Test Your Setup

After configuring secrets, test the CI/CD pipeline:

### 1. Test Backend CI

```bash
cd /tmp/goblin-repos/goblin-assistant-backend
git checkout -b test-secrets
echo "# Test" >> README.md
git add README.md
git commit -m "test: Verify secrets configuration"
git push origin test-secrets
```

Visit: https://github.com/fuaadabdullah/goblin-assistant-backend/actions

**Expected**: CI workflow runs successfully (lint, test, build, security scan)

### 2. Test Frontend CI
```bash

cd /tmp/goblin-repos/goblin-assistant-frontend
git checkout -b test-secrets
echo "# Test" >> README.md
git add README.md
git commit -m "test: Verify secrets configuration"
git push origin test-secrets
```

Visit: <https://github.com/fuaadabdullah/goblin-assistant-frontend/actions>

**Expected**: CI workflow runs successfully (ESLint, Vitest, Storybook, Chromatic)

---

## 🚨 Troubleshooting

### Secret Not Found Error
**Error**: `Secret RENDER_API_KEY not found`

**Solution**:

```bash
# Verify secret exists
gh secret list --repo fuaadabdullah/goblin-assistant-backend

# Re-add if missing
echo "your-secret-value" | gh secret set RENDER_API_KEY \
  --repo fuaadabdullah/goblin-assistant-backend
```

### Authentication Failed
**Error**: `Authentication failed`

**Solution**:
1. Verify the token/key is correct
2. Check if token has expired
3. Ensure proper permissions (API token scopes)
4. Regenerate and update the secret

### Base64 Decoding Error
**Error**: `illegal base64 data at input byte`

**Solution**:
```bash

# Ensure no newlines in base64 encoding
cat ~/.kube/config | base64 | tr -d '\n' | gh secret set KUBE_CONFIG_STAGING \
  --repo fuaadabdullah/goblin-assistant-infra
```

---

## 📚 Additional Resources

- **GitHub Secrets Documentation**: <https://docs.github.com/en/actions/security-guides/encrypted-secrets>
- **Render API Docs**: <https://render.com/docs/api>
- **Vercel API Docs**: <https://vercel.com/docs/rest-api>
- **Chromatic Docs**: <https://www.chromatic.com/docs/>
- **AWS IAM Best Practices**: <https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html>

---

## 🔒 Security Best Practices

1. **Use least-privilege access** - Grant only necessary permissions
2. **Rotate secrets regularly** - Especially for long-lived tokens
3. **Use environment-specific secrets** - Separate staging/production credentials
4. **Never commit secrets** - Always use GitHub Secrets, never hardcode
5. **Monitor secret usage** - Check audit logs regularly
6. **Use organization secrets** - Share common secrets (like Slack webhooks) at org level
7. **Set expiration dates** - For tokens that support it

---

**Configuration Complete?** ✅
**Next Steps**: [Configure GitHub Environments](./GITHUB_ENVIRONMENTS_SETUP.md)
