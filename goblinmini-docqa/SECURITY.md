# 🔐 Security Configuration Guide

## API Token Management

### DOCQA_TOKEN

- **Purpose**: Authenticates API requests to the GoblinMini-DocQA service
- **Format**: 64-byte URL-safe token (88 characters when base64-encoded)
- **Generation**: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`
- **Storage**: Environment variable only (never in code or config files)
- **Rotation**: Monthly rotation recommended

### Token Rotation Procedure

1. **Generate New Token**:

   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

2. **Update All Environments**:
   - Development: Update `.env` file
   - Staging: Update deployment secrets
   - Production: Update Kubernetes secrets / environment variables

3. **Deploy Changes**:
   - Restart all application instances
   - Verify old tokens are invalidated
   - Update client applications with new token

4. **Cleanup**:
   - Remove old tokens from all storage
   - Update documentation with new token references

## Container Security

### Read-Only Filesystem

- **Purpose**: Prevents filesystem modifications by malicious actors
- **Implementation**: `read_only: true` in docker-compose.yml
- **Temporary Storage**: `/tmp` mounted as tmpfs for temporary files
- **Data Volumes**: Explicitly mounted as needed (e.g., DOCQA_ROOT as read-only)

### Non-Root User

- **User**: `goblin` (UID 1001)
- **Purpose**: Limits attack surface by running with minimal privileges
- **File Permissions**: Application files owned by goblin user

### Volume Mounts

- **DOCQA_ROOT**: Mounted as read-only (`:ro`) to prevent data modification
- **Security**: Ensures application cannot modify input data

## Environment Variables

### Required Variables

```bash

DOCQA_TOKEN=<secure-64-byte-token>
DOCQA_ROOT=/mnt/allowed
REDIS_URL=redis://redis:6379/0
```

### Optional Variables

```bash
COPILOT_API_URL=https://api.github.com/copilot
COPILOT_API_KEY=<github-copilot-token>
MAX_PROXY_DAILY_TOKENS=100000
```

## Security Monitoring

### Token Usage Monitoring

- Log all authentication attempts
- Alert on failed authentication attempts
- Monitor token usage patterns

### Container Security

- Monitor for privilege escalation attempts
- Alert on filesystem write attempts in read-only containers
- Monitor resource usage for anomalies

## Incident Response

### Token Compromise

1. **Immediate**: Generate new token
2. **Deploy**: Update all environments within 1 hour
3. **Investigate**: Review access logs for unauthorized usage
4. **Communicate**: Notify affected parties if necessary

### Container Breach

1. **Isolate**: Stop affected containers
2. **Investigate**: Analyze container logs and filesystem
3. **Rebuild**: Deploy from clean images
4. **Update**: Rotate all secrets

## Compliance

### Data Protection

- No sensitive data stored in application containers
- All data encrypted in transit and at rest
- Minimal data retention policies

### Access Control

- API token required for all operations
- No anonymous access allowed
- Audit logging for all operations

---

## 🔄 Token Rotation Schedule

- **Development**: Rotate every 3 months
- **Staging**: Rotate every month
- **Production**: Rotate every month

**Next Rotation Due**: [Date + 30 days]

**Last Rotated**: December 10, 2025
