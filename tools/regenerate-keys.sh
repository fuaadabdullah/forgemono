#!/bin/bash
# Goblin Assistant - Key Regeneration Script
# Updates Bitwarden vault with new regenerated keys after security incident
# Usage: ./regenerate-keys.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to prompt for secret input
prompt_secret() {
    local service_name="$1"
    local description="$2"
    local secret_value=""

    echo ""
    log_info "Enter new $service_name API key:"
    echo "$description"
    echo "(Press Enter when done, or Ctrl+C to cancel)"
    read -s secret_value

    if [ -z "$secret_value" ]; then
        log_warning "No value entered for $service_name, skipping..."
        return 1
    fi

    echo "$secret_value"
}

# Function to add secret to Bitwarden
add_secret() {
    local secret_name="$1"
    local secret_value="$2"
    local notes="$3"

    log_info "Adding $secret_name to Bitwarden..."

    # Use the secrets.sh tool to add the secret
    "$SCRIPT_DIR/secrets.sh" set "$secret_name" "$secret_value" "$notes"

    if [ $? -eq 0 ]; then
        log_success "$secret_name added successfully"
    else
        log_error "Failed to add $secret_name"
        return 1
    fi
}

# Main regeneration function
regenerate_keys() {
    echo "🔐 Goblin Assistant - Key Regeneration Tool"
    echo "=========================================="
    log_warning "This tool will help you update compromised API keys in Bitwarden"
    log_warning "Make sure you have regenerated these keys from their respective provider dashboards first!"
    echo ""

    # OpenAI API Key
    openai_key=$(prompt_secret "OpenAI" "Get from: https://platform.openai.com/api-keys")
    if [ $? -eq 0 ] && [ -n "$openai_key" ]; then
        add_secret "goblin-assistant-openai" "$openai_key" "OpenAI API Key for Goblin Assistant - Regenerated $(date)"
    fi

    # Anthropic API Key
    anthropic_key=$(prompt_secret "Anthropic" "Get from: https://console.anthropic.com/settings/keys")
    if [ $? -eq 0 ] && [ -n "$anthropic_key" ]; then
        add_secret "goblin-assistant-anthropic" "$anthropic_key" "Anthropic API Key for Goblin Assistant - Regenerated $(date)"
    fi

    # DeepSeek API Key
    deepseek_key=$(prompt_secret "DeepSeek" "Get from: https://platform.deepseek.com/api-keys")
    if [ $? -eq 0 ] && [ -n "$deepseek_key" ]; then
        add_secret "goblin-assistant-deepseek" "$deepseek_key" "DeepSeek API Key for Goblin Assistant - Regenerated $(date)"
    fi

    # Gemini API Key
    gemini_key=$(prompt_secret "Gemini" "Get from: https://makersuite.google.com/app/apikey")
    if [ $? -eq 0 ] && [ -n "$gemini_key" ]; then
        add_secret "goblin-assistant-gemini" "$gemini_key" "Gemini API Key for Goblin Assistant - Regenerated $(date)"
    fi

    # Grok API Key
    grok_key=$(prompt_secret "Grok" "Get from: https://console.x.ai/")
    if [ $? -eq 0 ] && [ -n "$grok_key" ]; then
        add_secret "goblin-assistant-grok" "$grok_key" "Grok API Key for Goblin Assistant - Regenerated $(date)"
    fi

    # Supabase Service Role Key
    supabase_service_key=$(prompt_secret "Supabase Service Role" "Get from: https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api")
    if [ $? -eq 0 ] && [ -n "$supabase_service_key" ]; then
        add_secret "goblin-assistant-supabase-service-role" "$supabase_service_key" "Supabase Service Role Key for Goblin Assistant - Regenerated $(date)"
    fi

    # JWT Secret
    jwt_secret=$(prompt_secret "JWT Secret" "Generate a new secure random string (256-bit recommended)")
    if [ $? -eq 0 ] && [ -n "$jwt_secret" ]; then
        add_secret "goblin-assistant-jwt-secret" "$jwt_secret" "JWT Secret Key for Goblin Assistant authentication - Regenerated $(date)"
    fi

    # Google OAuth Client ID
    google_client_id=$(prompt_secret "Google OAuth Client ID" "Get from: https://console.cloud.google.com/apis/credentials")
    if [ $? -eq 0 ] && [ -n "$google_client_id" ]; then
        add_secret "goblin-assistant-google-oauth-client-id" "$google_client_id" "Google OAuth Client ID for Goblin Assistant - Regenerated $(date)"
    fi

    # Google OAuth Client Secret
    google_client_secret=$(prompt_secret "Google OAuth Client Secret" "Get from: https://console.cloud.google.com/apis/credentials")
    if [ $? -eq 0 ] && [ -n "$google_client_secret" ]; then
        add_secret "goblin-assistant-google-oauth-client-secret" "$google_client_secret" "Google OAuth Client Secret for Goblin Assistant - Regenerated $(date)"
    fi

    echo ""
    log_success "Key regeneration complete!"
    log_info "Run './tools/secrets.sh list' to verify all keys were added"
    log_info "Test your deployments to ensure the new keys work correctly"
}

# Check if Bitwarden CLI is available
check_dependencies() {
    if ! command -v bw &> /dev/null; then
        log_error "Bitwarden CLI not found. Please install it first:"
        echo "npm install -g @bitwarden/cli"
        exit 1
    fi
}

# Main execution
main() {
    check_dependencies
    regenerate_keys
}

main "$@"
