# 🔐 GitHub Secrets - Quick Reference Card

## 🚀 Quick Setup (Recommended)

Run the automated configuration script:

```bash
./tools/configure-github-secrets.sh
```

This interactive script will guide you through setting up all required secrets for all repositories.

---

## 📋 Secrets Checklist

### ✅ Backend (goblin-assistant-backend)
- [ ] `FLY_API_TOKEN` - From Fly.io dashboard → Account → Access Tokens

**Set via CLI**:
```bash

gh secret set FLY_API_TOKEN --repo fuaadabdullah/goblin-assistant-backend
```

**Verify**:

```bash
gh secret list --repo fuaadabdullah/goblin-assistant-backend
```

---

### ✅ Frontend (goblin-assistant-frontend)
- [ ] `VERCEL_TOKEN` - Vercel → Account Settings → Tokens → Create
- [ ] `VERCEL_ORG_ID` - Vercel → Team Settings → Team ID
- [ ] `VERCEL_PROJECT_ID` - Create project first, then copy from Settings
- [ ] `VITE_API_URL` - Your backend URL (e.g., `https://api.goblin-assistant.com`)
- [ ] `CHROMATIC_PROJECT_TOKEN` - Chromatic.com → Add project → Copy token

**Set via CLI**:
```bash

gh secret set VERCEL_TOKEN --repo fuaadabdullah/goblin-assistant-frontend
gh secret set VERCEL_ORG_ID --repo fuaadabdullah/goblin-assistant-frontend
gh secret set VERCEL_PROJECT_ID --repo fuaadabdullah/goblin-assistant-frontend
gh secret set VITE_API_URL --repo fuaadabdullah/goblin-assistant-frontend
gh secret set CHROMATIC_PROJECT_TOKEN --repo fuaadabdullah/goblin-assistant-frontend
```

**Verify**:

```bash
gh secret list --repo fuaadabdullah/goblin-assistant-frontend
```

---

### ✅ Contracts (goblin-assistant-contracts)
- [ ] `NPM_TOKEN` - npmjs.com → Account Settings → Tokens → Generate (Automation)
- [ ] `PYPI_TOKEN` - pypi.org → Account Settings → API Tokens → Add

**Set via CLI**:
```bash

gh secret set NPM_TOKEN --repo fuaadabdullah/goblin-assistant-contracts
gh secret set PYPI_TOKEN --repo fuaadabdullah/goblin-assistant-contracts
```

**Verify**:

```bash
gh secret list --repo fuaadabdullah/goblin-assistant-contracts
```

---

### ✅ Infrastructure (goblin-assistant-infra)
- [ ] `AWS_ACCESS_KEY_ID` - AWS IAM → Users → Security Credentials → Create Access Key
- [ ] `AWS_SECRET_ACCESS_KEY` - Same as above (only shown once!)
- [ ] `KUBE_CONFIG_STAGING` - Base64-encoded kubeconfig for staging cluster
- [ ] `KUBE_CONFIG_PRODUCTION` - Base64-encoded kubeconfig for production cluster

**Set via CLI**:
```bash

gh secret set AWS_ACCESS_KEY_ID --repo fuaadabdullah/goblin-assistant-infra
gh secret set AWS_SECRET_ACCESS_KEY --repo fuaadabdullah/goblin-assistant-infra

# Encode kubeconfig
cat ~/.kube/staging-config | base64 | tr -d '\n' | \
  gh secret set KUBE_CONFIG_STAGING --repo fuaadabdullah/goblin-assistant-infra

cat ~/.kube/production-config | base64 | tr -d '\n' | \
  gh secret set KUBE_CONFIG_PRODUCTION --repo fuaadabdullah/goblin-assistant-infra
```

**Verify**:

```bash
gh secret list --repo fuaadabdullah/goblin-assistant-infra
```

---

## 🌐 Optional: Organization Secrets

These secrets are shared across all repositories:

- [ ] `SLACK_WEBHOOK_URL` - Slack → Apps → Incoming Webhooks → Add to Channel
- [ ] `INFRACOST_API_KEY` - Infracost.io → Sign Up → Settings → API Keys

**Set via CLI**:
```bash

gh secret set SLACK_WEBHOOK_URL --org fuaadabdullah
gh secret set INFRACOST_API_KEY --org fuaadabdullah
```

**Verify**:

```bash
gh secret list --org fuaadabdullah
```

---

## 🔗 Direct Links

### Credential Creation
- **Fly.io API Token**: https://fly.io/user/personal_access_tokens
- **Vercel Token**: https://vercel.com/account/tokens
- **npm Token**: https://www.npmjs.com/settings/~/tokens
- **PyPI Token**: https://pypi.org/manage/account/token/
- **Chromatic**: https://www.chromatic.com/start
- **AWS IAM**: https://console.aws.amazon.com/iam/
- **Slack Webhooks**: https://api.slack.com/apps
- **Infracost**: https://www.infracost.io

### GitHub Secret Settings
- **Backend**: https://github.com/fuaadabdullah/goblin-assistant-backend/settings/secrets/actions
- **Frontend**: https://github.com/fuaadabdullah/goblin-assistant-frontend/settings/secrets/actions
- **Contracts**: https://github.com/fuaadabdullah/goblin-assistant-contracts/settings/secrets/actions
- **Infra**: https://github.com/fuaadabdullah/goblin-assistant-infra/settings/secrets/actions

---

## 🧪 Test Setup

After configuring secrets, test with a dummy commit:

```bash

# Backend
cd /tmp/goblin-repos/goblin-assistant-backend
git checkout -b test-ci
echo "# Test" >> README.md
git add . && git commit -m "test: secrets" && git push origin test-ci

# Frontend
cd /tmp/goblin-repos/goblin-assistant-frontend
git checkout -b test-ci
echo "# Test" >> README.md
git add . && git commit -m "test: secrets" && git push origin test-ci
```

**Expected**: Workflows run successfully in GitHub Actions

---

## 🚨 Common Issues

### "Secret not found"

```bash
# Re-add the secret
echo "your-value" | gh secret set SECRET_NAME --repo owner/repo
```

### "Authentication failed"
- Check if token expired
- Verify correct permissions/scopes
- Regenerate and update

### "Base64 decode error"
```bash

# Remove newlines from base64 encoding
cat file | base64 | tr -d '\n' | gh secret set SECRET_NAME --repo owner/repo
```

---

## 📚 Full Documentation

For detailed step-by-step instructions, see:

- **Complete Guide**: `docs/GITHUB_SECRETS_SETUP.md`
- **Automated Script**: `tools/configure-github-secrets.sh`

---

**Next Steps**: [Configure GitHub Environments](./GITHUB_ENVIRONMENTS_SETUP.md)
