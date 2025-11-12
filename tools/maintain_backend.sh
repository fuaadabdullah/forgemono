#!/usr/bin/env bash
# ForgeTM Backend Maintenance Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FORGE_TM_DIR="${REPO_ROOT}/ForgeTM"
BACKEND_DIR="${FORGE_TM_DIR}/apps/backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Database maintenance functions
db_backup() {
    log_info "Creating database backup..."

    cd "${BACKEND_DIR}"

    # Create backups directory if it doesn't exist
    mkdir -p backups

    # Generate backup filename with timestamp
    BACKUP_FILE="backups/forge_$(date +%Y%m%d_%H%M%S).db"

    # Copy database file
    if [ -f "forgetm.db" ]; then
        cp forgetm.db "${BACKUP_FILE}"
        log_success "Database backup created: ${BACKUP_FILE}"
    else
        log_warning "Database file not found, skipping backup"
    fi
}

db_migrate() {
    log_info "Running database migrations..."

    cd "${BACKEND_DIR}"
    source .venv/bin/activate

    # Create backup before migration
    db_backup

    # Run migrations
    PYTHONPATH=src uv run alembic upgrade head

    log_success "Database migrations completed"
}

db_reset() {
    log_warning "This will reset the database and delete all data!"
    read -p "Are you sure? (type 'yes' to confirm): " -r
    if [[ ! $REPLY =~ ^yes$ ]]; then
        log_info "Database reset cancelled"
        exit 0
    fi

    log_info "Resetting database..."

    cd "${BACKEND_DIR}"

    # Create backup before reset
    db_backup

    # Remove database file
    if [ -f "forgetm.db" ]; then
        rm forgetm.db
        log_success "Database file removed"
    fi

    # Run migrations to recreate tables
    source .venv/bin/activate
    PYTHONPATH=src uv run alembic upgrade head

    log_success "Database reset completed"
}

db_stats() {
    log_info "Database statistics..."

    cd "${BACKEND_DIR}"

    if [ ! -f "forgetm.db" ]; then
        log_warning "Database file not found"
        return
    fi

    source .venv/bin/activate

    # Run Python script to get database stats
    PYTHONPATH=src python3 -c "
import sqlite3
import os
from datetime import datetime

db_path = 'forgetm.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get table info
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table';\")
    tables = cursor.fetchall()

    print(f'Database: {db_path}')
    print(f'Size: {os.path.getsize(db_path)} bytes')
    print(f'Last modified: {datetime.fromtimestamp(os.path.getmtime(db_path))}')

    for table in tables:
        table_name = table[0]
        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
        count = cursor.fetchone()[0]
        print(f'Table {table_name}: {count} records')

    conn.close()
else:
    print('Database file not found')
"
}

# Cache and temporary files cleanup
cleanup_cache() {
    log_info "Cleaning up cache and temporary files..."

    cd "${BACKEND_DIR}"

    # Python cache
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true

    # Test cache
    rm -rf .pytest_cache .coverage htmlcov

    # MyPy cache
    rm -rf .mypy_cache

    # Ruff cache
    rm -rf .ruff_cache

    # Hypothesis cache
    rm -rf .hypothesis

    log_success "Cache cleanup completed"
}

cleanup_logs() {
    log_info "Cleaning up old log files..."

    cd "${BACKEND_DIR}"

    # Remove log files older than 30 days
    find . -name "*.log" -type f -mtime +30 -delete 2>/dev/null || true

    log_success "Log cleanup completed"
}

