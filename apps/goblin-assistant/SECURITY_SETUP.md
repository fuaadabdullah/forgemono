# Goblin Assistant - Security & Secrets Management

## 🔐 Security Overview

All application secrets have been migrated from plain text environment files to secure storage in Bitwarden. This ensures compliance with security best practices and prevents accidental exposure of sensitive credentials.

## 📁 Vault Structure

The Bitwarden vault is organized into the following collections:

### Goblin Assistant/Supabase
- **Supabase URL**: `https://dhxoowakvmobjxsffpst.supabase.co`
- **Supabase Anon Key**: Public anonymous access key
- **Supabase Service Role Key**: Admin service role key (server-side only)
- **Database URL**: PostgreSQL connection string

### Goblin Assistant/Google OAuth
- **Google Client ID**: OAuth 2.0 client identifier
- **Google Client Secret**: OAuth 2.0 client secret

### Goblin Assistant/JWT Secrets
- **JWT Secret Key**: Primary JWT signing key
- **JWT Standby Key**: Backup JWT signing key
- **JWT Current Key**: Currently active JWT key

### Goblin Assistant/AI Providers
- **OpenAI API Key**: OpenAI service access
- **Anthropic API Key**: Anthropic Claude access
- **DeepSeek API Key**: DeepSeek AI access
- **Google Gemini API Key**: Google Gemini access
- **xAI Grok API Key**: xAI Grok access
- **SiliconFlow API Key**: SiliconFlow access
- **Moonshot API Key**: Moonshot AI access
- **ElevenLabs API Key**: Text-to-speech service

### Goblin Assistant/Infrastructure
- **Sentry Admin Token**: Error monitoring admin access
- **Kamatera Host**: Local LLM server IP
- **Kamatera LLM URL**: Local LLM API endpoint
- **Kamatera LLM API Key**: Local LLM authentication

## 🚀 Deployment Process

### Prerequisites

1. **Bitwarden CLI**: Install via `brew install bitwarden-cli`
2. **Login to Bitwarden**: Run `bw login`
3. **Unlock Vault**: Run `bw unlock` (for CLI operations)

### Secure Deployment Script

Use the provided `deploy-with-bitwarden.sh` script for secure deployments:

```bash
# Make script executable (one-time)
chmod +x deploy-with-bitwarden.sh

# Run secure deployment
./deploy-with-bitwarden.sh
```

This script will:
1. Verify Bitwarden CLI installation and login
2. Unlock the vault securely
3. Fetch all required secrets
4. Create temporary environment files
5. Deploy frontend (Vercel) and backend (Fly.io)
6. Clean up temporary files
7. Lock the vault

## 🔧 Manual Setup

If you need to set up secrets manually:

1. **Install Bitwarden CLI**:
   ```bash
   brew install bitwarden-cli
   ```

2. **Login and Setup Vault**:
   ```bash
   bw login
   ./setup-bitwarden-secrets.sh
   ```

3. **Follow the prompts** to create all required vault items.

## 📋 Environment Files

### Frontend (.env.production)
Contains only non-sensitive configuration with Bitwarden references:

```bash
# Goblin Assistant Frontend Configuration
# Secrets are stored securely in Bitwarden vault
# Retrieve secrets using: bw get item "Item Name"

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=<retrieve from Bitwarden: "Supabase URL">
NEXT_PUBLIC_SUPABASE_ANON_KEY=<retrieve from Bitwarden: "Supabase Anon Key">

# Google OAuth
GOOGLE_CLIENT_ID=<retrieve from Bitwarden: "Google Client ID">
GOOGLE_CLIENT_SECRET=<retrieve from Bitwarden: "Google Client Secret">

# AI Provider Keys
OPENAI_API_KEY=<retrieve from Bitwarden: "OpenAI API Key">
ANTHROPIC_API_KEY=<retrieve from Bitwarden: "Anthropic API Key">
# ... (other AI keys)

# Infrastructure
SENTRY_ADMIN_TOKEN=<retrieve from Bitwarden: "Sentry Admin Token">
KAMATERA_HOST=<retrieve from Bitwarden: "Kamatera Host">
KAMATERA_LLM_URL=<retrieve from Bitwarden: "Kamatera LLM URL">
KAMATERA_LLM_API_KEY=<retrieve from Bitwarden: "Kamatera LLM API Key">
```

