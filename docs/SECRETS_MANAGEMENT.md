# ForgeMonorepo - Secret Management with Bitwarden

This document outlines the secure secret management practices for the ForgeMonorepo using Bitwarden CLI instead of local .env files.

## 🚨 Security Policy

**NEVER store secrets in .env files or commit them to git.** All secrets must be stored in Bitwarden and retrieved programmatically.

## 🔐 Bitwarden Setup

### Prerequisites

1. Install Bitwarden CLI:

   ```bash
   npm install -g @bitwarden/cli
   ```

2. Login to Bitwarden:

   ```bash

   bw login
   ```

3. Unlock vault (required for each session):

   ```bash
   export BW_SESSION=$(bw unlock --raw)
   ```

### Secret Naming Convention

All secrets follow the pattern: `goblin-{app/component}-{service}`

Examples:

- `goblin-assistant-openai` - OpenAI API key for goblin-assistant
- `goblin-forge-lite-supabase-url` - Supabase URL for forge-lite
- `goblin-prod-jwt-secret` - JWT secret for production

## 🛠️ Secret Management Tools

### Secret Manager Script (`tools/secrets.sh`)

The main tool for managing secrets:

```bash

# Get a secret
./tools/secrets.sh get goblin-assistant-openai

# Set a new secret
./tools/secrets.sh set goblin-assistant-openai "sk-your-key-here" "OpenAI API key for development"

# List all secrets
./tools/secrets.sh list

# Load secrets for an app (creates temporary .env file)
./tools/secrets.sh load goblin-assistant

# Clean up generated .env files
./tools/secrets.sh cleanup
```

### .env File Monitor (`tools/monitor-env-files.sh`)

Monitors for unauthorized .env files:

```bash
# Check for unauthorized .env files
./tools/monitor-env-files.sh

# Generate JSON report
./tools/monitor-env-files.sh report
```

## 📋 Development Workflow

### For Local Development

1. **Never create .env files manually** - they will be flagged by the monitor
2. **Use the secret manager** to load required secrets:
   ```bash

   ./tools/secrets.sh load your-app-name
   ```

3. **Clean up after development**:

   ```bash
   ./tools/secrets.sh cleanup
   ```

### For CI/CD

CI/CD pipelines automatically fetch secrets from Bitwarden. See:

- `apps/goblin-assistant/.circleci/fetch_secrets.sh` - CircleCI secret fetching
- `apps/goblin-assistant/deploy-vercel-bw.sh` - Vercel deployment with Bitwarden

## 🔍 Monitoring & Security

### Pre-commit Hooks

The repository includes gitleaks pre-commit hooks that scan for secrets before commits.

### CI/CD Security Checks

- **CircleCI**: Runs `./tools/monitor-env-files.sh` in all pipelines
- **Pre-commit**: Runs gitleaks on staged files
- **Manual checks**: Run `./tools/monitor-env-files.sh` anytime

### What Gets Flagged

The monitor flags .env files containing:

- API keys (sk-, AIza, etc.)
- Tokens, secrets, passwords
- Real values (not placeholders like "your-key-here")

Allowed .env files:

- `.env.example` - Template files
- `.env.template` - Template files
- Files in `/tools/` - For development utilities

## 🚀 Migration Guide

### From .env Files to Bitwarden

1. **Extract secrets** from existing .env files
2. **Store in Bitwarden**:
   ```bash

   ./tools/secrets.sh set goblin-app-service "your-secret-value" "Description"
   ```

3. **Delete .env files**:

   ```bash
   rm dangerous-env-file.env
   ```
4. **Update code** to use environment variables or secret manager

### Example Migration

**Before (❌ Dangerous)**:
```bash

# .env file
OPENAI_API_KEY=sk-real-key-here
```

**After (✅ Secure)**:

```bash
# Store in Bitwarden
./tools/secrets.sh set goblin-assistant-openai "sk-real-key-here" "OpenAI API key"

# Load in code
import os
api_key = os.getenv('OPENAI_API_KEY') or get_secret_from_bitwarden()
```

## 📚 Common Secrets

### Goblin Assistant

- `goblin-assistant-openai` - OpenAI API key
- `goblin-assistant-anthropic` - Anthropic API key
- `goblin-assistant-supabase-url` - Supabase URL
- `goblin-assistant-supabase-anon` - Supabase anonymous key

### Production Secrets

- `goblin-prod-fastapi-secret` - FastAPI secret key
- `goblin-prod-db-url` - Database URL
- `goblin-prod-jwt` - JWT secret

## 🔧 Troubleshooting

### "Bitwarden vault is locked"

   ```bash

   export BW_SESSION=$(bw unlock --raw)
   ```

### "Secret not found"

   ```bash
   ./tools/secrets.sh list  # Check available secrets
   bw list items --search "goblin-"  # Direct Bitwarden search
   ```

### Monitor shows false positives

Update the monitor script to exclude legitimate files or adjust patterns in `tools/monitor-env-files.sh`.

## 📞 Support

For security issues or secret management questions:

1. Check this documentation
2. Run `./tools/secrets.sh help`
3. Contact the security team

---

**Remember**: Security is everyone's responsibility. Never commit secrets to git!
