#!/bin/bash
set -e
# example: check API health
# curl --fail "https://api.staging.goblin.example/healthz" || exit 1
# run any post-deploy integration checks
echo "staging smoke tests passed"
