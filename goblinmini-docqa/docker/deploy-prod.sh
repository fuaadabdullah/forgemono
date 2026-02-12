#!/usr/bin/env bash
set -euo pipefail

# Docker-based production deploy script (for a Docker host)
# This script does not replace a full orchestration system but provides an easy
# and reproducible method for running the app on a single Docker host.

COMPOSE_FILE="docker/docker-compose.yml"
ENV_FILE=".env"
PROJECT_NAME="goblinmini"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Docker compose file not found: $COMPOSE_FILE" 1>&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Environment file not found: $ENV_FILE" 1>&2
  exit 1
fi

echo "Building Docker images and deploying stack using docker compose..."
# Build and run with resource caps already defined in the compose file
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" pull || true
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" build --pull
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" up -d --remove-orphans

echo "Result: docker compose status"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" ps

echo "To view logs: docker compose -f $COMPOSE_FILE --env-file $ENV_FILE -p $PROJECT_NAME logs -f"
