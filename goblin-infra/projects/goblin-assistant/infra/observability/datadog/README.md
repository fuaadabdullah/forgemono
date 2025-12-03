# Datadog Process Monitoring Setup for Goblin Assistant

Complete guide for setting up Datadog process monitoring with I/O stats for the Goblin Assistant backend.

## Overview

This configuration enables comprehensive process monitoring including:
- ✅ Process discovery and metrics collection
- ✅ I/O and open files statistics (via system-probe)
- ✅ Sensitive argument scrubbing
- ✅ Optimized collection (runs in core agent for v7.53.0+)
- ✅ Container-aware monitoring
- ✅ APM integration

## Prerequisites

1. **Datadog Account**: Active account with API key
2. **Datadog Agent**: Version 7.53.0+ (recommended 7.65.0+ for optimized collection)
3. **System Access**: Root/sudo privileges for installation
4. **Environment**: Linux (macOS/Windows monitoring differs)

## Installation Methods

### Method 1: Automated Setup (Linux Hosts)

**Quickest way to get started:**

```bash
# 1. Install Datadog Agent (if not already installed)
DD_API_KEY=<YOUR_API_KEY> \
DD_SITE="datadoghq.com" \
bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script_agent7.sh)"

# 2. Run our setup script
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/observability/datadog
sudo ./setup-datadog-processes.sh
```

The script will:
- ✅ Detect agent version and configure optimally
- ✅ Enable system-probe for I/O stats
- ✅ Configure sensitive data scrubbing
- ✅ Restart agent and verify setup

### Method 2: Docker Compose

**For containerized deployments:**

```bash
# 1. Set environment variables
export DD_API_KEY="your_api_key_here"
export DD_SITE="datadoghq.com"
export DD_ENV="production"
export DD_HOSTNAME="goblin-backend-01"

# 2. Start Datadog agent
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/observability/datadog
docker-compose -f docker-compose-datadog.yml up -d

# 3. Verify
docker logs datadog-agent
```

**Requirements:**
- Docker Engine 20.10+
- Host PID mode access
- Required kernel capabilities

### Method 3: Kubernetes

**For K8s deployments:**

```bash
# 1. Create namespace
kubectl create namespace goblin-assistant

# 2. Add API key to secret
kubectl create secret generic datadog-secret \
  --from-literal=api-key=<YOUR_API_KEY> \
  -n goblin-assistant

# 3. Deploy DaemonSet
kubectl apply -f k8s-datadog-agent.yaml

# 4. Verify
kubectl get pods -n goblin-assistant -l app=datadog-agent
kubectl logs -n goblin-assistant -l app=datadog-agent --tail=50
```

**Alternative: Helm Chart** (Recommended for production)

```bash
helm repo add datadog https://helm.datadoghq.com
helm repo update

helm install datadog-agent datadog/datadog \
  --set datadog.apiKey=<YOUR_API_KEY> \
  --set datadog.site=datadoghq.com \
  --set datadog.processAgent.enabled=true \
  --set datadog.processAgent.runInCoreAgent=true \
  --set datadog.systemProbe.enabled=true \
  --set datadog.systemProbe.enableProcessCollection=true \
  --namespace goblin-assistant
```

## Configuration Files

### 1. `datadog-agent.yaml`
Main agent configuration with:
- API key and site settings
- Tags for filtering (env, service, component)
- Process collection settings
- Sensitive word scrubbing
- Container discovery

### 2. `system-probe.yaml`
System probe configuration for:
- I/O statistics
- Open files tracking
- Network monitoring (optional)

### 3. Docker/K8s Manifests
Production-ready deployment configs

## Verification

### Check Agent Status

```bash
# Linux host
sudo datadog-agent status

# Look for:
# Process Agent (check 'process' and 'rtprocess')
# ==============================
#   Instance ID: process [OK]
#   Configuration Source: file:/etc/datadog-agent/datadog.yaml
#   Total Runs: 12
#   Process Count: 245
#   Container Count: 8
```

