#!/bin/bash
# Quick Start Migration Sprint - 1 Hour Migration Workflow
# This script guides you through migrating ~30-50% of your tests in under 1 hour

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Timer variables
START_TIME=$(date +%s)

# Function to print colored output
print_header() {
    echo -e "\n${CYAN}=======================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}=======================================${NC}"
}

print_step() {
    echo -e "\n${BLUE}▶️  STEP $1: $2${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_time() {
    local current_time=$(date +%s)
    local elapsed=$((current_time - START_TIME))
    local minutes=$((elapsed / 60))
    local seconds=$((elapsed % 60))
    echo -e "${BLUE}⏱️  Time elapsed: ${minutes}m ${seconds}s${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_step "0" "Checking Prerequisites"

    # Check if Node.js is available
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js first."
        exit 1
    fi

    # Check if we're in a project with package.json
    if [ ! -f "package.json" ]; then
        print_error "No package.json found. Please run this from your project root."
        exit 1
    fi

    # Check if migration tools exist
    if [ ! -f "scripts/turbo-migrate.js" ]; then
        print_warning "Migration tools not found. Installing..."
        # Try to install migration tools
        npm install --save-dev @testing-library/react-codemod jest-codemods cli-progress || true
    fi

    print_success "Prerequisites check passed"
}

# Step 1: Turbo setup
step_1_setup() {
    print_step "1" "Turbo Setup (2 minutes)"
    echo "Installing migration tools and dependencies..."

    npm install --save-dev @testing-library/react-codemod jest-codemods cli-progress

    # Install Testing Library if not present
    if ! grep -q "@testing-library/react" package.json; then
        npm install --save-dev @testing-library/react @testing-library/user-event @testing-library/jest-dom
    fi

    print_success "Setup completed"
    print_time
}

# Step 2: Analysis
step_2_analyze() {
    print_step "2" "Quick Analysis (3 minutes)"
    echo "Scanning your codebase for migration opportunities..."

    if [ -f "scripts/migration-dashboard.js" ]; then
        node scripts/migration-dashboard.js
    else
        echo "Migration dashboard not found. Running basic analysis..."
        # Basic analysis using grep
        TOTAL_TESTS=$(find . -name "*.test.*" -o -name "*.spec.*" | wc -l)
        ENZYME_TESTS=$(grep -l "from 'enzyme'" $(find . -name "*.test.*" -o -name "*.spec.*") 2>/dev/null | wc -l || echo "0")

        echo "📊 Quick Analysis Results:"
        echo "   Total test files: $TOTAL_TESTS"
        echo "   Enzyme tests found: $ENZYME_TESTS"
        echo "   Migration candidates: $ENZYME_TESTS"
    fi

    print_success "Analysis completed"
    print_time
}

# Step 3: Auto-migrate low-hanging fruit
step_3_auto_migrate() {
    print_step "3" "Auto-Migrate Low-Hanging Fruit (10 minutes)"
    echo "Automatically migrating simple tests (Button, Input, utility tests)..."

    # Run turbo migration on simple patterns
    if [ -f "scripts/turbo-migrate.js" ]; then
        node scripts/turbo-migrate.js --pattern="Button|Input|util|helper" --dry-run --verbose

        echo
        read -p "Review the dry-run results above. Proceed with actual migration? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            node scripts/turbo-migrate.js --pattern="Button|Input|util|helper"
            print_success "Auto-migration completed"
        else
            print_warning "Auto-migration skipped"
        fi
    else
        print_warning "Turbo migrate script not found. Skipping auto-migration."
    fi

    print_time
}

# Step 4: Migrate key components
step_4_key_components() {
    print_step "4" "Migrate Key Components (30 minutes)"
    echo "Time to migrate your most important components manually with AI assistance."

    echo
    echo "🎯 Priority Components to Migrate:"
    echo "   1. Button components (5-10 minutes each)"
    echo "   2. Form inputs (10-15 minutes each)"
    echo "   3. Modal/Dialog components (15-20 minutes each)"
    echo
    echo "💡 Pro Tips:"
    echo "   • Use GitHub Copilot or your AI assistant"
    echo "   • Copy the migration patterns from .github/copilot-instructions.md"
    echo "   • Focus on one component at a time"
    echo "   • Run tests after each migration"
    echo
    echo "🚀 Ready to start migrating key components?"
    read -p "Press Enter when ready, or 's' to skip: " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Ss]$ ]]; then
        print_warning "Key component migration skipped"
        return
    fi

    # Try to find and suggest components
    if [ -d "src/components" ]; then
        echo "📂 Found components in src/components/:"
        ls src/components/ | head -10
    elif [ -d "components" ]; then
        echo "📂 Found components in components/:"
        ls components/ | head -10
    fi

    echo
    echo "🧠 Use this prompt with your AI assistant for each component:"
    echo
    echo 'Convert this Enzyme test to Testing Library:'
    echo '[PASTE YOUR ENZYME TEST HERE]'
    echo
    echo 'Guidelines:'
    echo '1. Use screen.getByRole() preferred'
    echo '2. Use userEvent for interactions'
    echo '3. Test behavior, not implementation'
    echo '4. Add proper async/await'
    echo
    read -p "Press Enter when you've migrated some key components: "

    print_success "Key component migration phase completed"
    print_time
}

