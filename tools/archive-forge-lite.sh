#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$REPO_ROOT/apps/forge-lite"
ARCHIVE_DIR="$REPO_ROOT/archive/forge-lite"
PNPM_WS_FILE="$REPO_ROOT/pnpm-workspace.yaml"
PACKAGE_JSON="$REPO_ROOT/package.json"

if [ ! -d "$APP_DIR" ]; then
  echo "apps/forge-lite does not exist or is already archived"
  exit 0
fi

mkdir -p "$ARCHIVE_DIR"

echo "Moving apps/forge-lite to archive/forge-lite ..."
mv "$APP_DIR" "$ARCHIVE_DIR/"

echo "Updating pnpm-workspace.yaml to remove apps/forge-lite from workspace..."
if grep -q "apps/forge-lite" "$PNPM_WS_FILE"; then
  sed -i.bak "/apps\/forge-lite/ s/^/# /" "$PNPM_WS_FILE"
  echo "# updated: archived forge-lite" >> "$PNPM_WS_FILE"
fi

echo "Removing apps/forge-lite from package.json workspaces if present..."
if grep -q "apps/forge-lite" "$PACKAGE_JSON"; then
  python3 - <<'PY'
import json
p='''$PACKAGE_JSON'''
with open('$PACKAGE_JSON','r',encoding='utf-8') as f:
    data=json.load(f)
ws=data.get('workspaces',[])
new_ws=[w for w in ws if w!='apps/forge-lite']
if len(new_ws)!=len(ws):
    data['workspaces']=new_ws
    with open('$PACKAGE_JSON','w',encoding='utf-8') as f:
        json.dump(data,f,indent=2,ensure_ascii=False)
    print('package.json updated')
else:
    print('package.json had no apps/forge-lite entry')
PY
fi

echo "Archiving complete. Please run 'pnpm install' at repo root to refresh workspace state if needed."
