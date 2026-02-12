#!/bin/bash
# Setup cheap fallback model (goblin-simple-llama-1b)
# This is a minimal 1B parameter model for emergency fallback

set -e

echo "🔧 Setting up cheap fallback model: goblin-simple-llama-1b"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if running as root (for Ollama service management)
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root for Ollama service management"
    exit 1
fi

# Configuration
FALLBACK_MODEL="goblin-simple-llama-1b"
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

# Function to check if Ollama is running
check_ollama() {
    if ! systemctl is-active --quiet ollama; then
        log_info "Starting Ollama service..."
        systemctl start ollama
        sleep 5
    fi

    # Test Ollama API
    if ! curl -s "$OLLAMA_HOST/api/tags" > /dev/null; then
        log_error "Ollama API not responding at $OLLAMA_HOST"
        return 1
    fi

    log_success "Ollama is running and responsive"
    return 0
}

# Function to create minimal model file
create_minimal_model() {
    log_info "Creating minimal 1B parameter model configuration..."

    # Create a minimal model configuration
    # Using a very small model for fallback - could be based on TinyLlama or similar
    cat > /tmp/fallback-model.modelfile << 'EOF'
FROM tinyllama:1b
PARAMETER temperature 0.8
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 512
PARAMETER repeat_penalty 1.1
PARAMETER repeat_last_n 64
PARAMETER num_predict 128

SYSTEM """
You are a helpful AI assistant. Keep responses brief and to the point.
If you cannot help with a request, say so clearly.
"""
EOF

    log_success "Minimal model configuration created"
}

# Function to pull/create the fallback model
setup_fallback_model() {
    log_info "Setting up fallback model: $FALLBACK_MODEL"

    # First try to pull a small existing model
    if ollama list | grep -q "tinyllama"; then
        log_info "TinyLlama model found, using as base"
        ollama create "$FALLBACK_MODEL" -f /tmp/fallback-model.modelfile
    elif ollama list | grep -q "gemma:2b"; then
        log_info "Using gemma:2b as fallback base (creating lighter version)"
        # Create a lighter version of gemma:2b
        cat > /tmp/fallback-model.modelfile << 'EOF'
FROM gemma:2b
PARAMETER temperature 0.9
PARAMETER top_p 0.95
PARAMETER top_k 50
PARAMETER num_ctx 256
PARAMETER repeat_penalty 1.0
PARAMETER num_predict 64

SYSTEM """
You are a basic AI assistant. Keep responses very brief.
This is a fallback service - please try again later for full functionality.
"""
EOF
        ollama create "$FALLBACK_MODEL" -f /tmp/fallback-model.modelfile
    else
        log_warning "No suitable base model found. Fallback model will be created when a base model becomes available."
        log_warning "Run this script again after setting up your primary models."
        return 1
    fi

    log_success "Fallback model $FALLBACK_MODEL created"
    return 0
}

# Function to test the fallback model
test_fallback_model() {
    log_info "Testing fallback model..."

    # Test basic inference
    response=$(echo 'test' | ollama run "$FALLBACK_MODEL" --format json 2>/dev/null | head -1)

    if [[ -n "$response" ]]; then
        log_success "Fallback model test successful"
        return 0
    else
        log_warning "Fallback model test failed - model may not be ready yet"
        return 1
    fi
}

# Function to update Ollama service configuration
update_ollama_service() {
    log_info "Updating Ollama service for fallback model support..."

    # Ensure Ollama service has proper environment variables
    mkdir -p /etc/systemd/system/ollama.service.d

    cat > /etc/systemd/system/ollama.service.d/fallback.conf << EOF
[Service]
Environment=OLLAMA_MAX_LOADED_MODELS=4
Environment=OLLAMA_KEEP_ALIVE=24h
Environment=OLLAMA_HOST=0.0.0.0:11434
Environment=OLLAMA_TMPDIR=/tmp
EOF

    systemctl daemon-reload
    log_success "Ollama service updated for fallback support"
}

# Main execution
main() {
    log_info "Starting cheap fallback model setup..."

    # Check Ollama
    if ! check_ollama; then
        exit 1
    fi

    # Update Ollama service
    update_ollama_service

    # Create model configuration
    create_minimal_model

    # Setup fallback model
    if setup_fallback_model; then
        # Test the model
        test_fallback_model

        log_success "Cheap fallback model setup complete!"
        echo ""
        log_info "Fallback model: $FALLBACK_MODEL"
        log_info "Capabilities: Basic chat, very fast response, minimal context"
        log_info "Use case: Emergency fallback during high load or outages"
        echo ""
        log_info "To test: ollama run $FALLBACK_MODEL"
    else
        log_warning "Fallback model setup deferred - run again after primary models are available"
    fi
}

main "$@"</content>
<parameter name="filePath">/Users/fuaadabdullah/ForgeMonorepo/scripts/setup_fallback_model.sh