### Backend (.env)
Contains server-side secrets with Bitwarden references:

```bash
# Goblin Assistant Backend Configuration
# Secrets are stored securely in Bitwarden vault

# Supabase (Server-side)
SUPABASE_URL=<retrieve from Bitwarden: "Supabase URL">
SUPABASE_SERVICE_ROLE_KEY=<retrieve from Bitwarden: "Supabase Service Role Key">
DATABASE_URL=<retrieve from Bitwarden: "Database URL">

# JWT Secrets
JWT_SECRET_KEY=<retrieve from Bitwarden: "JWT Secret Key">
JWT_STANDBY_KEY=<retrieve from Bitwarden: "JWT Standby Key">
JWT_CURRENT_KEY=<retrieve from Bitwarden: "JWT Current Key">

# AI Provider Keys (all)
# ... (same as frontend)

# Infrastructure
SENTRY_ADMIN_TOKEN=<retrieve from Bitwarden: "Sentry Admin Token">
KAMATERA_HOST=<retrieve from Bitwarden: "Kamatera Host">
KAMATERA_LLM_URL=<retrieve from Bitwarden: "Kamatera LLM URL">
KAMATERA_LLM_API_KEY=<retrieve from Bitwarden: "Kamatera LLM API Key">
```

## 🔒 Security Best Practices

### Secret Management
- ✅ **Never commit secrets** to version control
- ✅ **Use Bitwarden** for all credential storage
- ✅ **Rotate keys regularly** (recommended: quarterly)
- ✅ **Use different keys** for different environments
- ✅ **Monitor access logs** for unauthorized activity

### Deployment Security
- 🔐 **Vault remains locked** except during deployment
- 🧹 **Temporary files cleaned up** after deployment
- 🚫 **No secrets in build artifacts** or containers
- ✅ **Environment variables** used at runtime only

### Access Control
- 👥 **Limit vault access** to authorized team members
- 🔑 **Use strong master password** and 2FA
- 📊 **Audit vault access** regularly
- 🚨 **Monitor for suspicious activity**

## 🧪 Testing Deployment

After deployment, verify functionality:

1. **Frontend**: Visit https://goblin.fuaad.ai
2. **API**: Test endpoints at https://api.goblin.fuaad.ai
3. **Authentication**: Verify Google OAuth login
4. **AI Features**: Test chat and AI functionality
5. **Admin Panel**: Access https://ops.goblin.fuaad.ai

## 🆘 Troubleshooting

### Common Issues

**Bitwarden CLI not found**:
```bash
brew install bitwarden-cli
```

**Login failed**:
```bash
bw login
```

**Vault unlock failed**:
```bash
bw unlock
```

**Secret not found**:
- Verify item name in Bitwarden vault
- Check collection organization
- Run `./setup-bitwarden-secrets.sh` to recreate structure

**Deployment failed**:
- Check Vercel/Fly.io credentials
- Verify all secrets are accessible
- Check deployment logs

## 📚 Additional Resources

- [Bitwarden CLI Documentation](https://bitwarden.com/help/cli/)
- [Vercel Deployment Guide](https://vercel.com/docs)
- [Fly.io Deployment Guide](https://fly.io/docs)
- [Supabase Security](https://supabase.com/docs/guides/security)
- [OAuth 2.0 Best Practices](https://tools.ietf.org/html/rfc6749)

## 🔄 Migration Complete

✅ **All secrets migrated** from plain text to Bitwarden
✅ **Environment files secured** with vault references
✅ **Deployment scripts updated** for secure operations
✅ **Backup files created** for safety
✅ **Documentation provided** for team reference

**Next Steps**:
1. Test the deployment process
2. Remove `.env.backup.*` files after verification
3. Set up automated secret rotation
4. Implement vault access monitoring
5. Train team on secure practices
