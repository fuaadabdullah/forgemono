#!/usr/bin/env bash
set -euo pipefail

echo "Starting data consolidation script (scripts/consolidate-data.sh)"
echo "This will reorganize local data into /data. Backups will be created.
"

read -p "Make sure you have backups. Continue? (y/N): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted by user. No changes made."
  exit 0
fi

mkdir -p data/vector/chroma
mkdir -p data/vector/staging
mkdir -p data/sqlite/apps
mkdir -p data/sqlite/shared
mkdir -p data/logs
mkdir -p data/backups

safe_move() {
  src="$1"
  dst="$2"
  if [ -e "$src" ]; then
    echo "Moving: $src -> $dst"
    mkdir -p "$(dirname "$dst")"
    cp -r "$src" "$dst" 2>/dev/null || true
    mv "$src" "${src}.moved-$(date +%Y%m%d)" 2>/dev/null || true
  fi
}

# Move Chromadb
if [ -f chroma_db/chroma.sqlite3 ]; then
  safe_move "chroma_db/chroma.sqlite3" "data/vector/chroma/chroma.sqlite3"
fi

# Move any vector_db contents
if [ -d vector_db ] && [ "$(ls -A vector_db 2>/dev/null)" ]; then
  safe_move "vector_db" "data/vector/staging/"
  rmdir vector_db 2>/dev/null || true
fi

echo "Collecting SQLite files from apps directory..."
find apps/ -name "*.db" -type f | while read -r db_file; do
  app_name=$(echo "$db_file" | cut -d'/' -f2)
  filename=$(basename "$db_file")
  mkdir -p "data/sqlite/apps/$app_name"
  safe_move "$db_file" "data/sqlite/apps/$app_name/$filename"
done

# Move logs
if [ -d "logs" ]; then
  safe_move "logs" "data/logs/"
  rmdir logs 2>/dev/null || true
fi

echo "Data consolidation complete."
echo "Verify your applications and update configuration files as needed. Backups are suffixed with .moved-$(date +%Y%m%d)"

exit 0
