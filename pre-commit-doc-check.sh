#!/bin/bash
# Git pre-commit hook for documentation quality checks
# Install: cp pre-commit-doc-check.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

set -e

echo "🔍 Running documentation quality checks..."

# Check if doc_quality_check.py exists
if [ ! -f "tools/doc-quality/doc_quality_check.py" ]; then
    echo "❌ doc_quality_check.py not found. Skipping quality check."
    exit 0
fi

# Get staged documentation files
STAGED_DOCS=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(md|txt|rst|adoc)$' || true)

if [ -z "$STAGED_DOCS" ]; then
    echo "ℹ️  No documentation files staged for commit. Skipping quality check."
    exit 0
fi

echo "📄 Checking staged documentation files:"
echo "$STAGED_DOCS" | sed 's/^/  • /'
echo

# Run quality check on staged files
echo "Running quality analysis..."
# Ensure dependencies for doc-quality are installed (local env)
python3 -m pip install -qq -r tools/doc-quality/requirements.txt || true
python3 -m pip install -qq -r tools/raptor-mini/requirements.txt || true
# Respect DOC_QUALITY_SOFT_FALLBACK env var
SOFT_FALLBACK_FLAG=""
if [ "${DOC_QUALITY_SOFT_FALLBACK,,}" = "true" ]; then
    SOFT_FALLBACK_FLAG="--soft-fallback"
fi
if python3 tools/doc-quality/doc_quality_check.py --ci --mode phi_only --min-score 70 --quiet $SOFT_FALLBACK_FLAG $STAGED_DOCS; then
    echo "✅ All staged documentation passed quality checks!"
else
    echo "❌ Quality check failed. Please fix the issues before committing."
    echo
    echo "💡 To see detailed results, run:"
    echo "   python3 tools/doc-quality/doc_quality_check.py $STAGED_DOCS"
    echo
    echo "💡 To bypass this check (not recommended), use:"
    echo "   git commit --no-verify"
    exit 1
fi
