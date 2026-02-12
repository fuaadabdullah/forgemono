#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
TF_DIR="$ROOT_DIR/infra/gcp/llm"

ACTION=${CANARY_ACTION:-plan}
RUN_SMOKE_TESTS=${RUN_SMOKE_TESTS:-true}

if [[ -z "${GCP_PROJECT_ID:-}" ]]; then
  echo "GCP_PROJECT_ID is required"
  exit 1
fi

TF_VARS=(
  -var "project_id=${GCP_PROJECT_ID}"
)

if [[ -n "${GCP_REGION:-}" ]]; then
  TF_VARS+=( -var "region=${GCP_REGION}" )
fi

if [[ -n "${GCP_ZONE:-}" ]]; then
  TF_VARS+=( -var "zone=${GCP_ZONE}" )
fi

if [[ -n "${TF_VAR_google_credentials_json:-}" ]]; then
  TF_VARS+=( -var "google_credentials_json=${TF_VAR_google_credentials_json}" )
fi

terraform -chdir="$TF_DIR" init -input=false
terraform -chdir="$TF_DIR" fmt -check
terraform -chdir="$TF_DIR" validate
terraform -chdir="$TF_DIR" plan -input=false -out=tfplan "${TF_VARS[@]}"

if [[ "$ACTION" == "apply" ]]; then
  terraform -chdir="$TF_DIR" apply -input=false -auto-approve tfplan
fi

if [[ "$RUN_SMOKE_TESTS" == "true" ]]; then
  LLAMACPP_URL=${LLAMACPP_CANARY_URL:-}
  if [[ -z "$LLAMACPP_URL" ]]; then
    LLAMACPP_URL=$(terraform -chdir="$TF_DIR" output -raw llamacpp_url || true)
  fi

  if [[ -z "$LLAMACPP_URL" ]]; then
    echo "LLAMACPP_CANARY_URL not set and terraform output missing. Skipping smoke tests."
    exit 1
  fi

  python3 "$ROOT_DIR/tools/deploy/ci/test_llamacpp_server.py" \
    --server-url "$LLAMACPP_URL" \
    --auth-token "${LLM_CANARY_JWT:-}"
fi
