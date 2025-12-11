#!/bin/bash
# Weekly doc maintenance script
# Run this every Monday: ./scripts/weekly_doc_maintenance.sh

echo "🧹 Starting weekly doc maintenance..."

# 1. Scan for issues
echo "📄 Scanning docs for issues..."
python3 scripts/goblin_docs.py scan

# 2. Archive stale docs (older than 90 days)
echo "📦 Archiving docs older than 90 days..."
find docs/*.md -mtime +90 -exec mv {} docs/archive/ \; 2>/dev/null && echo "✅ Stale docs archived" || echo "ℹ️  No stale docs found"

# 3. Quick-check most recent 3 docs
echo "🔍 Checking most recent 3 docs..."
ls -t docs/*.md | head -3 | xargs -I {} sh -c 'echo "Checking: {}"; python3 scripts/goblin_docs.py check "{}"'

echo "✅ Weekly maintenance complete!"
