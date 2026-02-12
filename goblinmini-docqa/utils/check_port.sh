#!/bin/bash
# Goblin Mini DocQA - Port Check Utility
# Prevents multiple instances from running on the same port

PORT=${1:-8000}

if command -v lsof >/dev/null 2>&1; then
    if lsof -i :$PORT >/dev/null 2>&1; then
        echo "❌ Port $PORT is already in use by another process."
        echo "   Use 'lsof -i :$PORT' to see what's using it."
        exit 1
    else
        echo "✅ Port $PORT is free and available."
        exit 0
    fi
else
    echo "⚠️  lsof command not found. Attempting alternative check..."
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
            echo "❌ Port $PORT is already in use (detected by netstat)."
            exit 1
        else
            echo "✅ Port $PORT appears to be free (checked via netstat)."
            exit 0
        fi
    else
        echo "⚠️  Neither lsof nor netstat available. Cannot verify port availability."
        echo "   Please install lsof or netstat for proper port checking."
        exit 2
    fi
fi
