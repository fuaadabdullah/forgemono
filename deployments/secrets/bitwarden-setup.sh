#!/bin/bash
# Project: Goblin Assistant
# Script: bitwarden-setup.sh
# Purpose: Setup Bitwarden CLI for secrets management
# Date: 2025-12-18
# Maintainer: fuaadabdullah

set -e

echo "🔐 Setting up Bitwarden CLI for Secrets Management"
echo "================================================"

# Install Bitwarden CLI
echo "📦 Installing Bitwarden CLI..."
if ! command -v bw &> /dev/null; then
    curl -L "https://github.com/bitwarden/clients/releases/download/cli-v2024.7.1/bw-linux-x64-v2024.7.1.zip" -o bw.zip
    unzip bw.zip
    chmod +x bw
    sudo mv bw /usr/local/bin/
    rm bw.zip
else
    echo "✅ Bitwarden CLI already installed"
fi

# Install jq for JSON processing
echo "📦 Installing jq..."
if ! command -v jq &> /dev/null; then
    sudo apt update && sudo apt install -y jq
else
    echo "✅ jq already installed"
fi

# Create Bitwarden configuration directory
mkdir -p /opt/goblin-secrets

# Create Bitwarden login script
echo "🔑 Creating Bitwarden login script..."
cat > /opt/goblin-secrets/bitwarden-login.sh << 'EOF'
#!/bin/bash
# Bitwarden login and configuration

echo "🔐 Bitwarden Login"
echo "================="
echo
echo "Please log in to Bitwarden:"
bw login

echo
echo "🔑 Setting up unlock mechanism..."
echo "Please enter your Bitwarden password when prompted:"
UNLOCK_PASSWORD=$(read -s -p "Password: " && echo $REPLY)
echo
echo "🔧 Configuring unlock..."

# Create unlock script
cat > /opt/goblin-secrets/unlock.sh << 'UNLOCK_SCRIPT'
#!/bin/bash
# Unlock Bitwarden vault

UNLOCK_PASSWORD_FILE="/opt/goblin-secrets/.unlock_password"

if [ ! -f "$UNLOCK_PASSWORD_FILE" ]; then
    echo "🔐 Setting up unlock password..."
    read -s -p "Enter your Bitwarden password: " UNLOCK_PASSWORD
    echo "$UNLOCK_PASSWORD" > "$UNLOCK_PASSWORD_FILE"
    chmod 600 "$UNLOCK_PASSWORD_FILE"
fi

UNLOCK_PASSWORD=$(cat "$UNLOCK_PASSWORD_FILE")
echo "$UNLOCK_PASSWORD" | bw unlock --passwordfile /dev/stdin

echo "✅ Bitwarden unlocked"
echo "Session token: $BW_SESSION"
UNLOCK_SCRIPT

chmod +x /opt/goblin-secrets/unlock.sh

# Create secrets management functions
echo "📝 Creating secrets management functions..."
cat > /opt/goblin-secrets/secrets-manager.sh << 'EOF'
#!/bin/bash
# Bitwarden secrets management for Goblin Assistant

VAULT_NAME="Goblin Assistant"
SECRETS_DIR="/opt/goblin-secrets"

# Check if Bitwarden is unlocked
check_bitwarden() {
    if [ -z "$BW_SESSION" ]; then
        echo "❌ Bitwarden is not unlocked. Run: /opt/goblin-secrets/unlock.sh"
        return 1
    fi
    return 0
}

# Get a secret from Bitwarden
get_secret() {
    local secret_name="$1"
    local field="${2:-password}"
    
    check_bitwarden || return 1
    
    echo "🔍 Getting secret: $secret_name"
    bw get item "$secret_name" --session "$BW_SESSION" | jq -r ".fields[] | select(.name == \"$field\") | .value"
}

# Set a secret in Bitwarden
set_secret() {
    local secret_name="$1"
    local value="$2"
    local field="${3:-password}"
    
    check_bitwarden || return 1
    
    echo "💾 Setting secret: $secret_name"
    
    # Check if item exists
    if bw get item "$secret_name" --session "$BW_SESSION" > /dev/null 2>&1; then
        # Update existing item
        bw get item "$secret_name" --session "$BW_SESSION" | jq --arg field "$field" --arg value "$value" '.fields[] | select(.name == $field) | .value = $value' | bw edit item "$secret_name" --session "$BW_SESSION"
    else
        # Create new item
        bw create item --session "$BW_SESSION" << ITEM
{
  "organizationId": null,
  "collectionIds": [],
  "folderId": null,
  "type": 1,
  "name": "$secret_name",
  "notes": "Goblin Assistant secret",
  "fields": [
    {
      "name": "$field",
      "value": "$value",
      "type": 0
    }
  ],
  "login": null,
  "card": null,
  "identity": null,
  "secureNote": {
    "type": 0
  }
}
ITEM
    fi
    echo "✅ Secret saved"
}

