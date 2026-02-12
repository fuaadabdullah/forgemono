#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[sanity_checks] running sandbox sanity checks"

# Check if required tools are installed
command -v docker >/dev/null 2>&1 || { echo "[sanity_checks] error: docker is not installed"; exit 1; }
command -v cosign >/dev/null 2>&1 || { echo "[sanity_checks] warning: cosign not available, signature verification will be skipped"; }

# Check Docker daemon
if ! docker info >/dev/null 2>&1; then
    echo "[sanity_checks] error: Docker daemon not running"
    exit 1
fi

echo "[sanity_checks] Docker daemon is running"

# Check if sandbox image exists
SANDBOX_IMAGE="${SANDBOX_IMAGE:-goblin/sandbox:latest}"
if ! docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$SANDBOX_IMAGE"; then
    echo "[sanity_checks] warning: sandbox image $SANDBOX_IMAGE not found locally"
    echo "[sanity_checks] attempting to pull image..."
    if docker pull "$SANDBOX_IMAGE" >/dev/null 2>&1; then
        echo "[sanity_checks] successfully pulled $SANDBOX_IMAGE"
    else
        echo "[sanity_checks] error: failed to pull $SANDBOX_IMAGE"
        exit 1
    fi
else
    echo "[sanity_checks] sandbox image $SANDBOX_IMAGE is available"
fi

# Verify image signature if cosign is available and SANDBOX_VERIFY_SIGNATURES=cosign
if command -v cosign >/dev/null 2>&1 && [[ "${SANDBOX_VERIFY_SIGNATURES:-}" == "cosign" ]]; then
    echo "[sanity_checks] verifying image signature with cosign"
    if cosign verify "$SANDBOX_IMAGE" >/dev/null 2>&1; then
        echo "[sanity_checks] image signature verified"
    else
        echo "[sanity_checks] error: image signature verification failed"
        exit 1
    fi
else
    echo "[sanity_checks] skipping signature verification"
fi

# Check Docker security settings
echo "[sanity_checks] checking Docker security settings"

# Check if running in rootless mode
if docker info --format json | jq -e '.SecurityOptions[] | select(. | contains("rootless"))' >/dev/null 2>&1; then
    echo "[sanity_checks] Docker is running in rootless mode"
else
    echo "[sanity_checks] warning: Docker not running in rootless mode"
fi

# Check user namespaces
if docker info --format json | jq -e '.SecurityOptions[] | select(. | contains("userns"))' >/dev/null 2>&1; then
    echo "[sanity_checks] user namespaces enabled"
else
    echo "[sanity_checks] warning: user namespaces not enabled"
fi

# Check seccomp
if docker info --format json | jq -e '.SecurityOptions[] | select(. | contains("seccomp"))' >/dev/null 2>&1; then
    echo "[sanity_checks] seccomp enabled"
else
    echo "[sanity_checks] warning: seccomp not enabled"
fi

# Test basic sandbox functionality
echo "[sanity_checks] testing basic sandbox functionality"

cd "${REPO_ROOT}/goblin-assistant/api/fastapi"

# Run the test suite
if python -m pytest test_sandbox_runner.py -v >/dev/null 2>&1; then
    echo "[sanity_checks] sandbox tests passed"
else
    echo "[sanity_checks] error: sandbox tests failed"
    exit 1
fi

# Test a simple sandbox execution
TEST_CODE='print("Hello from sandbox!")'
if python -c "
from sandbox_runner import run_untrusted
exit_code, stdout, stderr, timed_out = run_untrusted('$TEST_CODE', timeout_seconds=5)
print(f'Exit code: {exit_code}')
print(f'Stdout: {stdout.strip()}')
assert exit_code == 0
assert 'Hello from sandbox!' in stdout
print('Basic sandbox execution test passed')
" >/dev/null 2>&1; then
    echo "[sanity_checks] basic sandbox execution test passed"
else
    echo "[sanity_checks] error: basic sandbox execution test failed"
    exit 1
fi

echo "[sanity_checks] all sanity checks passed"
