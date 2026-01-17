#!/bin/bash
# Goblin DocQA Monitoring Setup Script
# Sets up Prometheus, Grafana, and alerting for the DocQA service

set -euo pipefail

echo "🚀 Setting up Goblin DocQA monitoring..."

# Check if running as root for systemd setup
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Running as root - will install systemd services"
    INSTALL_SYSTEMD=true
else
    echo "ℹ️  Running as user - skipping systemd setup"
    INSTALL_SYSTEMD=false
fi

# Create monitoring directories
echo "📁 Creating monitoring directories..."
mkdir -p monitoring/{prometheus,grafana,loki}

# Setup Prometheus
echo "📊 Setting up Prometheus..."
cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerting_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # Add your alertmanager endpoints here

scrape_configs:
  - job_name: 'goblin-docqa'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 15s
    metrics_path: '/metrics'

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

# Copy alerting rules
cp prometheus/alerting_rules.yml monitoring/prometheus/

# Setup docker-compose for monitoring stack
cat > monitoring/docker-compose.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki:/etc/loki
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail:/etc/promtail
    command: -config.file=/etc/promtail/config.yml

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
EOF

# Setup Loki config
cat > monitoring/loki/local-config.yaml << 'EOF'
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
  - from: 2020-05-15
    store: boltdb
    object_store: filesystem
    schema: v11
    index:
      prefix: index_
      period: 168h

storage_config:
  boltdb:
    directory: /loki/index

  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
EOF

# Setup Promtail config
cat > monitoring/promtail/config.yml << 'EOF'
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
- job_name: systemd-goblin-docqa
  journal:
    json: false
    max_age: 12h
    labels:
      job: systemd-goblin-docqa
  relabel_configs:
    - source_labels: ['__journal__systemd_unit']
      target_label: 'unit'
      regex: 'goblin-docqa\.service'

- job_name: system
  static_configs:
  - targets:
      - localhost
    labels:
      job: varlogs
      __path__: /var/log/*log
EOF

# Setup systemd services if running as root
if [[ "$INSTALL_SYSTEMD" == "true" ]]; then
    echo "🔧 Installing systemd services..."

    # Install Prometheus service
    cat > /etc/systemd/system/prometheus.service << 'EOF'
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/var/lib/prometheus \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries \
    --storage.tsdb.retention.time=200h \
    --web.enable-lifecycle

[Install]
WantedBy=multi-user.target
EOF

    # Create prometheus user
    useradd --no-create-home --shell /bin/false prometheus || true
    mkdir -p /etc/prometheus /var/lib/prometheus
    chown prometheus:prometheus /etc/prometheus /var/lib/prometheus

    # Copy config
    cp monitoring/prometheus/prometheus.yml /etc/prometheus/
    cp monitoring/prometheus/alerting_rules.yml /etc/prometheus/

    systemctl daemon-reload
    systemctl enable prometheus
    echo "✅ Prometheus systemd service installed"
fi

echo "🎉 Monitoring setup complete!"
echo ""
echo "📊 Access points:"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana: http://localhost:3000 (admin/admin)"
echo "   Loki: http://localhost:3100"
echo ""
echo "🚀 To start monitoring stack:"
echo "   cd monitoring && docker-compose up -d"
echo ""
echo "📈 Check metrics at: http://localhost:8000/metrics"