# Step 5: Validate and commit
step_5_validate() {
    print_step "5" "Validate & Commit (5 minutes)"
    echo "Running tests to ensure everything works..."

    # Run tests
    if npm test; then
        print_success "All tests passing! 🎉"

        # Show git status
        echo
        echo "📝 Git status:"
        git status --short

        echo
        read -p "Commit these migration changes? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add .
            git commit -m "feat: migrate Enzyme tests to Testing Library

- Auto-migrated simple components and utilities
- Manually migrated key components with AI assistance
- All tests passing
- Ready for further migration sprints"
            print_success "Changes committed successfully"
        fi
    else
        print_warning "Some tests are failing. Please fix them before committing."
        echo
        echo "💡 Debugging tips:"
        echo "   • Check for missing imports (@testing-library/react)"
        echo "   • Ensure userEvent is used instead of fireEvent"
        echo "   • Verify async/await usage for user interactions"
        echo "   • Run 'npm run migrate:dashboard' for detailed analysis"
    fi

    print_time
}

# Step 6: Generate report
step_6_report() {
    print_step "6" "Generate Report (2 minutes)"
    echo "Creating migration progress report..."

    if [ -f "scripts/migration-dashboard.js" ]; then
        node scripts/migration-dashboard.js > migration-sprint-report.txt
        print_success "Report saved to migration-sprint-report.txt"
    else
        # Basic report
        TOTAL_TESTS=$(find . -name "*.test.*" -o -name "*.spec.*" | wc -l)
        ENZYME_TESTS=$(grep -l "from 'enzyme'" $(find . -name "*.test.*" -o -name "*.spec.*") 2>/dev/null | wc -l || echo "0")
        TESTING_LIBRARY_TESTS=$(grep -l "from '@testing-library/react'" $(find . -name "*.test.*" -o -name "*.spec.*") 2>/dev/null | wc -l || echo "0")

        cat > migration-sprint-report.txt << EOF
Migration Sprint Report
=======================

Sprint Duration: $(print_time)
Total Test Files: $TOTAL_TESTS
Enzyme Tests Remaining: $ENZYME_TESTS
Testing Library Tests: $TESTING_LIBRARY_TESTS
Migration Progress: $((TESTING_LIBRARY_TESTS * 100 / TOTAL_TESTS))%

Next Steps:
- Continue migrating remaining components
- Focus on complex stateful components
- Consider team parallel migration for large codebases

Tools Available:
- npm run migrate:dashboard  # Progress tracking
- npm run migrate:interactive  # Guided migration
- npm run migrate:swarm  # Team distribution
EOF

        print_success "Basic report saved to migration-sprint-report.txt"
    fi

    print_time
}

# Main execution
main() {
    print_header "🚀 Quick Start Migration Sprint"
    echo "Welcome to the 1-hour Enzyme to Testing Library migration sprint!"
    echo
    echo "This guided workflow will help you migrate ~30-50% of your tests"
    echo "in under 1 hour with minimal manual effort."
    echo
    echo "⏱️  Total estimated time: 45-60 minutes"
    echo "🎯 Target completion: 30-50% of tests migrated"
    echo

    read -p "Ready to start the migration sprint? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Sprint cancelled. Run this script again when ready!"
        exit 0
    fi

    check_prerequisites
    step_1_setup
    step_2_analyze
    step_3_auto_migrate
    step_4_key_components
    step_5_validate
    step_6_report

    print_header "🎉 Sprint Complete!"
    echo "Congratulations! You've completed the quick start migration sprint."
    echo
    echo "📊 Check migration-sprint-report.txt for your results"
    echo "🔄 Run 'npm run migrate:dashboard' to see current progress"
    echo "🚀 Continue with additional sprints for remaining tests"
    echo
    print_time
}

# Run main function
main "$@"
