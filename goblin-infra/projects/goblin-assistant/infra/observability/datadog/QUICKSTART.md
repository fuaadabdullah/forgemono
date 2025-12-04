# Datadog Process Monitoring - Quick Reference

## 🚀 Quick Start

```bash
# 1. Install Datadog Agent
DD_API_KEY=<YOUR_KEY> DD_SITE="datadoghq.com" \
bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script_agent7.sh)"

# 2. Setup process monitoring
cd goblin-infra/projects/goblin-assistant/infra/observability/datadog
sudo ./setup-datadog-processes.sh

# 3. Verify
./verify-setup.sh
```

## 📊 View Data

- **Processes**: <https://app.datadoghq.com/process?tags=service%3Agoblin-assistant>
- **Monitors**: <https://app.datadoghq.com/monitors>
- **Dashboards**: <https://app.datadoghq.com/dashboard/lists>

## 🔍 Essential Queries

```python
# CPU usage by process
avg:system.processes.cpu.pct{service:goblin-assistant} by {process}

# Memory usage
sum:system.processes.mem.rss{service:goblin-assistant}

# I/O operations
sum:system.processes.io.read_bytes{service:goblin-assistant}.as_rate()

# Process count
count_nonzero(avg:system.processes.number{service:goblin-assistant})
```

## 🚨 Key Monitors

| Monitor | Threshold | Alert |
|---------|-----------|-------|
| High CPU | > 80% for 5 min | P2 |
| Memory Leak | > 2GB and increasing | P1 |
| File Descriptors | > 1000 | P2 |
| Process Crash | Uptime decreased | P1 |

## 🔧 Common Commands

```bash
# Check status
sudo datadog-agent status

# View logs
tail -f /var/log/datadog/agent.log

# Restart agent
sudo systemctl restart datadog-agent

# Test config
sudo datadog-agent configcheck

# Send diagnostic bundle
sudo datadog-agent flare
```

## ⚙️ Configuration Locations

```text
Main Config:         /etc/datadog-agent/datadog.yaml
System Probe:        /etc/datadog-agent/system-probe.yaml
Logs:                /var/log/datadog/
Docker Compose:      docker-compose-datadog.yml
Kubernetes:          k8s-datadog-agent.yaml
```

## 🐛 Troubleshooting

**No processes showing?**

```bash
# Check if enabled
grep -A5 "process_config:" /etc/datadog-agent/datadog.yaml
sudo systemctl restart datadog-agent
```

**No I/O stats?**

```bash
# Check system-probe
ps aux | grep system-probe
sudo systemctl restart datadog-agent
```

**API keys visible?**

```bash
# Enable scrubbing
sudo vi /etc/datadog-agent/datadog.yaml
# Set: scrub_args: true
sudo systemctl restart datadog-agent
```

## 📚 Resources

- [Full Documentation](./README.md)
- [Datadog Docs](https://docs.datadoghq.com/infrastructure/process/)
- [SLO Definitions](../../datadog/DATADOG_SLOS.md)

---
**Updated**: 2025-12-03
