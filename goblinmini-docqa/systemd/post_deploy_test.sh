#!/usr/bin/env bash
set -euo pipefail

# post_deploy_test.sh - lightweight post-deploy checks for Goblin DocQA
# Usage: sudo ./post_deploy_test.sh --venv /opt/goblinmini-docqa/venv --socket /run/goblinmini-docqa.sock [--model-name "ggml-small.bin"] [--run-model-load]

VENV_PY=/opt/goblinmini-docqa/venv/bin/python
SOCKET=/run/goblinmini-docqa.sock
MODEL_NAME=""
RUN_MODEL_LOAD=false

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --venv)
      VENV_PY="$2"/bin/python
      shift 2
      ;;
    --socket)
      SOCKET="$2"
      shift 2
      ;;
    --model-name)
      MODEL_NAME="$2"
      shift 2
      ;;
    --run-model-load)
      RUN_MODEL_LOAD=true
      shift
      ;;
    --help)
      echo "Usage: $0 --venv /path/to/venv --socket /run/goblinmini-docqa.sock [--model-name name] [--run-model-load]"
      exit 0
      ;;
    *)
      shift
      ;;
  esac
done

function check_unix_socket() {
  if [[ ! -S "$SOCKET" ]]; then
    echo "UNIX socket $SOCKET not present" 1>&2
    return 1
  fi
  return 0
}

function health_check() {
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --unix-socket "$SOCKET" http://localhost/health || true)
  echo "Health endpoint returned HTTP $HTTP_CODE"
  if [[ "$HTTP_CODE" != "200" ]]; then
    return 1
  fi
  return 0
}

function analyze_smoke() {
  # Basic test - small payload
  read -r CASERESP < <(curl -s -w "\n%{http_code}" --unix-socket "$SOCKET" -X POST -H "Content-Type: application/json" -d '{"text":"This is a small smoke test.","query":"Summarize"}' http://localhost/analyze/content || true)
  HTTP_CODE=$(echo "$CASERESP" | tail -n1)
  if [[ "$HTTP_CODE" != "200" ]] && [[ "$HTTP_CODE" != "202" ]]; then
    echo "Analyze content returned HTTP $HTTP_CODE" 1>&2
    return 1
  fi
  echo "Analyze content returned HTTP $HTTP_CODE"
  return 0
}

function run_llm_test() {
  if [[ ! -x "$VENV_PY" ]]; then
    echo "Venv python not found: $VENV_PY" 1>&2
    return 2
  fi
  if [[ -z "$MODEL_NAME" ]]; then
    echo "No model name specified; skipping model load test"
    return 0
  fi
  export MODEL_NAME
  $VENV_PY $(dirname "$0")/llm_test.py --model-name "$MODEL_NAME" --test-load
}

if ! check_unix_socket; then
  echo "Socket or service appears down" 1>&2
  exit 2
fi

echo "Running health check via socket:"
if ! health_check; then
  echo "Health check failed" 1>&2
  exit 3
fi

echo "Running analyze content smoke test:"
if ! analyze_smoke; then
  echo "Analyze content smoke test failed" 1>&2
  exit 4
fi

if [[ "$RUN_MODEL_LOAD" == true ]]; then
  echo "Running LLM model load test (this may be slow):"
  if ! run_llm_test; then
    echo "LLM model load test failed" 1>&2
    exit 5
  fi
fi

echo "All post-deploy tests passed"
exit 0
