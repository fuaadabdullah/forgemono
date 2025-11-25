#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO_ROOT/tools/forge-lite-references.txt"

# Run the search script first if needed
bash "$REPO_ROOT/tools/find-forge-lite-references.sh"

if [ ! -s "$OUT" ]; then
  echo "No references found to remove."
  exit 0
fi

# For safety, print the list and create backups for all affected files
awk -F: '{print $1}' "$OUT" | sort -u | while read -r file; do
  echo "Inspecting $file"
  cp "$file" "$file.bak"
  # Conservative default: comment out lines containing 'apps/forge-lite' or 'forge-lite' in configuration files
  case "$file" in
    *.yml|*.yaml|*.md|*.txt|*.sh)
      awk '{ if (tolower($0) ~ /apps\/forge-lite|forge-lite/) { print "# " $0 } else { print $0 } }' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
      echo "Commented lines in $file (backup: $file.bak)"
      ;;
    *.json)
      # For JSON files, replace any "apps/forge-lite" with "" or remove entries conservatively
      # This is a soft removal: replace with null string
      python3 - <<'PY'
import json, sys
p='''$file'''
with open(p,'r',encoding='utf-8') as f:
    s=f.read()
ns=s.replace('"apps/forge-lite"','""').replace('"forge-lite"','""')
with open(p,'w',encoding='utf-8') as f:
    f.write(ns)
print('Updated json file', p)
PY
      ;;
    *)
      echo "Skipping file type for $file; please review manually."
      ;;
  esac
done

# Generate summary report
rg --hidden --no-ignore -n "forge-lite" "$REPO_ROOT" || true

echo "Safe-remove script completed. Review backups (.bak) for any files and restore if needed."