cleanup_backups() {
    log_info "Cleaning up old database backups..."

    cd "${BACKEND_DIR}"

    # Keep only last 10 backups
    if [ -d "backups" ]; then
        ls -t backups/*.db 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
        log_success "Old backups cleaned up (keeping last 10)"
    else
        log_info "No backups directory found"
    fi
}

# Health monitoring functions
check_services() {
    log_info "Checking service health..."

    local host="${1:-127.0.0.1}"
    local port="${2:-8000}"

    # Test health endpoint
    if curl -s "http://${host}:${port}/health" | grep -q '"status":"ok"'; then
        log_success "Backend service is healthy"
    else
        log_error "Backend service is not responding"
        return 1
    fi

    # Test database connectivity (via health endpoint)
    if curl -s "http://${host}:${port}/health" | grep -q '"database":"ok"'; then
        log_success "Database connection is healthy"
    else
        log_warning "Database health check not available in health endpoint"
    fi
}

check_resources() {
    log_info "Checking system resources..."

    # Check disk usage
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        log_error "Disk usage is high: ${DISK_USAGE}%"
    elif [ "$DISK_USAGE" -gt 75 ]; then
        log_warning "Disk usage is elevated: ${DISK_USAGE}%"
    else
        log_success "Disk usage is normal: ${DISK_USAGE}%"
    fi

    # Check memory usage
    MEM_USAGE=$(ps aux --no-headers -o pmem -C python3 | awk '{sum+=$1} END {print sum}')
    if [ -n "$MEM_USAGE" ] && [ "$(echo "$MEM_USAGE > 80" | bc -l)" -eq 1 ]; then
        log_warning "High memory usage by Python processes: ${MEM_USAGE}%"
    else
        log_success "Memory usage is normal"
    fi
}

# Performance monitoring
performance_report() {
    log_info "Generating performance report..."

    cd "${BACKEND_DIR}"
    source .venv/bin/activate

    # Run a simple load test
    log_info "Running basic load test..."

    # Simple concurrent requests test
    for i in {1..10}; do
        curl -s "http://127.0.0.1:8000/health" > /dev/null &
    done
    wait

    log_success "Load test completed"

    # Show running processes
    log_info "Running ForgeTM processes:"
    ps aux | grep -E "(uvicorn|celery|python)" | grep -v grep || log_info "No ForgeTM processes found"
}

# Main maintenance function
maintenance() {
    local command="$1"
    shift

    case "$command" in
        "db-backup")
            db_backup
            ;;
        "db-migrate")
            db_migrate
            ;;
        "db-reset")
            db_reset
            ;;
        "db-stats")
            db_stats
            ;;
        "cleanup-cache")
            cleanup_cache
            ;;
        "cleanup-logs")
            cleanup_logs
            ;;
        "cleanup-backups")
            cleanup_backups
            ;;
        "cleanup-all")
            cleanup_cache
            cleanup_logs
            cleanup_backups
            ;;
        "health-check")
            check_services "$@"
            ;;
        "resource-check")
            check_resources
            ;;
        "performance")
            performance_report
            ;;
        "full-check")
            check_services "$@"
            check_resources
            db_stats
            ;;
        *)
            log_error "Unknown maintenance command: $command"
            usage
            exit 1
            ;;
    esac
}

# Show usage
usage() {
    cat << EOF
ForgeTM Backend Maintenance Script

USAGE:
    $0 COMMAND [OPTIONS]

COMMANDS:
    Database Operations:
        db-backup           Create database backup
        db-migrate          Run database migrations
        db-reset            Reset database (WARNING: deletes all data)
        db-stats            Show database statistics

    Cleanup Operations:
        cleanup-cache       Clean Python cache files
        cleanup-logs        Remove old log files (>30 days)
        cleanup-backups     Remove old backups (keep last 10)
        cleanup-all         Run all cleanup operations

    Monitoring:
        health-check [HOST] [PORT]    Check service health (default: 127.0.0.1:8000)
        resource-check                Check system resources
        performance                   Generate performance report
        full-check                    Run all checks

EXAMPLES:
    $0 db-backup                    # Create database backup
    $0 cleanup-all                  # Clean everything
    $0 health-check 127.0.0.1 8000  # Check service health
    $0 full-check                   # Complete system check

EOF
}

# Main script
main() {
    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi

    local command="$1"
    shift

    case "$command" in
        -h|--help)
            usage
            exit 0
            ;;
        *)
            maintenance "$command" "$@"
            ;;
    esac
}

# Run main function with all arguments
main "$@"
