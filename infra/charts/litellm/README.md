---title: LiteLLM Gateway Helm Chart
type: reference
project: ForgeMonorepo
status: published
owner: GoblinOS
description: "README"

---

# LiteLLM Gateway - Universal Model Gateway

Production-ready Helm chart for deploying LiteLLM Proxy as a unified gateway for OpenAI, Gemini, DeepSeek, Ollama and other LLM providers.

## Features

- ✅ **Unified API**: Single OpenAI-compatible endpoint for all models
- ✅ **Smart Routing**: Latency-based, cost-based, or simple shuffle routing
- ✅ **Automatic Fallbacks**: Chain providers for resilience
- ✅ **Autoscaling**: HPA based on CPU/memory with 2-20 replicas
- ✅ **Observability**: OpenTelemetry tracing, Prometheus metrics
- ✅ **Security**: Non-root containers, read-only filesystem, PodDisruptionBudget
- ✅ **Production-ready**: Resource limits, health checks, proper labeling

## Quick Start

### Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- API keys for your providers (OpenAI, Gemini, DeepSeek, etc.)

### Installation

1. **Create secrets file**:

```bash
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with your actual API keys
```

1. **Install the chart**:

```bash

# Development (default values)
helm install litellm . -f secrets.yaml

# Production with custom values
helm install litellm . -f secrets.yaml -f values-prod.yaml
```

1. **Verify deployment**:

```bash
kubectl get pods -l app.kubernetes.io/name=litellm
kubectl logs -l app.kubernetes.io/name=litellm
```

1. **Test the gateway**:

```bash

# Port-forward for local testing
kubectl port-forward svc/litellm 4000:4000

# Make a test request
curl <http://localhost:4000/v1/chat/completions> \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Configuration

### Model Configuration

Edit `values.yaml` to configure your models:

```yaml
config:
  models:
    - model_name: gpt-4-turbo
      litellm_params:
        model: openai/gpt-4-turbo-preview
        api_key: "os.environ/OPENAI_API_KEY"

    - model_name: gemini-pro
      litellm_params:
        model: gemini/gemini-1.5-pro-latest
        api_key: "os.environ/GEMINI_API_KEY"

    - model_name: ollama-local
      litellm_params:
        model: ollama/llama3.2
        api_base: "http://ollama:11434"
```

### Routing & Fallbacks

```yaml

config:
  router:
    enabled: true
    routingStrategy: "latency-based-routing"  # or cost-based-routing, simple-shuffle
    fallbacks:

      - ["gpt-4-turbo", "gemini-pro"]       # Fallback gpt-4 -> gemini
      - ["gemini-pro", "deepseek-chat"]     # Fallback gemini -> deepseek
      - ["deepseek-chat", "ollama-local"]   # Fallback deepseek -> ollama
```

### Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 20
  targetCPU: 70
  targetMemory: 80
```

### Observability

```yaml

config:
  telemetry:
    enabled: true
    endpoint: "<http://jaeger-collector:4318/v1/traces">

metrics:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
```

## Integration with Services

### Update Overmind to use LiteLLM

1. **Set environment variable**:

```yaml
# In your service deployment
env:
  - name: LITELLM_BASE_URL
    value: "http://litellm:4000"
  - name: OPENAI_API_KEY
    value: "dummy"  # LiteLLM handles auth
```

1. **Update code to use OpenAI SDK**:

```typescript

// Node.js / TypeScript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'dummy',
  baseURL: process.env.LITELLM_BASE_URL
});

const response = await client.chat.completions.create({
  model: 'gpt-4-turbo',  // or gemini-pro, deepseek-chat, ollama-local
  messages: [{ role: 'user', content: 'Hello!' }]
});
```

```python
# Python
import openai

openai.api_base = "http://litellm:4000"
openai.api_key = "dummy"

response = openai.ChatCompletion.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Environment-Specific Values

### Development (`values-dev.yaml`)

```yaml

replicaCount: 1
autoscaling:
  enabled: false

config:
  logLevel: DEBUG
  setVerbose: true
  models:

    - model_name: ollama-local
      litellm_params:
        model: ollama/llama3.2
        api_base: "<http://ollama:11434">

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 256Mi
```

### Production (`values-prod.yaml`)

```yaml
replicaCount: 3

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 50

config:
  logLevel: INFO
  setVerbose: false
  database: "postgresql://user:pass@postgres:5432/litellm"

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

podDisruptionBudget:
  enabled: true
  minAvailable: 2
```

## Kustomize Overlays

For GitOps workflows, use Kustomize overlays:

```bash

infra/
  charts/litellm/
  overlays/
    dev/
      kustomization.yaml
      values.yaml
    staging/
      kustomization.yaml
      values.yaml
    prod/
      kustomization.yaml
      values.yaml
```

## Monitoring

### Metrics Endpoints

- **Prometheus metrics**: `<http://litellm:4000/metrics`>
- **Health check**: `<http://litellm:4000/health`>

### Grafana Dashboard

Import the LiteLLM dashboard (ID: TBD) for visualization of:

- Request rates by model
- Latency percentiles (p50, p95, p99)
- Error rates and fallback triggers
- Cost tracking per model/provider
- Token usage statistics

### Distributed Tracing

LiteLLM automatically exports traces to your OTLP endpoint with:

- Provider name and model
- Token counts (prompt + completion)
- Latency breakdown
- Fallback chains

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod -l app.kubernetes.io/name=litellm

# Check logs
kubectl logs -l app.kubernetes.io/name=litellm --tail=100
```

### API key errors

```bash

# Verify secrets exist
kubectl get secret litellm-secrets -o yaml

# Test secret decoding
kubectl get secret litellm-secrets -o jsonpath='{.data.openai-api-key}' | base64 -d
```

### High latency

- Check routing strategy (latency-based works best)
- Increase `maxParallelRequests` in config
- Scale up replicas or increase resource limits
- Check provider API status

## Upgrading

```bash
# Upgrade with new values
helm upgrade litellm . -f secrets.yaml -f values-prod.yaml

# Rollback if needed
helm rollback litellm
```

## Uninstallation

```bash

helm uninstall litellm
kubectl delete pvc litellm-data  # If persistence was enabled
```

## References

- [LiteLLM Documentation](https://docs.litellm.ai)
- [Supported Providers](https://docs.litellm.ai/docs/providers)
- [Router Settings](https://docs.litellm.ai/docs/routing)
- [Observability](https://docs.litellm.ai/docs/observability)

## Contributing

This chart is maintained by GoblinOS. For issues or improvements:

1. Check existing issues in the repository
1. Submit a PR with changes and updated documentation
1. Include test results with PR

## License

MIT License - See `tools/forge-new/assets/licenses/MIT.tpl`
