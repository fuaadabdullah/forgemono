#!/usr/bin/env bash
# CircleCI Setup Script for Goblin Infrastructure
# This script helps configure CircleCI environment variables and validates the setup

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# CircleCI configuration
CIRCLE_ORG_ID="86f0d600-175c-41cf-bf68-3855b72f7645"
CIRCLE_PROJECT="goblin-infra"
CIRCLE_API_TOKEN="${CIRCLE_TOKEN:-}"

echo -e "${GREEN}=== CircleCI Setup for Goblin Infrastructure ===${NC}\n"

# Function to print status messages
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if CircleCI CLI is installed
check_circleci_cli() {
    if ! command -v circleci &> /dev/null; then
        print_error "CircleCI CLI not found"
        echo "Install with: brew install circleci"
        echo "Or download from: https://circleci.com/docs/local-cli/"
        return 1
    fi
    print_status "CircleCI CLI is installed"
    return 0
}

# Validate CircleCI API token
validate_token() {
    if [ -z "$CIRCLE_API_TOKEN" ]; then
        print_error "CIRCLE_TOKEN environment variable not set"
        echo "Export your token: export CIRCLE_TOKEN=your_token_here"
        return 1
    fi
    print_status "CircleCI API token is set"
    return 0
}

# Check required environment variables for secrets
check_env_vars() {
    echo -e "\n${GREEN}Checking required environment variables...${NC}"

    local missing_vars=0

    # GitHub Container Registry
    if [ -z "${GHCR_TOKEN:-}" ]; then
        print_error "GHCR_TOKEN not set"
        ((missing_vars++))
    else
        print_status "GHCR_TOKEN is set"
    fi

    if [ -z "${GHCR_USER:-}" ]; then
        print_error "GHCR_USER not set"
        ((missing_vars++))
    else
        print_status "GHCR_USER is set"
    fi

    # Terraform Cloud
    if [ -z "${TF_CLOUD_TOKEN:-}" ]; then
        print_warning "TF_CLOUD_TOKEN not set (optional if using other auth)"
        ((missing_vars++))
    else
        print_status "TF_CLOUD_TOKEN is set"
    fi

    if [ $missing_vars -gt 0 ]; then
        echo -e "\n${YELLOW}Missing $missing_vars required variables${NC}"
        echo "Set them before running this script or add them manually in CircleCI UI"
        return 1
    fi

    return 0
}

# Add environment variable to CircleCI project
add_env_var() {
    local var_name=$1
    local var_value=$2
    local vcs_type="github"
    local username="fuaadabdullah"

    echo "Adding $var_name to CircleCI..."

    curl -X POST \
        --header "Circle-Token: $CIRCLE_API_TOKEN" \
        --header "Content-Type: application/json" \
        --data "{\"name\":\"$var_name\", \"value\":\"$var_value\"}" \
        "https://circleci.com/api/v2/project/$vcs_type/$username/$CIRCLE_PROJECT/envvar"

    if [ $? -eq 0 ]; then
        print_status "Added $var_name"
    else
        print_error "Failed to add $var_name"
    fi
}

# Setup all environment variables in CircleCI
setup_env_vars() {
    echo -e "\n${GREEN}Setting up CircleCI environment variables...${NC}"

    if ! validate_token; then
        return 1
    fi

    # GitHub Container Registry
    if [ -n "${GHCR_TOKEN:-}" ]; then
        add_env_var "GHCR_TOKEN" "$GHCR_TOKEN"
    fi

    if [ -n "${GHCR_USER:-}" ]; then
        add_env_var "GHCR_USER" "$GHCR_USER"
    fi

    # Terraform Cloud
    if [ -n "${TF_CLOUD_TOKEN:-}" ]; then
        add_env_var "TF_CLOUD_TOKEN" "$TF_CLOUD_TOKEN"
    fi

    if [ -n "${TF_ORGANIZATION:-}" ]; then
        add_env_var "TF_ORGANIZATION" "${TF_ORGANIZATION:-GoblinOS}"
    fi

    print_status "Environment variables setup complete"
}

