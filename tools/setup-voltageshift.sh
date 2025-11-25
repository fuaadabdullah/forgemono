#!/bin/bash

# setup-voltageshift.sh
# Downloads and sets up VoltageShift for mac-undervolt.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This script is designed for macOS only."
        exit 1
    fi
}

# Check if VoltageShift is already available
check_existing() {
    if command -v voltageshift &> /dev/null; then
        print_success "VoltageShift is already installed and available in PATH."
        voltageshift info
        exit 0
    fi
}

# Download VoltageShift
download_voltageshift() {
    local temp_dir="/tmp/voltageshift-setup"
    local zip_url="https://codeload.github.com/sicreative/VoltageShift/zip/refs/heads/master"
    local zip_file="$temp_dir/voltageshift.zip"
    local extract_dir="$temp_dir/extracted"

    print_info "Creating temporary directory..."
    mkdir -p "$temp_dir"

    print_info "Downloading VoltageShift from GitHub..."
    if ! curl -L -o "$zip_file" "$zip_url"; then
        print_error "Failed to download VoltageShift."
        rm -rf "$temp_dir"
        exit 1
    fi

    print_info "Extracting VoltageShift..."
    mkdir -p "$extract_dir"
    if ! unzip -q -o "$zip_file" -d "$extract_dir"; then
        print_error "Failed to extract VoltageShift."
        rm -rf "$temp_dir"
        exit 1
    fi

    # Find the extracted directory (should be VoltageShift-master)
    local voltageshift_dir
    voltageshift_dir=$(find "$extract_dir" -name "VoltageShift*" -type d | head -1)

    if [[ -z "$voltageshift_dir" ]]; then
        print_error "Could not find VoltageShift directory after extraction."
        rm -rf "$temp_dir"
        exit 1
    fi

    print_success "VoltageShift downloaded and extracted to: $voltageshift_dir"
    echo "$voltageshift_dir"
}

# Build VoltageShift
build_voltageshift() {
    local voltageshift_dir="$1"

    print_info "Building VoltageShift..."
    cd "$voltageshift_dir"

    # Check if Makefile exists
    if [[ ! -f "Makefile" ]]; then
        print_error "Makefile not found in VoltageShift directory."
        print_info "This version may not be buildable. Please check the GitHub repository for pre-built binaries."
        exit 1
    fi

    # Try to build
    if ! make; then
        print_error "Failed to build VoltageShift."
        print_info "You may need to install Xcode command line tools:"
        echo "  xcode-select --install"
        exit 1
    fi

    # Check if binary was created
    if [[ ! -f "voltageshift" ]]; then
        print_error "voltageshift binary not found after build."
        exit 1
    fi

    print_success "VoltageShift built successfully."
    echo "$voltageshift_dir/voltageshift"
}

# Setup PATH or copy to local bin
setup_binary() {
    local binary_path="$1"
    local local_bin="$HOME/bin"

    print_info "Setting up VoltageShift binary..."

    # Option 1: Copy to ~/bin and add to PATH
    mkdir -p "$local_bin"

    if cp "$binary_path" "$local_bin/"; then
        print_success "VoltageShift copied to $local_bin/voltageshift"

        # Check if ~/bin is in PATH
        if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
            print_warning "~/bin is not in your PATH."
            print_info "Add the following line to your ~/.zshrc or ~/.bash_profile:"
            echo "  export PATH=\"\$HOME/bin:\$PATH\""
            print_info "Then restart your terminal or run: source ~/.zshrc"
        else
            print_success "~/bin is already in your PATH."
        fi

        # Make executable
        chmod +x "$local_bin/voltageshift"
        print_success "VoltageShift is now ready to use!"
        print_info "Test it with: voltageshift info"

    else
        print_error "Failed to copy VoltageShift to $local_bin"
        print_info "You can manually copy it or add $binary_path to your PATH"
        exit 1
    fi
}

# Main setup function
main() {
    print_info "VoltageShift Setup for mac-undervolt.sh"
    echo ""

    check_macos
    check_existing

    print_warning "This will download and build VoltageShift from GitHub."
    print_warning "Make sure you have Xcode command line tools installed."
    echo ""

    read -p "Continue with setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Setup cancelled."
        exit 0
    fi

    local voltageshift_dir
    voltageshift_dir=$(download_voltageshift)

    local binary_path
    binary_path=$(build_voltageshift "$voltageshift_dir")

    setup_binary "$binary_path"

    # Cleanup
    print_info "Cleaning up temporary files..."
    rm -rf "/tmp/voltageshift-setup"

    print_success "Setup complete! You can now use mac-undervolt.sh"
}

# Run main function
main "$@"