### View Process Logs

```bash
# Core agent logs (optimized mode)
tail -f /var/log/datadog/agent.log | grep process

# Process agent logs (non-optimized mode)
tail -f /var/log/datadog/process-agent.log

# System probe logs
tail -f /var/log/datadog/system-probe.log
```

### Check Running Processes

```bash
# Optimized mode (v7.53.0+)
ps aux | grep datadog
# Should see: datadog-agent (core) and system-probe
# Should NOT see: process-agent running separately

# Non-optimized mode
ps aux | grep datadog
# Should see: datadog-agent, process-agent, system-probe
```

### Datadog UI

1. **Process Explorer**: https://app.datadoghq.com/process
   - Filter by `service:goblin-assistant`
   - View Python/Gunicorn processes
   - Check CPU, memory, I/O stats

2. **Infrastructure Map**: https://app.datadoghq.com/infrastructure/map
   - Visualize host and container relationships
   - See process-level details

3. **Live Containers**: https://app.datadoghq.com/containers
   - View containerized processes
   - Inspect container metrics

## Features Enabled

### 1. Process Discovery
Automatically discovers and monitors:
- Python processes (`python`, `gunicorn`, `uvicorn`)
- System processes
- Container processes
- Child processes

### 2. Process Metrics
Collects:
- **CPU**: Usage %, user time, system time
- **Memory**: RSS, VMS, shared memory
- **I/O**: Read/write bytes, operations count
- **Network**: Connections, bytes sent/received
- **Files**: Open file descriptors

### 3. Sensitive Data Scrubbing
Automatically hides from command lines:
- API keys (`api_key`, `apikey`, `*_key`)
- Tokens (`token`, `auth_token`, `bearer`, `jwt`)
- Passwords (`password`, `passwd`)
- Secrets (`secret`, `*_secret`)
- Credentials

**Example:**
```
Before: python app.py --api-key=sk_live_12345 --debug
After:  python app.py --api-key=****** --debug
```

### 4. Container Tagging
Processes tagged with:
- `container_name`
- `image_name`
- `kube_namespace` (K8s)
- `pod_name` (K8s)
- `service`, `env`, `version` (from labels)

## Querying Process Data

### Datadog Query Language

```python
# Average CPU by service
avg:system.processes.cpu.pct{service:goblin-assistant} by {process}

# Memory usage trend
sum:system.processes.mem.rss{service:goblin-assistant}

# I/O operations
sum:system.processes.io.read_bytes{service:goblin-assistant}.as_rate()

# Open files count
avg:system.processes.open_file_descriptors{service:goblin-assistant}

# Process count
count_nonzero(avg:system.processes.number{service:goblin-assistant})
```

### API Query Example

```bash
curl -X GET "https://api.datadoghq.com/api/v2/processes" \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DD_APP_KEY}" \
  -d 'tags=service:goblin-assistant'
```

## Monitoring & Alerts

### Recommended Monitors

#### 1. High CPU Usage
```yaml
Name: "[Goblin Assistant] High Process CPU"
Query: avg(last_5m):avg:system.processes.cpu.pct{service:goblin-assistant,process:python} by {host} > 80
Alert: CPU usage > 80% for 5 minutes
```

#### 2. Memory Leak Detection
```yaml
Name: "[Goblin Assistant] Memory Leak"
Query: avg(last_30m):avg:system.processes.mem.rss{service:goblin-assistant,process:python} by {host} > 2000000000
Alert: Memory > 2GB and increasing
```

#### 3. File Descriptor Exhaustion
```yaml
Name: "[Goblin Assistant] File Descriptors High"
Query: avg(last_5m):avg:system.processes.open_file_descriptors{service:goblin-assistant} by {host} > 1000
Alert: Open files > 1000
```

#### 4. Process Crash Detection
```yaml
Name: "[Goblin Assistant] Process Restart"
Query: change(avg(last_5m),last_5m):avg:system.processes.uptime{service:goblin-assistant,process:gunicorn} by {host} < -60
Alert: Process restarted (uptime decreased)
```

