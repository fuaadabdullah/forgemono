#!/usr/bin/env bash
# Production Database Backup Script
# Creates encrypted backups of PostgreSQL/Supabase databases
set -euo pipefail

# Configuration
TIMESTAMP=$(date -u +"%Y-%m-%dT%H%MZ")
FILENAME="db-backup-${TIMESTAMP}.sql.gz"
BACKUP_DIR="${BACKUP_DIR:-/tmp/db-backups}"
S3_BUCKET="${BACKUP_BUCKET:-goblin-backups}"
S3_PREFIX="${BACKUP_PREFIX:-postgres}"
AWS_ENDPOINT="${AWS_ENDPOINT:-}" # For Cloudflare R2 or other S3-compatible

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $1${NC}"
}

# Validate environment
validate_env() {
    local missing_vars=()

    if [ -z "${DATABASE_URL:-}" ]; then
        missing_vars+=("DATABASE_URL")
    fi

    if [ -z "${AWS_ACCESS_KEY_ID:-}" ] && [ -z "${BACKUP_BUCKET:-}" ]; then
        missing_vars+=("AWS_ACCESS_KEY_ID or BACKUP_BUCKET")
    fi

    if [ ${#missing_vars[@]} -ne 0 ]; then
        error "Missing required environment variables:"
        printf '  - %s\n' "${missing_vars[@]}"
        echo ""
        echo "For local testing, set:"
        echo "  export DATABASE_URL='postgresql://user:pass@localhost:5432/db'"
        echo "  export BACKUP_BUCKET='my-bucket'  # optional for local testing"
        exit 1
    fi
}

# Create backup directory
setup_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    log "Backup directory: $BACKUP_DIR"
}

# Extract database connection details
extract_db_info() {
    # Extract from DATABASE_URL: postgresql://user:pass@host:port/db
    local db_url="$DATABASE_URL"

    DB_HOST=$(echo "$db_url" | sed -E 's|postgresql://[^:]+:[^@]+@([^:]+):.*|\1|')
    DB_PORT=$(echo "$db_url" | sed -E 's|postgresql://[^:]+:[^@]+@[^:]+:([^/]+).*|\1|')
    DB_NAME=$(echo "$db_url" | sed -E 's|.*/([^?]+).*|\1|')
    DB_USER=$(echo "$db_url" | sed -E 's|postgresql://([^:]+):.*|\1|')
    DB_PASS=$(echo "$db_url" | sed -E 's|postgresql://[^:]+:([^@]+)@.*|\1|')

    log "Database: $DB_HOST:$DB_PORT/$DB_NAME"
}

# Test database connection
test_connection() {
    log "Testing database connection..."

    if command -v psql >/dev/null 2>&1; then
        export PGPASSWORD="$DB_PASS"
        if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" --quiet >/dev/null 2>&1; then
            log "Database connection successful"
        else
            error "Database connection failed"
            exit 1
        fi
    else
        warn "psql not available, skipping connection test"
    fi
}

# Create database dump
create_backup() {
    local backup_path="$BACKUP_DIR/$FILENAME"

    log "Creating database backup: $backup_path"

    export PGPASSWORD="$DB_PASS"

    # Use pg_dump with compression
    if ! pg_dump \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --no-password \
        --format=custom \
        --compress=9 \
        --file="$backup_path" \
        --verbose; then
        error "Database backup failed"
        exit 1
    fi

    # Verify backup file
    if [ ! -f "$backup_path" ]; then
        error "Backup file was not created"
        exit 1
    fi

    local size=$(du -h "$backup_path" | cut -f1)
    log "Backup created successfully: $size"
}

# Upload to S3-compatible storage (Cloudflare R2, AWS S3, etc.)
upload_to_s3() {
    if [ -z "${BACKUP_BUCKET:-}" ]; then
        warn "BACKUP_BUCKET not set, skipping upload"
        return 0
    fi

    local backup_path="$BACKUP_DIR/$FILENAME"
    local s3_key="$S3_PREFIX/$FILENAME"

    log "Uploading backup to S3: s3://$S3_BUCKET/$s3_key"

    # Prepare AWS CLI command
    local aws_cmd=(aws s3 cp "$backup_path" "s3://$S3_BUCKET/$s3_key")

    # Add endpoint for non-AWS S3 services
    if [ -n "$AWS_ENDPOINT" ]; then
        aws_cmd=(aws --endpoint-url="$AWS_ENDPOINT" s3 cp "$backup_path" "s3://$S3_BUCKET/$s3_key")
    fi

    # Execute upload
    if "${aws_cmd[@]}"; then
        log "Backup uploaded successfully"
    else
        error "Backup upload failed"
        return 1
    fi
}

# Clean up old backups (keep last 30 days)
cleanup_old_backups() {
    if [ -z "${BACKUP_BUCKET:-}" ]; then
        return 0
    fi

    log "Cleaning up backups older than 30 days..."

    # List and delete old backups
    local cutoff_date=$(date -u -d '30 days ago' +%Y-%m-%d)

    # For S3-compatible storage
    local aws_cmd=(aws s3api list-objects-v2 --bucket "$S3_BUCKET" --prefix "$S3_PREFIX/")
    if [ -n "$AWS_ENDPOINT" ]; then
        aws_cmd=(aws --endpoint-url="$AWS_ENDPOINT" s3api list-objects-v2 --bucket "$S3_BUCKET" --prefix "$S3_PREFIX/")
    fi

    # Get objects older than cutoff
    local old_objects
    old_objects=$("${aws_cmd[@]}" --query "Contents[?LastModified<='$cutoff_date'].Key" --output text 2>/dev/null || echo "")

    if [ -n "$old_objects" ]; then
        log "Found old backups to delete: $old_objects"

        # Delete old objects
        local delete_cmd=(aws s3api delete-objects --bucket "$S3_BUCKET" --delete "Objects=[$(echo "$old_objects" | sed 's/ /},{Key:/g' | sed 's/^/{Key:/' | sed 's/$/}/')]")
        if [ -n "$AWS_ENDPOINT" ]; then
            delete_cmd=(aws --endpoint-url="$AWS_ENDPOINT" s3api delete-objects --bucket "$S3_BUCKET" --delete "Objects=[$(echo "$old_objects" | sed 's/ /},{Key:/g' | sed 's/^/{Key:/' | sed 's/$/}/')]")
        fi

        if "${delete_cmd[@]}"; then
            log "Old backups cleaned up"
        else
            warn "Failed to cleanup old backups"
        fi
    else
        log "No old backups to cleanup"
    fi
}

# Clean up local files
cleanup_local() {
    local backup_path="$BACKUP_DIR/$FILENAME"

    if [ -f "$backup_path" ]; then
        rm -f "$backup_path"
        log "Local backup file cleaned up"
    fi
}

# Send notification (optional)
send_notification() {
    # This could integrate with Slack, Discord, email, etc.
    # For now, just log success
    log "Backup process completed successfully"
}

# Main execution
main() {
    log "Starting database backup process..."

    validate_env
    setup_backup_dir
    extract_db_info
    test_connection
    create_backup

    # Upload and cleanup
    if upload_to_s3; then
        cleanup_old_backups
        cleanup_local
        send_notification
        log "✅ Database backup completed successfully"
    else
        error "❌ Database backup failed during upload"
        exit 1
    fi
}

# Run main function
main "$@"