# Sync secrets to environment file
sync_secrets() {
    check_bitwarden || return 1
    
    echo "🔄 Syncing secrets to environment file..."
    
    # Create/update .env file
    cat > /opt/goblin-secrets/.env << ENV
# Goblin Assistant Secrets - Generated $(date)
# DO NOT COMMIT THIS FILE

ENV
    
    # Sync specific secrets
    local secrets=(
        "KAMATERA_API_KEY:Kamatera API Key"
        "CLOUDFLARE_API_TOKEN:Cloudflare API Token"
        "CLOUDFLARE_ZONE_ID:Cloudflare Zone ID"
        "CLOUDFLARE_ACCOUNT_ID:Cloudflare Account ID"
        "DATABASE_URL:Database URL"
        "JWT_SECRET_KEY:JWT Secret"
        "REDIS_URL:Redis URL"
        "GCS_BUCKET_NAME:GCS Bucket Name"
        "GCS_PROJECT_ID:GCS Project ID"
        "ANTHROPIC_API_KEY:Anthropic API Key"
        "OPENAI_API_KEY:OpenAI API Key"
        "GOOGLE_CLIENT_ID:Google Client ID"
        "GOOGLE_CLIENT_SECRET:Google Client Secret"
        "SUPABASE_URL:Supabase URL"
        "SUPABASE_ANON_KEY:Supabase Anon Key"
        "SUPABASE_SERVICE_ROLE_KEY:Supabase Service Role Key"
    )
    
    for secret_info in "${secrets[@]}"; do
        IFS=':' read -r secret_name display_name <<< "$secret_info"
        echo "Processing: $display_name"
        
        # Try to get secret from Bitwarden
        secret_value=$(get_secret "$display_name" 2>/dev/null || echo "")
        
        if [ -n "$secret_value" ]; then
            echo "$secret_name=$secret_value" >> /opt/goblin-secrets/.env
            echo "✅ $display_name"
        else
            echo "⚠️ $display_name not found in Bitwarden"
        fi
    done
    
    chmod 600 /opt/goblin-secrets/.env
    echo "✅ Secrets synced to /opt/goblin-secrets/.env"
}

# Import secrets from existing .env file
import_secrets() {
    local env_file="$1"
    
    if [ ! -f "$env_file" ]; then
        echo "❌ Environment file not found: $env_file"
        return 1
    fi
    
    echo "📥 Importing secrets from: $env_file"
    
    # Source the file to get variables
    set -a
    source "$env_file"
    set +a
    
    # Import each secret to Bitwarden
    local secrets=(
        "KAMATERA_API_KEY:Kamatera API Key"
        "CLOUDFLARE_API_TOKEN:Cloudflare API Token"
        "CLOUDFLARE_ZONE_ID:Cloudflare Zone ID"
        "CLOUDFLARE_ACCOUNT_ID:Cloudflare Account ID"
        "DATABASE_URL:Database URL"
        "JWT_SECRET_KEY:JWT Secret"
        "REDIS_URL:Redis URL"
        "GCS_BUCKET_NAME:GCS Bucket Name"
        "GCS_PROJECT_ID:GCS Project ID"
        "ANTHROPIC_API_KEY:Anthropic API Key"
        "OPENAI_API_KEY:OpenAI API Key"
        "GOOGLE_CLIENT_ID:Google Client ID"
        "GOOGLE_CLIENT_SECRET:Google Client Secret"
        "SUPABASE_URL:Supabase URL"
        "SUPABASE_ANON_KEY:Supabase Anon Key"
        "SUPABASE_SERVICE_ROLE_KEY:Supabase Service Role Key"
    )
    
    for secret_info in "${secrets[@]}"; do
        IFS=':' read -r var_name display_name <<< "$secret_info"
        
        if [ -n "${!var_name}" ]; then
            set_secret "$display_name" "${!var_name}"
        fi
    done
    
    echo "✅ Secrets imported to Bitwarden"
}

