#!/usr/bin/env bash
# Environment-specific Datadog setup for Goblin Assistant
# Usage: ./setup-env.sh [production|staging|development]

set -euo pipefail

ENV=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$ENV" in
  production)
    DD_SITE="datadoghq.com"
    DD_ENV="production"
    DD_HOSTNAME="goblin-prod-backend"
    DD_TAGS="env:production,service:goblin-assistant,component:backend,region:us-west-2"
    ;;
  staging)
    DD_SITE="datadoghq.com"
    DD_ENV="staging"
    DD_HOSTNAME="goblin-staging-backend"
    DD_TAGS="env:staging,service:goblin-assistant,component:backend,region:us-west-2"
    ;;
  development)
    DD_SITE="datadoghq.com"
    DD_ENV="development"
    DD_HOSTNAME="goblin-dev-backend"
    DD_TAGS="env:development,service:goblin-assistant,component:backend,region:local"
    ;;
  *)
    echo "Usage: $0 [production|staging|development]"
    exit 1
    ;;
esac

echo "Setting up Datadog for environment: $ENV"
echo "  Site: $DD_SITE"
echo "  Env: $DD_ENV"
echo "  Hostname: $DD_HOSTNAME"
echo "  Tags: $DD_TAGS"

# Export for docker-compose or scripts
export DD_SITE
export DD_ENV
export DD_HOSTNAME
export DD_TAGS

# Check for API key
if [ -z "${DD_API_KEY:-}" ]; then
  echo "ERROR: DD_API_KEY not set"
  echo "Please set it in your environment or .env file"
  exit 1
fi

# Save to .env file for docker-compose
cat > "$SCRIPT_DIR/.env.datadog" <<EOF
DD_API_KEY=${DD_API_KEY}
DD_SITE=${DD_SITE}
DD_ENV=${DD_ENV}
DD_HOSTNAME=${DD_HOSTNAME}
DD_TAGS=${DD_TAGS}
EOF

echo "✓ Environment configuration saved to .env.datadog"
echo ""
echo "Next steps:"
echo "  1. For Linux host: sudo ./setup-datadog-processes.sh"
echo "  2. For Docker: docker-compose -f docker-compose-datadog.yml --env-file .env.datadog up -d"
echo "  3. For K8s: Update k8s-datadog-agent.yaml with these values and kubectl apply"
