---
description: "API_KEYS_MANAGEMENT"
---

# API Keys & Secrets Management

This guide covers best practices for managing API keys, secrets, and sensitive configuration in the ForgeMonorepo.

## Core Principles

- **Never commit secrets** to version control
- Use environment-specific configuration files
- Implement proper access controls and rotation policies
- Coordinate shared secrets outside of the repository

## Local Development Setup

### Environment Variables

Use `.env` files for local development secrets:

```bash
# Copy example file and fill in values
cp GoblinOS/.env.example GoblinOS/.env
```

Example `.env` file structure:

```bash

# API Keys
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GROQ_API_KEY=gsk_your-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Service URLs
REDIS_URL=redis://localhost:6379
```

### Python Applications

For Python apps, use `python-dotenv` to load environment variables:

```python
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access secrets
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")
```

### System Keychains

For sensitive local development keys, use system keychains:

**macOS Keychain:**

```bash

# Store a secret
security add-generic-password -s "myapp-api-key" -a "myapp" -w "secret-value"

# Retrieve a secret
security find-generic-password -s "myapp-api-key" -a "myapp" -w
```

## Production Deployment

### Docker Compose Secrets

Use Docker secrets for service-based deployments:

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    image: myapp:latest
    secrets:
      - api_key
    environment:
      - API_KEY_FILE=/run/secrets/api_key

secrets:
  api_key:
    file: ./secrets/api_key.txt
```

### Kubernetes Secrets

For Kubernetes deployments, use Secret resources:

```yaml

apiVersion: v1
kind: Secret
metadata:
  name: myapp-secrets
type: Opaque
data:
  api-key: bXktc2VjcmV0LWFwaS1rZXk=  # base64 encoded
  db-password: cGFzc3dvcmQ=          # base64 encoded
```

Access in pods:

```yaml
env:
  - name: API_KEY
    valueFrom:
      secretKeyRef:
        name: myapp-secrets
        key: api-key
```

## Secret Rotation

### Automated Rotation

For services supporting automated rotation:

```bash

# AWS IAM access keys
aws iam create-access-key --user-name my-user
aws iam delete-access-key --user-name my-user --access-key-id OLD_KEY_ID

# GitHub personal access tokens

# 1. Create new token in GitHub UI

# 2. Update all applications

# 3. Revoke old token
```

### Manual Coordination

For shared secrets requiring coordination:

1. **Announce rotation** in team communication channels
2. **Provide transition period** for updates
3. **Verify all systems updated** before revoking old secrets
4. **Document rotation procedures** for future reference

## Security Best Practices

### Access Control

- Use principle of least privilege
- Rotate keys regularly (recommended: 90 days)
- Monitor secret usage and access patterns
- Implement proper logging without exposing secrets

### Validation

Always validate secrets are loaded correctly:

```python
def validate_config():
    required_vars = ['API_KEY', 'DATABASE_URL', 'SECRET_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    # Validate API key format if known
    api_key = os.getenv('API_KEY')
    if api_key and not api_key.startswith('sk-'):
        raise ValueError("API_KEY appears to be malformed")

# Call at application startup
validate_config()
```

## Tools and Resources

- **Bitwarden**: Primary vault for storing and rotating secrets
- **1Password**: Alternative vault solution
- **HashiCorp Vault**: Enterprise secret management
- **AWS Secrets Manager**: Cloud-native secret storage
- **Azure Key Vault**: Microsoft cloud secret management

## Troubleshooting

### Common Issues

**Environment variables not loading:**

```bash

# Check if .env file exists
ls -la .env

# Verify python-dotenv is installed
pip list | grep python-dotenv

# Debug loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('API_KEY'))"
```

**Docker secrets not accessible:**

```bash
# Check secret file permissions
ls -la /run/secrets/

# Verify secret content
cat /run/secrets/api_key
```

Rotations and shared secrets should be coordinated outside of the repo.

