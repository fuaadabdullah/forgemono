#!/usr/bin/env bash
# ForgeTM Backend Configuration Management Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FORGE_TM_DIR="${REPO_ROOT}/ForgeTM"
BACKEND_DIR="${FORGE_TM_DIR}/apps/backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration file paths
ENV_FILE="${BACKEND_DIR}/.env"
ENV_EXAMPLE="${BACKEND_DIR}/.env.example"

# Load current configuration
load_config() {
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
    fi
}

# Save configuration
save_config() {
    local key="$1"
    local value="$2"

    # Create .env file if it doesn't exist
    touch "$ENV_FILE"

    # Update or add the configuration
    if grep -q "^${key}=" "$ENV_FILE"; then
        sed -i.bak "s/^${key}=.*/${key}=${value}/" "$ENV_FILE"
    else
        echo "${key}=${value}" >> "$ENV_FILE"
    fi

    rm -f "${ENV_FILE}.bak"
    log_success "Configuration updated: ${key}=${value}"
}

# Get configuration value
get_config() {
    local key="$1"
    local default="${2:-}"

    if [ -f "$ENV_FILE" ] && grep -q "^${key}=" "$ENV_FILE"; then
        grep "^${key}=" "$ENV_FILE" | cut -d'=' -f2-
    else
        echo "$default"
    fi
}

# List all configuration
list_config() {
    log_info "Current configuration:"

    if [ ! -f "$ENV_FILE" ]; then
        log_warning "No .env file found"
        return
    fi

    echo "=== Current Configuration ==="
    while IFS='=' read -r key value; do
        if [[ $key =~ ^[[:space:]]*# ]]; then
            continue
        fi
        if [ -n "$key" ]; then
            echo "${key}=${value}"
        fi
    done < "$ENV_FILE"
}

# Validate configuration
validate_config() {
    log_info "Validating configuration..."

    local errors=0

    # Check required environment variables
    local required_vars=(
        "SECRET_KEY"
        "DATABASE_URL"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "$(get_config "$var")" ]; then
            log_error "Missing required configuration: $var"
            errors=$((errors + 1))
        fi
    done

    # Validate database URL format
    local db_url
    db_url=$(get_config "DATABASE_URL")
    if [ -n "$db_url" ]; then
        if [[ ! $db_url =~ ^(sqlite|postgresql|mysql):// ]]; then
            log_error "Invalid DATABASE_URL format. Expected: sqlite://, postgresql://, or mysql://"
            errors=$((errors + 1))
        fi
    fi

    # Validate port numbers
    local backend_port
    backend_port=$(get_config "BACKEND_PORT" "8000")
    if ! [[ $backend_port =~ ^[0-9]+$ ]] || [ "$backend_port" -lt 1 ] || [ "$backend_port" -gt 65535 ]; then
        log_error "Invalid BACKEND_PORT: $backend_port (must be 1-65535)"
        errors=$((errors + 1))
    fi

    if [ $errors -eq 0 ]; then
        log_success "Configuration validation passed"
        return 0
    else
        log_error "Configuration validation failed with $errors errors"
        return 1
    fi
}

# Initialize configuration from example
init_config() {
    if [ ! -f "$ENV_EXAMPLE" ]; then
        log_error "Example configuration file not found: $ENV_EXAMPLE"
        exit 1
    fi

    if [ -f "$ENV_FILE" ]; then
        log_warning ".env file already exists. Use --force to overwrite."
        read -p "Overwrite existing configuration? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Configuration initialization cancelled"
            exit 0
        fi
    fi

    cp "$ENV_EXAMPLE" "$ENV_FILE"
    log_success "Configuration initialized from example file"

    # Generate secure secret key if not set
    if [ -z "$(get_config "SECRET_KEY")" ]; then
        local secret_key
        secret_key=$(openssl rand -hex 32)
        save_config "SECRET_KEY" "$secret_key"
        log_success "Generated secure SECRET_KEY"
    fi
}

# Set configuration value interactively
set_config_interactive() {
    local key="$1"

    # Get current value
    local current_value
    current_value=$(get_config "$key")

    if [ -n "$current_value" ]; then
        echo "Current value for $key: $current_value"
    else
        echo "Setting new configuration: $key"
    fi

    # Prompt for new value
    read -p "Enter new value for $key: " -r new_value

    if [ -n "$new_value" ]; then
        save_config "$key" "$new_value"
    else
        log_info "No value entered, configuration unchanged"
    fi
}

# Database configuration helpers
configure_database() {
    log_info "Database Configuration"

    echo "Select database type:"
    echo "1) SQLite (default, file-based)"
    echo "2) PostgreSQL"
    echo "3) MySQL"
    read -p "Enter choice (1-3): " -r db_choice

    case $db_choice in
        1)
            local db_path
            read -p "Enter SQLite database path (default: forgetm.db): " -r db_path
            db_path=${db_path:-forgetm.db}
            save_config "DATABASE_URL" "sqlite:///${db_path}"
            ;;
        2)
            read -p "PostgreSQL host: " -r pg_host
            read -p "PostgreSQL port (default: 5432): " -r pg_port
            pg_port=${pg_port:-5432}
            read -p "PostgreSQL database: " -r pg_db
            read -p "PostgreSQL user: " -r pg_user
            read -s -p "PostgreSQL password: " -r pg_pass
            echo
            save_config "DATABASE_URL" "postgresql://${pg_user}:${pg_pass}@${pg_host}:${pg_port}/${pg_db}"
            ;;
        3)
            read -p "MySQL host: " -r mysql_host
            read -p "MySQL port (default: 3306): " -r mysql_port
            mysql_port=${mysql_port:-3306}
            read -p "MySQL database: " -r mysql_db
            read -p "MySQL user: " -r mysql_user
            read -s -p "MySQL password: " -r mysql_pass
            echo
            save_config "DATABASE_URL" "mysql://${mysql_user}:${mysql_pass}@${mysql_host}:${mysql_port}/${mysql_db}"
            ;;
        *)
            log_error "Invalid choice"
            return 1
            ;;
    esac

    log_success "Database configuration updated"
}

