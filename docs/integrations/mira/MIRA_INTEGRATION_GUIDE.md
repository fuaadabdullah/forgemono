# Mira Linker Integration - Configuration Guide

## 🔧 Jira Project Keys Configuration

### Overview
The Mira Linker integration supports configurable Jira project keys instead of being hardcoded to "PROJ". This allows you to match your actual Jira project structure.

### Quick Setup

1. **Configure Jira Keys:**

   ```bash
   ./configure_jira_keys.sh
   ```

2. **Or manually set GitHub variable:**
   - Go to Repository Settings → Variables
   - Add `JIRA_PROJECT_KEYS` with value like `(PROJ|GOB|INF)`

3. **Test configuration:**
   ```bash

   ./verify_mira_setup.sh
   ```

### Examples

#### Single Project Key
```
JIRA_PROJECT_KEYS: PROJ
Matches: PROJ-123, PROJ-456, PROJ-789
```

#### Multiple Project Keys
```
JIRA_PROJECT_KEYS: (PROJ|GOB|INF)
Matches: PROJ-123, GOB-456, INF-789
```

#### Complex Pattern
```
JIRA_PROJECT_KEYS: (PROJ|GOB|INF|DEVOPS|SEC)
Matches: PROJ-123, GOB-456, INF-789, DEVOPS-101, SEC-202
```

## 🔐 Security Best Practices

### Service Accounts & Authentication

#### GitHub Apps (Recommended)

- **Use GitHub Apps over Personal Access Tokens (PATs)** for better security
- **Least privilege**: Only grant necessary permissions
- **Organization-level secrets**: Store tokens in org-level secrets/contexts

#### CircleCI Contexts

- **Restrict access**: Limit who can access CircleCI contexts
- **SSH keys**: For Kamatera deploys, store SSH keys in CircleCI contexts
- **Rotate regularly**: Implement key rotation policies

### Token Management

#### Bitwarden Integration

- Store all API tokens in Bitwarden
- Use `bw` CLI for automated retrieval
- Never commit tokens to repository

#### Environment Variables

- Use repository variables for non-sensitive config
- Store secrets in GitHub Secrets or CircleCI contexts
- Implement token rotation policies

## 📋 CODEOWNERS vs Mira Auto-Assignment

### Understanding the Difference

#### CODEOWNERS

- **File-based assignment**: Assigns reviewers based on file paths
- **GitHub native**: Built into GitHub PR reviews
- **Static configuration**: Defined in `.github/CODEOWNERS` file

#### Mira Auto-Assignment

- **API-based assignment**: Uses Mira's intelligent assignment logic
- **Dynamic rules**: Can assign based on ticket type, component, etc.
- **Fallback support**: Uses CODEOWNERS as fallback when Mira can't determine assignee

### Configuration

```yaml
# mira-linker-config.yml
autoAssign:
  enabled: true
  fallback: "@fuaadabdullah"  # CODEOWNERS fallback
  method: CODEOWNERS_fallback
```

### Best Practices

1. **Keep CODEOWNERS simple**: Use for basic file-based ownership
2. **Let Mira handle complex logic**: Ticket type, component-based assignment
3. **Use fallback**: Ensure someone gets assigned even if Mira fails
4. **Regular review**: Audit CODEOWNERS and Mira assignment rules quarterly

## 🚀 Complete Setup Workflow

1. **Configure Jira Keys:**
   ```bash

   ./configure_jira_keys.sh
   ```

2. **Run Full Automation:**

   ```bash
   ./complete_mira_integration.sh
   ```

3. **Verify Setup:**
   ```bash

   ./verify_mira_setup.sh
   ```

4. **Test Integration:**
   - Create PR with valid Jira key (e.g., `PROJ-123: Fix bug`)
   - Verify workflow passes
   - Check Mira dashboard for ticket updates

## 🔍 Troubleshooting

### Common Issues

#### Jira Key Validation Failing

```bash
# Check configured keys
gh variable get JIRA_PROJECT_KEYS

# Test pattern manually
echo "PROJ-123" | grep -E "(PROJ|GOB|INF)-\d+"
```

#### Mira Auto-Assignment Not Working
- Check CODEOWNERS file exists
- Verify fallback user has repository access
- Review Mira dashboard for configuration errors

#### Webhook Issues
- Verify GitHub token has `repo` and `admin:repo_hook` scopes
- Check webhook delivery in repository settings
- Ensure Mira API key is valid

### Support

- **Mira Documentation**: https://docs.mira.tools
- **GitHub Actions**: Check workflow run logs
- **CircleCI**: Review context and secret configuration

---

**Last Updated**: December 9, 2025
**Version**: 2.0