#cloud-config
package_update: true
package_upgrade: true

packages:
  - docker.io
  - curl
  - jq

runcmd:
  # Enable and start Docker
  - systemctl enable docker
  - systemctl start docker

  # Fetch secrets from CI bootstrap server
  - |
    set -e
    echo "Fetching secrets for instance: ${INSTANCE_ID}"
    curl -sS "https://ci.yourcompany.com/secrets?instance=${INSTANCE_ID}" -o /tmp/secrets.json

    # Write secrets to secure env file
    jq -r 'to_entries|map("\(.key)=\(.value|tostring)")|.[]' /tmp/secrets.json > /etc/goblin/env
    chmod 600 /etc/goblin/env
    chown root:root /etc/goblin/env

    # Clean up temp file
    rm /tmp/secrets.json

  # Pull and run the Goblin Assistant container
  - docker run -d --name goblin-assistant --env-file /etc/goblin/env -p 80:8000 your-registry/goblin-assistant:latest

  # Setup basic monitoring
  - |
    cat > /etc/systemd/system/goblin-healthcheck.service << 'EOF'
    [Unit]
    Description=Goblin Health Check
    After=docker.service

    [Service]
    Type=simple
    ExecStart=/bin/bash -c 'while true; do curl -f http://localhost/health || exit 1; sleep 30; done'
    Restart=always

    [Install]
    WantedBy=multi-user.target
    EOF

  - systemctl enable goblin-healthcheck
  - systemctl start goblin-healthcheck
