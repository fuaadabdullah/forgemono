#!/usr/bin/env bash
set -e
INSTANCE_ID="$1"
# Fetch ephemeral secrets from CI-origin endpoint
curl -sS "https://ci.example.com/secrets?instance=$INSTANCE_ID" -o /tmp/secrets.json
# Write secrets to /etc/goblin/env (owner: root, mode 600)
jq -r 'to_entries|map("\(.key)=\(.value|tostring)")|.[]' /tmp/secrets.json > /etc/goblin/env
chmod 600 /etc/goblin/env
# Start docker compose with env file
cd /srv/goblin && docker compose --env-file /etc/goblin/env up -d