# Export secrets for deployment
export_secrets() {
    check_bitwarden || return 1
    
    local output_file="${1:-/tmp/goblin-secrets-export.json}"
    
    echo "📤 Exporting secrets to: $output_file"
    
    # Get all items from vault
    bw list items --session "$BW_SESSION" | jq -r '.[] | select(.name | contains("Goblin Assistant")) | {name: .name, fields: .fields}' > "$output_file"
    
    echo "✅ Secrets exported"
}

# Rotate a secret
rotate_secret() {
    local secret_name="$1"
    local new_value="$2"
    
    check_bitwarden || return 1
    
    echo "🔄 Rotating secret: $secret_name"
    set_secret "$secret_name" "$new_value"
    echo "✅ Secret rotated"
}

# List all secrets
list_secrets() {
    check_bitwarden || return 1
    
    echo "📋 Available secrets in Bitwarden:"
    bw list items --session "$BW_SESSION" | jq -r '.[] | select(.name | contains("Goblin Assistant")) | "• " + .name'
}

# Main command handler
case "$1" in
    unlock)
        /opt/goblin-secrets/unlock.sh
        ;;
    get)
        get_secret "$2" "${3:-password}"
        ;;
    set)
        set_secret "$2" "$3" "${4:-password}"
        ;;
    sync)
        sync_secrets
        ;;
    import)
        import_secrets "$2"
        ;;
    export)
        export_secrets "$2"
        ;;
    rotate)
        rotate_secret "$2" "$3"
        ;;
    list)
        list_secrets
        ;;
    *)
        echo "Usage: $0 {unlock|get|set|sync|import|export|rotate|list}"
        echo
        echo "Commands:"
        echo "  unlock    - Unlock Bitwarden vault"
        echo "  get NAME  - Get a secret by name"
        echo "  set NAME VALUE - Set a secret"
        echo "  sync      - Sync secrets from Bitwarden to .env"
        echo "  import FILE - Import secrets from .env file"
        echo "  export FILE - Export secrets to JSON file"
        echo "  rotate NAME VALUE - Rotate a secret"
        echo "  list      - List all Goblin Assistant secrets"
        exit 1
        ;;
esac
EOF

chmod +x /opt/goblin-secrets/secrets-manager.sh

# Create Fly.io secrets sync script
echo "🚀 Creating Fly.io secrets sync..."
cat > /opt/goblin-secrets/sync-fly-secrets.sh << 'EOF'
#!/bin/bash
# Sync secrets to Fly.io

check_bitwarden || exit 1

echo "🚀 Syncing secrets to Fly.io..."

# Get required secrets
KAMATERA_API_KEY=$(get_secret "Kamatera API Key")
CLOUDFLARE_API_TOKEN=$(get_secret "Cloudflare API Token")
CLOUDFLARE_ZONE_ID=$(get_secret "Cloudflare Zone ID")
CLOUDFLARE_ACCOUNT_ID=$(get_secret "Cloudflare Account ID")
DATABASE_URL=$(get_secret "Database URL")
JWT_SECRET_KEY=$(get_secret "JWT Secret")
REDIS_URL=$(get_secret "Redis URL")
GCS_BUCKET_NAME=$(get_secret "GCS Bucket Name")
GCS_PROJECT_ID=$(get_secret "GCS Project ID")

# Set Fly.io secrets
fly secrets set KAMATERA_API_KEY="$KAMATERA_API_KEY" \
    CLOUDFLARE_API_TOKEN="$CLOUDFLARE_API_TOKEN" \
    CLOUDFLARE_ZONE_ID="$CLOUDFLARE_ZONE_ID" \
    CLOUDFLARE_ACCOUNT_ID="$CLOUDFLARE_ACCOUNT_ID" \
    DATABASE_URL="$DATABASE_URL" \
    JWT_SECRET_KEY="$JWT_SECRET_KEY" \
    REDIS_URL="$REDIS_URL" \
    GCS_BUCKET_NAME="$GCS_BUCKET_NAME" \
    GCS_PROJECT_ID="$GCS_PROJECT_ID"

echo "✅ Secrets synced to Fly.io"
EOF

chmod +x /opt/goblin-secrets/sync-fly-secrets.sh

# Create system integration script
echo "🔧 Creating system integration..."
cat > /opt/goblin-secrets/system-integration.sh << 'EOF'
#!/bin/bash
# Integrate Bitwarden with system services

# Add secrets manager to PATH
echo 'export PATH="$PATH:/opt/goblin-secrets"' >> ~/.bashrc