# Validate CircleCI config
validate_config() {
    echo -e "\n${GREEN}Validating CircleCI configuration...${NC}"

    if [ ! -f ".circleci/config.yml" ]; then
        print_error "No .circleci/config.yml found in current directory"
        return 1
    fi

    if check_circleci_cli; then
        circleci config validate
        if [ $? -eq 0 ]; then
            print_status "CircleCI config is valid"
        else
            print_error "CircleCI config has errors"
            return 1
        fi
    fi

    return 0
}

# Setup self-hosted runner
setup_runner() {
    echo -e "\n${GREEN}Setting up self-hosted runner...${NC}"

    local runner_token="f2b1c985282919121e93365cbdc8df38a3cc8ffea18241c9061e26d6df5a5dc7dc4da6ff5c215256"
    local runner_dir="$HOME/.circleci-runner"

    # Check if runner is already installed
    if command -v circleci-runner &> /dev/null; then
        print_status "CircleCI runner is already installed"
    else
        print_warning "CircleCI runner not installed"
        echo "Install with: brew install circleci-runner"
        echo "Or follow: https://circleci.com/docs/runner-installation/"
    fi

    # Create runner config
    mkdir -p "$runner_dir"

    cat > "$runner_dir/config.yaml" <<EOF
api:
  auth_token: $runner_token

runner:
  name: goblin-assistant-local
  working_directory: /tmp/circleci-runner
  cleanup_working_directory: true

logging:
  file: $runner_dir/runner.log
  level: info
EOF

    print_status "Runner config created at $runner_dir/config.yaml"

    echo -e "\n${YELLOW}To start the runner, run:${NC}"
    echo "circleci-runner machine --config $runner_dir/config.yaml"
}

# Follow CircleCI project
follow_project() {
    echo -e "\n${GREEN}Following project in CircleCI...${NC}"

    if ! validate_token; then
        return 1
    fi

    local vcs_type="github"
    local username="fuaadabdullah"

    curl -X POST \
        --header "Circle-Token: $CIRCLE_API_TOKEN" \
        "https://circleci.com/api/v1.1/project/$vcs_type/$username/$CIRCLE_PROJECT/follow"

    if [ $? -eq 0 ]; then
        print_status "Project is now followed in CircleCI"
    else
        print_warning "Failed to follow project (may already be followed)"
    fi
}

# Main menu
show_menu() {
    echo -e "\n${GREEN}What would you like to do?${NC}"
    echo "1. Check prerequisites"
    echo "2. Validate CircleCI config"
    echo "3. Setup environment variables in CircleCI"
    echo "4. Setup self-hosted runner"
    echo "5. Follow project in CircleCI"
    echo "6. Run full setup (all of the above)"
    echo "7. Exit"
    echo -n "Enter choice [1-7]: "
}

# Main execution
main() {
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            show_menu
            read -r choice
            case $choice in
                1)
                    check_circleci_cli
                    check_env_vars
                    ;;
                2)
                    validate_config
                    ;;
                3)
                    setup_env_vars
                    ;;
                4)
                    setup_runner
                    ;;
                5)
                    follow_project
                    ;;
                6)
                    check_circleci_cli
                    check_env_vars
                    validate_config
                    setup_env_vars
                    setup_runner
                    follow_project
                    print_status "Full setup complete!"
                    ;;
                7)
                    echo "Exiting..."
                    exit 0
                    ;;
                *)
                    print_error "Invalid choice"
                    ;;
            esac
        done
    else
        # Non-interactive mode
        case "$1" in
            check)
                check_circleci_cli
                check_env_vars
                ;;
            validate)
                validate_config
                ;;
            setup-env)
                setup_env_vars
                ;;
            setup-runner)
                setup_runner
                ;;
            follow)
                follow_project
                ;;
            all)
                check_circleci_cli
                check_env_vars
                validate_config
                setup_env_vars
                setup_runner
                follow_project
                ;;
            *)
                echo "Usage: $0 {check|validate|setup-env|setup-runner|follow|all}"
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@"
