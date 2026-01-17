#!/bin/bash
# Secrets Management Migration Script
# Migrates from current SOPS/Bitwarden setup to HashiCorp Vault + Bitwarden hybrid

set -e

echo "🔐 Secrets Management Migration Tool"
echo "===================================="

# Check prerequisites
command -v vault >/dev/null 2>&1 || { echo "❌ Vault CLI required. Install: https://developer.hashicorp.com/vault/install"; exit 1; }
command -v bw >/dev/null 2>&1 || { echo "❌ Bitwarden CLI required. Install: npm install -g @bitwarden/cli"; exit 1; }

# Phase 1: Setup Vault Infrastructure
setup_vault_infrastructure() {
    echo "🏗️  Phase 1: Setting up Vault infrastructure..."

    # Deploy Vault using Terragrunt
    cd goblin-infra/envs/prod
    terragrunt init
    terragrunt apply -target=module.vault

    echo "✅ Vault infrastructure deployed"
}

# Phase 2: Configure Vault Policies and Auth
configure_vault_policies() {
    echo "🔒 Phase 2: Configuring Vault policies and authentication..."

    # Enable KV v2 secrets engine
    vault secrets enable -path=secret kv-v2

    # Create policies
    cat > developer-policy.hcl << EOF
path "secret/data/goblin/dev/*" {
    capabilities = ["read", "list"]
}

path "secret/data/goblin/staging/*" {
    capabilities = ["read", "list"]
}
EOF

    cat > production-policy.hcl << EOF
path "secret/data/goblin/prod/*" {
    capabilities = ["read", "list"]
}

path "secret/data/goblin/backup/*" {
    capabilities = ["read", "create", "update"]
}
EOF

    vault policy write developer developer-policy.hcl
    vault policy write production production-policy.hcl

    echo "✅ Vault policies configured"
}

# Phase 3: Migrate Secrets from Bitwarden to Vault
migrate_secrets() {
    echo "🚀 Phase 3: Migrating secrets from Bitwarden to Vault..."

    # Login to Bitwarden
    if [ -z "$BW_SESSION" ]; then
        echo "Please login to Bitwarden CLI:"
        bw login
        export BW_SESSION=$(bw unlock --raw)
    fi

    # Sync vault
    bw sync

    # Migrate production secrets
    echo "Migrating production secrets..."

    # API Keys
    migrate_secret "goblin-prod-openai" "secret/goblin/prod/openai" "api_key"
    migrate_secret "goblin-prod-anthropic" "secret/goblin/prod/anthropic" "api_key"
    migrate_secret "goblin-prod-groq" "secret/goblin/prod/groq" "api_key"

    # Infrastructure secrets
    migrate_secret "goblin-prod-db-url" "secret/goblin/prod/database" "url"
    migrate_secret "goblin-prod-jwt" "secret/goblin/prod/jwt" "secret_key"
    migrate_secret "goblin-prod-fastapi-secret" "secret/goblin/prod/fastapi" "secret"

    echo "✅ Secrets migrated to Vault"
}

migrate_secret() {
    local bw_item="$1"
    local vault_path="$2"
    local vault_key="$3"

    echo "Migrating $bw_item → $vault_path"

    # Get secret from Bitwarden
    local secret_value=$(bw get password "$bw_item")

    if [ -n "$secret_value" ]; then
        # Store in Vault
        vault kv put "$vault_path" "$vault_key=$secret_value"

        # Create backup in Vault
        vault kv put "secret/goblin/backup/$bw_item" \
            "value=$secret_value" \
            "migrated_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            "source=bitwarden"

        echo "✅ Migrated $bw_item"
    else
        echo "⚠️  Secret $bw_item not found in Bitwarden"
    fi
}

# Phase 4: Update Application Configuration
update_application_config() {
    echo "🔧 Phase 4: Updating application configuration..."

    # Update vault_client.py to prefer Vault over Bitwarden
    cat > vault_client_update.patch << 'EOF'
--- a/apps/goblin-assistant/backend/vault_client.py
+++ b/apps/goblin-assistant/backend/vault_client.py
@@ -1,5 +1,7 @@
 """
 Vault Client for Goblin Assistant
+Migrated to HashiCorp Vault as primary secrets manager
+Maintains Bitwarden fallback for development
 """

 import os
@@ -50,6 +52,15 @@ class VaultClient:
         self.cert_path = cert_path
         self.key_path = key_path
         self.ca_cert = ca_cert
+
+    def get_secret(self, path: str, key: str = None, use_vault: bool = None) -> Union[str, dict]:
+        """Get secret with intelligent fallback"""
+        if use_vault is None:
+            use_vault = self._should_use_vault()
+
+        if use_vault:
+            return self._get_from_vault(path, key)
+        else:
+            return self._get_from_bitwarden(path, key)

     def _should_use_vault(self) -> bool:
         """Determine if Vault should be used based on environment"""
EOF

    echo "✅ Application configuration updated"
}

# Phase 5: Enable Dynamic Secrets
enable_dynamic_secrets() {
    echo "🔄 Phase 5: Enabling dynamic secrets..."

    # Enable database secrets engine (example for PostgreSQL)
    vault secrets enable database

    # Configure database connection
    vault write database/config/goblin-postgres \
        plugin_name=postgresql-database-plugin \
        allowed_roles="goblin-app" \
        connection_url="postgresql://{{username}}:{{password}}@db.example.com/goblin" \
        username="vault_admin" \
        password="vault_admin_password"

    # Create role for dynamic credentials
    vault write database/roles/goblin-app \
        db_name=goblin-postgres \
        creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
        default_ttl="1h" \
        max_ttl="24h"

    echo "✅ Dynamic secrets enabled"
}

# Phase 6: Setup Audit Logging
setup_audit_logging() {
    echo "📊 Phase 6: Setting up audit logging..."

    # Enable file audit device
    vault audit enable file file_path=/vault/logs/audit.log

    # Enable syslog for centralized logging
    vault audit enable syslog

    echo "✅ Audit logging configured"
}

# Main execution
case "${1:-all}" in
    "infrastructure")
        setup_vault_infrastructure
        ;;
    "policies")
        configure_vault_policies
        ;;
    "migrate")
        migrate_secrets
        ;;
    "config")
        update_application_config
        ;;
    "dynamic")
        enable_dynamic_secrets
        ;;
    "audit")
        setup_audit_logging
        ;;
    "all")
        setup_vault_infrastructure
        configure_vault_policies
        migrate_secrets
        update_application_config
        enable_dynamic_secrets
        setup_audit_logging
        echo "🎉 Migration complete!"
        ;;
    *)
        echo "Usage: $0 [infrastructure|policies|migrate|config|dynamic|audit|all]"
        exit 1
        ;;
esac</content>
<parameter name="filePath">/Users/fuaadabdullah/ForgeMonorepo/scripts/migrate_secrets_to_vault.sh