### Create Monitors

```bash
# Via UI
https://app.datadoghq.com/monitors/create/metric

# Via API
curl -X POST "https://api.datadoghq.com/api/v1/monitor" \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DD_APP_KEY}" \
  -d '{
    "type": "metric alert",
    "query": "avg(last_5m):avg:system.processes.cpu.pct{service:goblin-assistant} > 80",
    "name": "[Goblin Assistant] High CPU",
    "message": "CPU usage is above 80% @slack-ops",
    "tags": ["service:goblin-assistant"]
  }'
```

## Dashboards

### Pre-built Dashboard

Import the Goblin Assistant process dashboard:

```json
{
  "title": "Goblin Assistant - Process Monitoring",
  "widgets": [
    {
      "definition": {
        "type": "timeseries",
        "requests": [
          {
            "q": "avg:system.processes.cpu.pct{service:goblin-assistant} by {process}",
            "display_type": "line"
          }
        ],
        "title": "CPU Usage by Process"
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "requests": [
          {
            "q": "avg:system.processes.mem.rss{service:goblin-assistant} by {process}",
            "display_type": "area"
          }
        ],
        "title": "Memory Usage (RSS)"
      }
    },
    {
      "definition": {
        "type": "toplist",
        "requests": [
          {
            "q": "top(avg:system.processes.io.write_bytes{service:goblin-assistant} by {process}.as_rate(), 10, 'mean', 'desc')"
          }
        ],
        "title": "Top I/O Processes"
      }
    }
  ]
}
```

## Troubleshooting

### Issue: Process Agent Not Starting

**Symptoms:**
- No processes visible in UI
- Logs show: "process-agent is not enabled, exiting"

**Solutions:**
```bash
# 1. Check config
grep -A5 "process_config:" /etc/datadog-agent/datadog.yaml

# 2. Ensure enabled
sudo sed -i 's/# process_config:/process_config:/' /etc/datadog-agent/datadog.yaml
sudo sed -i '/process_config:/a\  enabled: true' /etc/datadog-agent/datadog.yaml

# 3. Restart
sudo systemctl restart datadog-agent
```

### Issue: No I/O Stats

**Symptoms:**
- Process CPU/memory visible
- No I/O metrics

**Solutions:**
```bash
# 1. Check system-probe running
ps aux | grep system-probe

# 2. Check permissions
sudo chown dd-agent:dd-agent /etc/datadog-agent/system-probe.yaml
sudo chmod 0640 /etc/datadog-agent/system-probe.yaml

# 3. Enable in config
grep "process_config" /etc/datadog-agent/system-probe.yaml

# 4. Restart
sudo systemctl restart datadog-agent
```

### Issue: Sensitive Data Visible

**Symptoms:**
- API keys visible in process arguments

**Solutions:**
```bash
# Add custom words
sudo vi /etc/datadog-agent/datadog.yaml

# Add under process_config:
process_config:
  enabled: true
  scrub_args: true
  custom_sensitive_words:
    - 'your_custom_pattern'
    - '*api*key*'

# Or strip all args
process_config:
  strip_proc_arguments: true

sudo systemctl restart datadog-agent
```

### Issue: High Agent CPU Usage

**Symptoms:**
- datadog-agent consuming high CPU

**Solutions:**
```bash
# 1. Use optimized mode (if v7.53.0+)
echo "process_config:
  run_in_core_agent: true" | sudo tee -a /etc/datadog-agent/datadog.yaml

# 2. Reduce collection frequency
echo "process_config:
  intervals:
    container: 10
    process: 10" | sudo tee -a /etc/datadog-agent/datadog.yaml

# 3. Filter processes
echo "process_config:
  enabled: true
  process_dd_url: https://process.datadoghq.com
  intervals:
    container: 10
    process: 10
  blacklist_patterns:
    - ^/sbin/
    - ^/usr/sbin/" | sudo tee -a /etc/datadog-agent/datadog.yaml

sudo systemctl restart datadog-agent
```

