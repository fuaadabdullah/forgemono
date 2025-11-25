#!/bin/bash

# mac-undervolt.sh
# Safe temporary undervolting for Intel Macs using VoltageShift
# Based on PART 1 — TEMPORARY, SAFE METHOD guide
# This script provides a safe way to test undervolting that resets on reboot

set -e  # Exit on any error

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

# Function to check if VoltageShift is available
check_voltageshift() {
    if ! command -v voltageshift &> /dev/null; then
        print_error "VoltageShift not found in PATH."
        print_info "Run the setup script first:"
        echo "  bash tools/setup-voltageshift.sh"
        print_info "Or download manually from: https://github.com/sicreative/VoltageShift"
        print_info "Place the binary in a directory and add it to your PATH, or run this script from that directory."
        exit 1
    fi
}

# Function to show system info
show_system_info() {
    print_info "Checking system state..."
    echo "Current VoltageShift info:"
    voltageshift info
    echo ""
}

# Function to apply conservative undervolt
apply_undervolt() {
    print_warning "Applying conservative CPU undervolt (-20 mV)..."
    print_warning "This will only affect CPU core voltage. Other components remain at default."
    print_warning "This change resets on reboot - completely safe for testing."

    read -p "Continue with undervolt? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Undervolt cancelled."
        exit 0
    fi

    # Apply -20 mV to CPU only (cache, iGPU, etc. at 0)
    voltageshift offset -20 0 0 0 0 0

    if [ $? -eq 0 ]; then
        print_success "Undervolt applied successfully!"
        print_info "CPU offset: -20 mV"
        print_info "Cache, iGPU, System Agent, Analog I/O, Misc: 0 mV (default)"
    else
        print_error "Failed to apply undervolt."
        exit 1
    fi
}

# Function to monitor system
monitor_system() {
    print_info "Starting system monitoring..."
    print_info "Watch for:"
    echo "  - CPU temperatures stabilizing lower"
    echo "  - Power consumption slightly lower"
    echo "  - CPU clocks sustaining higher Turbo (3.6–4.1GHz)"
    echo ""
    print_warning "Press Ctrl+C to stop monitoring and continue."

    # Run monitoring in background and wait
    voltageshift mon &
    MON_PID=$!

    # Wait for user interrupt
    trap "kill $MON_PID 2>/dev/null; echo; print_info 'Monitoring stopped.'" INT
    wait $MON_PID
}

# Function to revert undervolt
revert_undervolt() {
    print_info "Reverting to default voltages..."
    voltageshift offset 0 0 0 0 0 0

    if [ $? -eq 0 ]; then
        print_success "Voltages restored to defaults."
    else
        print_error "Failed to revert voltages."
        exit 1
    fi
}

# Main menu function
show_menu() {
    echo ""
    echo "========================================"
    echo "   Mac Undervolt Tool - Safe Mode"
    echo "========================================"
    echo "1. Check system info"
    echo "2. Apply conservative undervolt (-20 mV CPU)"
    echo "3. Monitor system performance"
    echo "4. Revert to default voltages"
    echo "5. Full test cycle (info → undervolt → monitor)"
    echo "6. Exit"
    echo ""
}

# Full test cycle
full_test_cycle() {
    print_info "Starting full test cycle..."
    echo ""

    show_system_info
    apply_undervolt
    monitor_system

    echo ""
    print_info "Test cycle complete. You can now:"
    echo "  - Continue monitoring with option 3"
    echo "  - Revert voltages with option 4"
    echo "  - Reboot to reset (recommended for safety)"
}

# Main script logic
main() {
    print_info "Mac Undervolt Tool - PART 1 Safe Method"
    print_warning "This tool uses VoltageShift for temporary undervolting."
    print_warning "All changes reset on reboot - completely safe for testing."
    echo ""

    check_voltageshift

    while true; do
        show_menu
        read -p "Choose an option (1-6): " choice
        echo ""

        case $choice in
            1)
                show_system_info
                ;;
            2)
                apply_undervolt
                ;;
            3)
                monitor_system
                ;;
            4)
                revert_undervolt
                ;;
            5)
                full_test_cycle
                ;;
            6)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid option. Please choose 1-6."
                ;;
        esac

        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function
main "$@"
