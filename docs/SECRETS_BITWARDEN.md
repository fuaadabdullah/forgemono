# Bitwarden Secrets Management

This guide explains how to manage secrets for the ForgeMonorepo using Bitwarden CLI.

## Prerequisites

1. **Install Bitwarden CLI**:

   ```bash
   brew install bitwarden-cli
   ```

2. **Login to Bitwarden**:
   ```bash

   bw login
   ```

3. **Unlock vault** (required for each session):

   ```bash
   bw unlock
   ```
   This will provide a session token that you can export:
   ```bash

   export BW_SESSION="your-session-token-here"
   ```

## Required Secrets

Add these secrets to your Bitwarden vault:

### LLM API Keys

- `KAMATERA_LLM_API_KEY` - API key for Kamatera-hosted LLM runtime
- `LOCAL_LLM_API_KEY` - API key for local LLM proxy
- `GROQ_API_KEY` - API key for Groq LLM service

### Cloud Provider API Keys

- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `GOOGLE_API_KEY` - Google AI API key

### AI Services

- `RAPTOR_API_KEY` - API key for Raptor Mini service

## Using the Secrets Management Script

The `scripts/bw-secrets.sh` script provides convenient commands for managing secrets:

### Check vault status

```bash
./scripts/bw-secrets.sh status
```

### Export all secrets to environment variables
```bash

./scripts/bw-secrets.sh export
```

### Setup .env file for a service

```bash
# For backend
./scripts/bw-secrets.sh setup backend

# For raptor-mini
./scripts/bw-secrets.sh setup raptor-mini
```

### List all required secrets
```bash

./scripts/bw-secrets.sh list
```

## Manual Secret Retrieval

You can also manually retrieve secrets:

```bash
# Get a specific secret
bw get password SECRET_NAME

# Export to environment variable
export SECRET_NAME="$(bw get password SECRET_NAME)"
```

## Adding Secrets to Bitwarden

To add a new secret to your vault:

```bash

bw create item
```

Follow the interactive prompts to create a login item with the secret name and password.

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use strong, unique passwords** for each secret
3. **Rotate secrets regularly** (recommended: every 90 days)
4. **Use environment-specific secrets** when possible
5. **Limit vault access** to authorized team members only

## Troubleshooting

### Vault is locked

```bash
bw unlock
```

### Permission denied
Make sure you're logged in and have access to the vault:
```bash

bw login
bw unlock
```

### Secret not found
Verify the secret name exists in your vault:

```bash
bw list items --search "SECRET_NAME"
```

## Integration with CI/CD

For CI/CD pipelines, use Bitwarden CLI in your deployment scripts:

```bash

# Login (use API key for CI)
bw login --apikey

# Unlock vault
bw unlock --passwordenv BW_PASSWORD

# Get secrets
export API_KEY="$(bw get password API_KEY)"
```

See `.circleci/config.yml` for examples of CI integration.