## Cost Optimization

### Reduce Data Volume

1. **Filter Processes** - Only monitor relevant processes:
```yaml
process_config:
  blacklist_patterns:
    - ^/sbin/
    - ^/usr/sbin/
    - .*kernel.*
```

2. **Adjust Collection Intervals**:
```yaml
process_config:
  intervals:
    container: 30  # Default: 10s
    process: 30    # Default: 10s
```

3. **Disable Unnecessary Features**:
```yaml
# If not using NPM
network_config:
  enabled: false

# If not using USM
service_monitoring_config:
  enabled: false
```

## Integration with Goblin Assistant

### Tag Strategy

Ensure processes tagged for filtering:
```yaml
tags:
  - env:production
  - service:goblin-assistant
  - component:backend
  - stack:fastapi
  - project:forge-monorepo
```

### Query Examples

```python
# FastAPI worker processes
avg:system.processes.cpu.pct{service:goblin-assistant,process:uvicorn}

# Gunicorn master process
avg:system.processes.mem.rss{service:goblin-assistant,process:gunicorn}

# All Python processes
sum:system.processes.number{service:goblin-assistant,cmd:python}
```

### APM Integration

Link process metrics with APM traces:
```python
from ddtrace import tracer

# In your FastAPI app
@app.middleware("http")
async def add_process_tags(request, call_next):
    span = tracer.current_span()
    if span:
        span.set_tag("process.id", os.getpid())
        span.set_tag("process.name", "goblin-assistant")
    return await call_next(request)
```

## Security Considerations

1. **API Key Storage**:
   - Use secrets management (AWS Secrets Manager, Vault)
   - Never commit keys to Git
   - Rotate regularly

2. **Network Access**:
   - Agent connects outbound only (443/tcp)
   - No inbound connections required
   - Can use proxy if needed

3. **Data Privacy**:
   - Scrub all sensitive arguments
   - Review process names for PII
   - Use `strip_proc_arguments: true` for maximum privacy

4. **Permissions**:
   - Agent runs as `dd-agent` user
   - System-probe requires elevated privileges
   - Review CAP_* requirements for containers

## Performance Impact

**Resource Usage:**
- CPU: 0.5-2% (optimized mode)
- Memory: 200-500 MB
- Network: ~50 KB/s per 1000 processes
- Disk: Minimal (logs only)

**Collection Impact:**
- Process data collected every 10s (default)
- System-probe adds <1% overhead
- Container overhead: <0.5%

## Maintenance

### Regular Tasks

1. **Weekly:**
   - Review process metrics for anomalies
   - Check for new processes to monitor/exclude

2. **Monthly:**
   - Update agent to latest version
   - Review and optimize tag strategy
   - Audit sensitive data scrubbing

3. **Quarterly:**
   - Review monitor thresholds
   - Optimize dashboards
   - Assess cost vs value

### Upgrade Agent

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install --only-upgrade datadog-agent

# RHEL/CentOS
sudo yum update datadog-agent

# Verify
datadog-agent version
```

## Resources

- **Datadog Docs**: https://docs.datadoghq.com/infrastructure/process/
- **Process Agent**: https://docs.datadoghq.com/infrastructure/process/
- **System Probe**: https://docs.datadoghq.com/infrastructure/process/#io-and-open-files-stats
- **API Reference**: https://docs.datadoghq.com/api/latest/processes/
- **Goblin Assistant SLOs**: `../DATADOG_SLOS.md`

## Support

For issues or questions:
1. Check logs: `/var/log/datadog/`
2. Run status: `sudo datadog-agent status`
3. Flare: `sudo datadog-agent flare` (sends diagnostic bundle to support)
4. Community: https://datadoghq.slack.com

---

**Last Updated**: December 3, 2025
**Version**: 1.0.0
**Maintainer**: Goblin Assistant DevOps Team