# Create systemd service for automatic unlock (optional)
echo "🔧 Creating automatic unlock service (optional)..."

cat > /etc/systemd/system/bitwarden-unlock.service << 'UNLOCK_SERVICE'
[Unit]
Description=Bitwarden Auto Unlock
After=network.target

[Service]
Type=oneshot
User=root
ExecStart=/opt/goblin-secrets/unlock.sh
StandardOutput=append:/var/log/bitwarden-unlock.log
StandardError=append:/var/log/bitwarden-unlock.log

[Install]
WantedBy=multi-user.target
UNLOCK_SERVICE

# Create timer for periodic unlock
cat > /etc/systemd/system/bitwarden-unlock.timer << 'UNLOCK_TIMER'
[Unit]
Description=Bitwarden Auto Unlock Timer
Requires=bitwarden-unlock.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
UNLOCK_TIMER

echo "✅ System integration complete"
echo "💡 To enable auto-unlock: systemctl enable bitwarden-unlock.timer"
EOF

chmod +x /opt/goblin-secrets/system-integration.sh

# Create secrets validation script
echo "✅ Creating secrets validation..."
cat > /opt/goblin-secrets/validate-secrets.sh << 'EOF'
#!/bin/bash
# Validate that all required secrets are available

REQUIRED_SECRETS=(
    "KAMATERA_API_KEY"
    "CLOUDFLARE_API_TOKEN"
    "CLOUDFLARE_ZONE_ID"
    "DATABASE_URL"
    "JWT_SECRET_KEY"
)

echo "🔍 Validating secrets..."

check_bitwarden || exit 1

missing_secrets=()
for secret in "${REQUIRED_SECRETS[@]}"; do
    if ! get_secret "$secret" > /dev/null 2>&1; then
        missing_secrets+=("$secret")
        echo "❌ Missing: $secret"
    else
        echo "✅ Found: $secret"
    fi
done

if [ ${#missing_secrets[@]} -eq 0 ]; then
    echo "🎉 All required secrets are available!"
    exit 0
else
    echo "⚠️ Missing secrets: ${missing_secrets[*]}"
    echo "💡 Add missing secrets using: /opt/goblin-secrets/secrets-manager.sh set"
    exit 1
fi
EOF

chmod +x /opt/goblin-secrets/validate-secrets.sh

# Create backup script
echo "💾 Creating secrets backup..."
cat > /opt/goblin-secrets/backup-secrets.sh << 'EOF'
#!/bin/bash
# Backup secrets to encrypted file

check_bitwarden || exit 1

BACKUP_FILE="/opt/goblin-secrets/backup-$(date +%Y%m%d-%H%M%S).json.enc"

echo "💾 Creating secrets backup: $BACKUP_FILE"

# Export and encrypt
bw export --format json --session "$BW_SESSION" | gpg --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 --s2k-digest-algo SHA512 --s2k-count 65536 --force-mdc --quiet --no-greeting --batch --yes --passphrase "$UNLOCK_PASSWORD" --symmetric --output "$BACKUP_FILE"

echo "✅ Backup created: $BACKUP_FILE"

# Cleanup old backups (keep last 7)
find /opt/goblin-secrets -name "backup-*.json.enc" -type f -mtime +7 -delete

echo "🧹 Old backups cleaned up"
EOF

chmod +x /opt/goblin-secrets/backup-secrets.sh

# Setup cron jobs
echo "⏰ Setting up cron jobs..."
echo "0 2 * * * root /opt/goblin-secrets/backup-secrets.sh" >> /etc/crontab
echo "0 */6 * * * root /opt/goblin-secrets/validate-secrets.sh" >> /etc/crontab

# Final setup summary
echo
echo "🎉 Bitwarden Setup Complete!"
echo "==========================="
echo
echo "✅ Bitwarden CLI installed"
echo "✅ Secrets manager created"
echo "✅ Fly.io integration ready"
echo "✅ System integration configured"
echo "✅ Validation and backup scripts created"
echo "✅ Cron jobs scheduled"
echo
echo "📋 Next Steps:"
echo "1. Login to Bitwarden: /opt/goblin-secrets/bitwarden-login.sh"
echo "2. Unlock vault: /opt/goblin-secrets/secrets-manager.sh unlock"
echo "3. Import existing secrets: /opt/goblin-secrets/secrets-manager.sh import /path/to/.env"
echo "4. Sync to Fly.io: /opt/g
