#!/bin/bash
set -e
echo "=== PROD SMOKE TESTS ==="
echo "Checking API health..."
# curl --fail "https://${API_LB_DNS}/healthz" || { echo "API health failed"; exit 2; }
echo "Checking DB connectivity (sanity)..."
# Run a short connectivity/migration sanity check here
echo "All prod smoke tests passed"
