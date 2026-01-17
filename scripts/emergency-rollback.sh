#!/bin/bash
# Emergency Rollback Script for Enzyme Migration
# Use this when migration goes wrong and you need to quickly revert

set -e  # Exit on any error

echo "🚨 EMERGENCY ROLLBACK - Enzyme Migration"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository. Cannot rollback."
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
print_status "Current branch: $CURRENT_BRANCH"

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --staged --quiet; then
    print_warning "You have uncommitted changes. These will be lost in rollback."
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Rollback cancelled."
        exit 0
    fi
fi

# Strategy selection
echo
echo "Select rollback strategy:"
echo "1) Quick revert - Discard all test changes"
echo "2) Smart rollback - Revert only migrated test files"
echo "3) Branch rollback - Switch to pre-migration branch"
echo "4) Full reset - Reset to before migration started"
echo

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        print_status "Performing quick revert..."

        # Find and reset all test files
        find . -name "*.test.*" -o -name "*.spec.*" | head -20 | xargs git checkout -- 2>/dev/null || true

        # Reinstall Enzyme if needed
        if ! grep -q "enzyme" package.json; then
            print_status "Reinstalling Enzyme..."
            npm install --save-dev enzyme enzyme-adapter-react-16
        fi

        print_success "Quick revert completed."
        ;;

    2)
        print_status "Performing smart rollback..."

        # Find migrated test files (those using Testing Library)
        MIGRATED_FILES=$(grep -l "from '@testing-library/react'" $(find . -name "*.test.*" -o -name "*.spec.*") 2>/dev/null || true)

        if [ -n "$MIGRATED_FILES" ]; then
            echo "$MIGRATED_FILES" | xargs git checkout --
            print_success "Reverted $(echo "$MIGRATED_FILES" | wc -l) migrated test files."
        else
            print_warning "No migrated test files found."
        fi
        ;;

    3)
        print_status "Looking for pre-migration backup branches..."

        # Find backup branches
        BACKUP_BRANCHES=$(git branch | grep -E "migration|backup" | sed 's/*//' | sed 's/ //g' || true)

        if [ -n "$BACKUP_BRANCHES" ]; then
            echo "Available backup branches:"
            echo "$BACKUP_BRANCHES" | nl

            read -p "Enter branch number to switch to: " branch_num

            SELECTED_BRANCH=$(echo "$BACKUP_BRANCHES" | sed -n "${branch_num}p")

            if [ -n "$SELECTED_BRANCH" ]; then
                git checkout "$SELECTED_BRANCH"
                print_success "Switched to backup branch: $SELECTED_BRANCH"
            else
                print_error "Invalid branch selection."
            fi
        else
            print_warning "No backup branches found. Creating one now..."

            # Create backup of current state
            TIMESTAMP=$(date +%Y%m%d-%H%M%S)
            BACKUP_BRANCH="emergency-backup-$TIMESTAMP"
            git checkout -b "$BACKUP_BRANCH"
            git add .
            git commit -m "Emergency backup before rollback - $TIMESTAMP"

            print_success "Created backup branch: $BACKUP_BRANCH"
        fi
        ;;

    4)
        print_warning "This will reset to the last commit before any migration changes."
        read -p "Are you sure? This cannot be undone easily. (yes/N): " confirm

        if [ "$confirm" = "yes" ]; then
            print_status "Performing full reset..."

            # Find the last commit that doesn't have migration changes
            LAST_CLEAN_COMMIT=$(git log --oneline --grep="migration\|enzyme\|testing-library" --invert-grep -n 1 --pretty=format:"%H" || git rev-parse HEAD~1)

            if [ -n "$LAST_CLEAN_COMMIT" ]; then
                git reset --hard "$LAST_CLEAN_COMMIT"
                print_success "Reset to commit: $LAST_CLEAN_COMMIT"
            else
                print_error "Could not find a clean commit to reset to."
            fi
        else
            print_status "Full reset cancelled."
        fi
        ;;

    *)
        print_error "Invalid choice. Rollback cancelled."
        exit 1
        ;;
esac

# Post-rollback validation
echo
print_status "Running post-rollback validation..."

if npm test --silent 2>/dev/null; then
    print_success "Tests are passing after rollback."
else
    print_warning "Tests are failing. You may need to:"
    echo "  - Run 'npm install' to restore dependencies"
    echo "  - Check for missing Enzyme adapters"
    echo "  - Verify test file contents"
fi

# Show current status
echo
print_status "Current git status:"
git status --short

echo
print_success "Emergency rollback completed."
echo "If you need further help, check the migration documentation or run:"
echo "  npm run migrate:dashboard  # to see current migration status"
