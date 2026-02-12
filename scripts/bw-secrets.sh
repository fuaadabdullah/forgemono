#!/bin/bash
# Bitwarden Secrets Management Script for ForgeMonorepo
# This script helps manage secrets using Bitwarden CLI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Bitwarden CLI is installed
check_bw_cli() {
    if ! command -v bw &> /dev/null; then
        print_error "Bitwarden CLI is not installed. Install it first:"
        echo "  brew install bitwarden-cli"
        exit 1
    fi
}

# Check if vault is unlocked
check_vault_status() {
    if ! bw status | grep -q "unlocked"; then
        print_warning "Bitwarden vault is locked. Please unlock it first:"
        echo "  bw unlock"
        exit 1
    fi
}

# Get a secret from Bitwarden
get_secret() {
    local secret_name=$1
    local secret_value

    if ! secret_value=$(bw get password "$secret_name" 2>/dev/null); then
        print_error "Failed to get secret: $secret_name"
        print_info "Make sure the secret exists in your Bitwarden vault"
        return 1
    fi

    echo "$secret_value"
}

# Export secrets to environment variables
export_secrets() {
    print_info "Exporting secrets to environment variables..."

    # LLM API Keys
    export KAMATERA_LLM_API_KEY="$(get_secret "KAMATERA_LLM_API_KEY")" && print_success "KAMATERA_LLM_API_KEY exported"
    export LOCAL_LLM_API_KEY="$(get_secret "LOCAL_LLM_API_KEY")" && print_success "LOCAL_LLM_API_KEY exported"
    export GROQ_API_KEY="$(get_secret "GROQ_API_KEY")" && print_success "GROQ_API_KEY exported"

    # Cloud Provider API Keys
    export OPENAI_API_KEY="$(get_secret "OPENAI_API_KEY")" && print_success "OPENAI_API_KEY exported"
    export ANTHROPIC_API_KEY="$(get_secret "ANTHROPIC_API_KEY")" && print_success "ANTHROPIC_API_KEY exported"
    export GOOGLE_API_KEY="$(get_secret "GOOGLE_API_KEY")" && print_success "GOOGLE_API_KEY exported"

    # Raptor Mini API Key
    export RAPTOR_API_KEY="$(get_secret "RAPTOR_API_KEY")" && print_success "RAPTOR_API_KEY exported"

    print_success "All secrets exported to environment variables"
}

# Create .env file from Bitwarden secrets
create_env_file() {
    local env_file=${1:-".env"}
    local env_example=${2:-".env.example"}

    if [ ! -f "$env_example" ]; then
        print_error "Environment example file not found: $env_example"
        return 1
    fi

    print_info "Creating $env_file from $env_example and Bitwarden secrets..."

    cp "$env_example" "$env_file"

    # Replace placeholder values with actual secrets
    sed -i.bak "s/your-kamatera-llm-api-key/$(get_secret "KAMATERA_LLM_API_KEY" | sed 's/[\/&]/\\&/g')/g" "$env_file"
    sed -i.bak "s/your-local-llm-api-key/$(get_secret "LOCAL_LLM_API_KEY" | sed 's/[\/&]/\\&/g')/g" "$env_file"
    sed -i.bak "s/your-grok-api-key/$(get_secret "GROQ_API_KEY" | sed 's/[\/&]/\\&/g')/g" "$env_file"
    sed -i.bak "s/sk-.../$(get_secret "OPENAI_API_KEY" | sed 's/[\/&]/\\&/g')/g" "$env_file"
    sed -i.bak "s/sk-ant-.../$(get_secret "ANTHROPIC_API_KEY" | sed 's/[\/&]/\\&/g')/g" "$env_file"

    rm "${env_file}.bak"
    print_success "Created $env_file with secrets from Bitwarden"
}

# Setup secrets for a specific service
setup_service() {
    local service=$1

    case $service in
        "backend")
            print_info "Setting up secrets for Goblin Assistant Backend..."
            cd "apps/goblin-assistant/backend"
            create_env_file
            ;;
        "raptor-mini")
            print_info "Setting up secrets for Raptor Mini..."
            cd "apps/raptor-mini"
            create_env_file
            ;;
        *)
            print_error "Unknown service: $service"
            echo "Available services: backend, raptor-mini"
            return 1
            ;;
    esac
}

# List required secrets
list_secrets() {
    print_info "Required secrets in Bitwarden vault:"
    echo ""
    echo "🔑 LLM API Keys:"
    echo "  - KAMATERA_LLM_API_KEY"
    echo "  - LOCAL_LLM_API_KEY"
    echo "  - GROQ_API_KEY"
    echo ""
    echo "☁️  Cloud Provider API Keys:"
    echo "  - OPENAI_API_KEY"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - GOOGLE_API_KEY"
    echo ""
    echo "🤖 AI Services:"
    echo "  - RAPTOR_API_KEY"
    echo ""
    print_info "To add a secret to Bitwarden:"
    echo "  bw create item"
}

# Main script logic
main() {
    check_bw_cli

    case "${1:-help}" in
        "status")
            bw status
            ;;
        "unlock")
            print_info "Run: bw unlock"
            ;;
        "export")
            check_vault_status
            export_secrets
            ;;
        "setup")
            check_vault_status
            if [ -z "$2" ]; then
                print_error "Please specify a service: backend or raptor-mini"
                echo "Usage: $0 setup <service>"
                exit 1
            fi
            setup_service "$2"
            ;;
        "list")
            list_secrets
            ;;
        "help"|*)
            echo "Bitwarden Secrets Management Script"
            echo ""
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  status          Show Bitwarden vault status"
            echo "  unlock          Show unlock command"
            echo "  export          Export all secrets to environment variables"
            echo "  setup <service> Create .env file for service (backend|raptor-mini)"
            echo "  list            List all required secrets"
            echo "  help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 status"
            echo "  $0 export"
            echo "  $0 setup backend"
            ;;
    esac
}

main "$@"