# API Keys configuration
configure_api_keys() {
    log_info "API Keys Configuration"

    local api_keys=(
        "OPENAI_API_KEY"
        "GEMINI_API_KEY"
        "DEEPSEEK_API_KEY"
        "POLYGON_API_KEY"
        "PINECONE_API_KEY"
    )

    for key in "${api_keys[@]}"; do
        if [ -z "$(get_config "$key")" ]; then
            read -s -p "Enter $key (or press Enter to skip): " -r key_value
            echo
            if [ -n "$key_value" ]; then
                save_config "$key" "$key_value"
            fi
        else
            log_info "$key is already configured"
        fi
    done

    log_success "API keys configuration completed"
}

# Service configuration
configure_service() {
    log_info "Service Configuration"

    # Backend host and port
    local backend_host
    read -p "Backend host (default: 127.0.0.1): " -r backend_host
    backend_host=${backend_host:-127.0.0.1}
    save_config "BACKEND_HOST" "$backend_host"

    local backend_port
    read -p "Backend port (default: 8000): " -r backend_port
    backend_port=${backend_port:-8000}
    save_config "BACKEND_PORT" "$backend_port"

    # Tracing configuration
    read -p "Enable OpenTelemetry tracing? (y/N): " -r enable_tracing
    if [[ $enable_tracing =~ ^[Yy]$ ]]; then
        save_config "ENABLE_TRACING" "true"
        read -p "OTLP endpoint (default: http://localhost:4317): " -r otlp_endpoint
        otlp_endpoint=${otlp_endpoint:-http://localhost:4317}
        save_config "OTLP_ENDPOINT" "$otlp_endpoint"
    else
        save_config "ENABLE_TRACING" "false"
    fi

    log_success "Service configuration completed"
}

# Main configuration function
config() {
    local command="$1"
    shift

    case "$command" in
        "init")
            init_config
            ;;
        "list")
            list_config
            ;;
        "get")
            local key="$1"
            local value
            value=$(get_config "$key")
            if [ -n "$value" ]; then
                echo "$value"
            else
                echo "(not set)"
            fi
            ;;
        "set")
            local key="$1"
            local value="$2"
            save_config "$key" "$value"
            ;;
        "set-interactive")
            local key="$1"
            set_config_interactive "$key"
            ;;
        "validate")
            validate_config
            ;;
        "database")
            configure_database
            ;;
        "api-keys")
            configure_api_keys
            ;;
        "service")
            configure_service
            ;;
        "wizard")
            log_info "Starting interactive configuration wizard..."
            configure_database
            configure_api_keys
            configure_service
            validate_config
            ;;
        *)
            log_error "Unknown configuration command: $command"
            usage
            exit 1
            ;;
    esac
}

# Show usage
usage() {
    cat << EOF
ForgeTM Backend Configuration Management Script

USAGE:
    $0 COMMAND [OPTIONS]

COMMANDS:
    init                    Initialize configuration from .env.example
    list                    List all current configuration
    get KEY                 Get configuration value for KEY
    set KEY VALUE           Set configuration KEY to VALUE
    set-interactive KEY     Set configuration KEY interactively
    validate                Validate current configuration
    database                Configure database settings interactively
    api-keys                Configure API keys interactively
    service                 Configure service settings interactively
    wizard                  Run complete interactive configuration wizard

EXAMPLES:
    $0 init                          # Initialize configuration
    $0 list                          # Show current config
    $0 set BACKEND_PORT 8080         # Set specific value
    $0 get DATABASE_URL              # Get specific value
    $0 validate                      # Validate configuration
    $0 wizard                        # Interactive setup

EOF
}

# Main script
main() {
    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi

    local command="$1"
    shift

    case "$command" in
        -h|--help)
            usage
            exit 0
            ;;
        *)
            load_config
            config "$command" "$@"
            ;;
    esac
}

# Run main function with all arguments
main "$@"
