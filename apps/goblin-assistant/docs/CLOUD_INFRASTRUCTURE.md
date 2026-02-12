# Multi-Cloud Inference Infrastructure

## Overview

This infrastructure provides multi-cloud GPU inference for the Goblin Assistant with:

- **Google Cloud Platform (GCP)**: Ollama + llama.cpp for development and production
- **RunPod**: Serverless inference and Instant Clusters for production scaling
- **Vast.ai**: Budget-friendly batch jobs on spot 4090/3090 ($50-200/month)
- **Fly.io**: Always-on lightweight chat backend (TinyLlama)

### Architecture Decisions (Alpha Phase)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Region** | Single (us-east1) | Reduce complexity; add regions via config later |
| **Model Registry** | Hybrid (MLflow/W&B + GCS) | Track experiments, store artifacts cheaply |
| **Vast.ai Budget** | $50-200/month | Spot 4090/3090 for dev/experimental jobs |
| **Fallback** | Fly.io TinyLlama | Always-on chat when cloud providers unavailable |

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Inference Orchestrator                               │
│   ┌─────────────┬──────────────┬──────────────┬───────────┬────────────┐   │
│   │ GCP Ollama  │ GCP llama.cpp│   RunPod     │  Vast.ai  │  Fly.io    │   │
│   │  (Dev/Fast) │  (Cloud Run) │ (Production) │  (Budget) │ (Fallback) │   │
│   └──────┬──────┴──────┬───────┴──────┬───────┴─────┬─────┴─────┬──────┘   │
│          │             │              │             │           │          │
│   ┌──────▼─────────────▼──────────────▼─────────────▼───────────▼──────┐   │
│   │                    GCS Model Storage (us-east1)                     │   │
│   │           (Encrypted weights, checkpoints, configs)                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│   ┌────────────────────────────────▼────────────────────────────────────┐   │
│   │              Model Registry (MLflow/W&B + GCS Artifacts)            │   │
│   │          Experiments → Metrics → Artifacts → Deployment             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

1. **GCP Project** with billing enabled
2. **Terraform** >= 1.0
3. **Docker** and Docker Compose
4. **Fly.io account** (for chat backend)
5. **API Keys**:
   - RunPod: https://www.runpod.io/console/user/settings
   - Vast.ai: https://vast.ai/console/account

### 1. Set Environment Variables

```bash
# Copy example env and fill in values
cp .env.example .env

# Required variables:
export GCS_PROJECT_ID="goblin-assistant-llm"
export GCS_REGION="us-east1"  # Single region for alpha
export RUNPOD_API_KEY="rpa_XXXXXXXXX"
export VASTAI_API_KEY="XXXXXXXXXXXXXXXX"

# Vast.ai budget settings
export VASTAI_MONTHLY_BUDGET="100"
export VASTAI_MAX_COST_PER_HOUR="0.80"

# Model Registry
export MLFLOW_TRACKING_URI="http://localhost:5000"
export WANDB_PROJECT="goblin-llm"

# Optional (for external providers):
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GROQ_API_KEY="gsk_..."
```

### 2. Deploy Infrastructure (Terraform)

```bash
cd infra/cloud-providers

# Initialize Terraform
terraform init

# Create production config
cp example.tfvars prod.tfvars
# Edit prod.tfvars with your values

# Plan and verify
terraform plan -var-file=prod.tfvars

# Apply infrastructure
terraform apply -var-file=prod.tfvars
```

### 3. Deploy Fly.io Chat Backend

```bash
# Full setup (first time)
./scripts/deploy/deploy_flyio_chat.sh full

# Or step by step:
./scripts/deploy/deploy_flyio_chat.sh setup
./scripts/deploy/deploy_flyio_chat.sh download-model
./scripts/deploy/deploy_flyio_chat.sh deploy
```

### 4. Start Services (Docker)

```bash
cd apps/goblin-assistant

# Start base services (Redis, Celery workers, etc.)
docker-compose up -d

# Add cloud provider services
docker-compose -f docker-compose.yml -f docker-compose.cloud.yml up -d
```

### 5. Verify Deployment

```bash
# Check service health
curl http://localhost:8003/health

# Check Fly.io chat backend
curl https://goblin-chat.fly.dev/health

# Check provider status
curl http://localhost:8004/providers

# View Flower dashboard
open http://localhost:5555
```

## Architecture

### Components

#### Inference Orchestrator (`inference_orchestrator.py`)

Central routing layer that selects the best provider based on:
- **Latency**: RTT-based routing to fastest provider
- **Cost**: Route to cheapest available option
- **Availability**: Skip unhealthy providers
- **Capability**: Match model requirements to provider capabilities

Routing strategies:
- `LOWEST_LATENCY`: Minimize response time
- `LOWEST_COST`: Minimize inference cost
- `ROUND_ROBIN`: Distribute load evenly
- `WEIGHTED_RANDOM`: Probabilistic based on weights
- `FAILOVER`: Primary → Secondary → Tertiary

#### Provider Adapters

| Provider | Adapter | Use Case |
|----------|---------|----------|
| GCP Ollama | `ollama_adapter.py` | Fast iteration, dev environment |
| GCP llama.cpp | `llamacpp_adapter.py` | Production Cloud Run, quantized models |
| RunPod | `runpod_adapter.py` | Serverless inference, auto-scaling |
| Vast.ai | `vastai_adapter.py` | Training, batch jobs, cost-sensitive |

#### Model Storage (`model_storage.py`)

GCS-backed storage with:
- **Encryption**: KMS or customer-managed keys
- **Signed URLs**: Time-limited download links (1 hour default)
- **Checkpointing**: Resumable training with automatic save/restore
- **Versioning**: Track model iterations with metadata

#### Celery Workers

| Queue | Concurrency | Tasks |
|-------|-------------|-------|
| `high_priority` | 2 | Real-time inference requests |
| `default` | 4 | Standard processing |
| `low_priority` | 2 | Background tasks |
| `training` | 2 | Model training jobs |
| `inference` | 4 | Batch inference |

### Data Flow

```
User Request → API Gateway → Orchestrator
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
              GCP Ollama   RunPod     Vast.ai
                    │           │           │
                    └───────────┼───────────┘
                                │
                          GCS Models
                                │
                          Response Cache
                                │
                         User Response
```

## Provider Configuration

### GCP (Ollama + llama.cpp)

**Best for**: Development, low-latency production, persistent model caching

```python
# config/cloud_providers.py
gcp_config = GCPConfig(
    project_id="goblin-assistant-llm",
    region="us-central1",
    ollama_vm_url="http://10.128.0.2:11434",
    llamacpp_cloudrun_url="https://llama-cpp-xxxx.run.app",
    model_bucket="goblin-llm-models",
)
```

**Setup**:
1. Terraform creates VM for Ollama
2. Cloud Run deploys llama.cpp container
3. Models stored in GCS with signed URL access

### RunPod

**Best for**: Production inference, auto-scaling, managed infrastructure

```python
runpod_config = RunPodConfig(
    api_key=os.getenv("RUNPOD_API_KEY"),
    endpoint_name="goblin-inference",
    gpu_types=["NVIDIA RTX 4090", "NVIDIA A100 80GB"],
    min_workers=0,  # Scale to zero
    max_workers=5,
    idle_timeout=300,
)
```

**Features**:
- Serverless endpoints with cold start ~10s
- Instant Clusters for training (multi-GPU)
- Pay-per-second billing
- Managed networking and storage

### Vast.ai

**Best for**: Training, batch processing, cost optimization

```python
# Budget mode config ($50-200/month)
vastai_config = VastAIConfig(
    api_key=os.getenv("VASTAI_API_KEY"),
    monthly_budget_usd=100,
    max_cost_per_hour=0.80,  # ~$0.40-0.80/hr for spot 4090
    min_reliability=0.90,    # 90% uptime acceptable for dev
    preferred_gpus=["RTX_4090", "RTX_3090"],  # Budget GPUs only
    use_spot_instances=True,
    spot_bid_multiplier=1.0,  # Accept preemption
    checkpoint_interval_minutes=15,  # Frequent checkpoints
)
```

**Budget Pricing (Spot)**:
| GPU | $/hour | Best For |
|-----|--------|----------|
| RTX 4090 | $0.40-0.60 | Quantized inference, light training |
| RTX 3090 | $0.25-0.40 | Budget training, batch jobs |

**Security**:
- Treat as **untrusted** environment
- Use signed URLs for model downloads
- Encrypt sensitive weights
- Checkpoint frequently (preemption risk)

### Fly.io (Always-On Chat)

**Best for**: Fallback when cloud providers unavailable, lightweight chat

```toml
# fly.chat.toml
app = "goblin-chat"
primary_region = "iad"  # us-east

[[vm]]
  size = "shared-cpu-2x"
  memory = "2gb"
```

**Features**:
- Always-on (auto_stop_machines = false)
- TinyLlama 1.1B (fits in 2GB with int4)
- OpenAI fallback if local model unavailable
- $5-10/month for always-on

**Deployment**:
```bash
./scripts/deploy/deploy_flyio_chat.sh full
```

## Model Registry

### Hybrid Strategy

Track experiments in MLflow/W&B, store artifacts in GCS:

```
Experiment Tracking (MLflow/W&B)     Artifact Storage (GCS)
┌─────────────────────────┐         ┌─────────────────────────┐
│ - Metrics (loss, acc)   │         │ gs://goblin-llm-models/ │
│ - Parameters (lr, epoch)│  ──►    │   models/goblin/        │
│ - Run history           │         │     mistral-7b/         │
│ - Model versions        │         │       v1.0.0/           │
└─────────────────────────┘         │         model.safetens  │
                                    │         metadata.json   │
                                    └─────────────────────────┘
```

### Usage

```python
from services.model_registry import get_registry, ModelStage

registry = get_registry()

# Register a new model
version = registry.register_model(
    model_name="mistral-7b-instruct",
    model_path="/path/to/model",
    metrics={"loss": 0.5, "accuracy": 0.95},
    parameters={"epochs": 10, "lr": 1e-5},
)

# Promote to production
registry.promote_to_production("mistral-7b-instruct", "v1.0.0")

# Rollback
registry.rollback("mistral-7b-instruct", "v0.9.0")

# Get production model
prod = registry.get_production_model("mistral-7b-instruct")
```

### Naming Convention

```
gs://{bucket}/models/{org}/{model_name}/{version}/{artifact}

Example:
gs://goblin-llm-models/models/goblin/mistral-7b-instruct/v1.0.0/model.safetensors
```

## Operations

### Submitting Training Jobs

```bash
# Via CLI script (budget mode)
./infra/cloud-providers/scripts/submit_vastai_job.sh \
  --type training \
  --gpu RTX_4090 \
  --hours 8 \
  --max-cost 0.80

# Via Celery task
from tasks.model_training_worker import submit_training_job

task = submit_training_job.apply_async(
    args=["my-model", {"epochs": 10, "batch_size": 32}],
    queue="training"
)
```

### Monitoring

**Flower Dashboard**: http://localhost:5555
- Task status and history
- Worker health
- Queue depths

**Provider Health**: http://localhost:8004/providers
```json
{
  "gcp_ollama": {"status": "healthy", "latency_ms": 45},
  "runpod": {"status": "healthy", "latency_ms": 120},
  "vastai": {"status": "degraded", "active_instances": 2}
}
```

**Prometheus Metrics**: http://localhost:9090
- `inference_requests_total`
- `inference_latency_seconds`
- `provider_errors_total`
- `model_download_bytes`

### Cost Management

```bash
# Check current costs
./scripts/cloud_costs.sh

# Set cost alerts (Terraform)
resource "google_monitoring_alert_policy" "cost_alert" {
  display_name = "Cloud Cost Alert"
  conditions {
    condition_threshold {
      filter          = "metric.type=\"billing.googleapis.com/billing/cost\""
      threshold_value = 100  # $100/day
    }
  }
}
```

**Cost optimization tips**:
1. Use RunPod serverless for variable load
2. Use Vast.ai spot for training (up to 80% savings)
3. Set `idle_timeout` to scale to zero
4. Cache frequently used models in GCS
5. Use quantized models (GGUF Q4_K_M) for inference

## Troubleshooting

### Common Issues

**RunPod endpoint not responding**:
```bash
# Check endpoint status
./scripts/deploy_runpod_endpoint.sh --status

# Verify API key
curl -H "Authorization: Bearer $RUNPOD_API_KEY" \
  https://api.runpod.io/graphql \
  -d '{"query": "{ myself { id } }"}'
```

**Vast.ai no offers found**:
```bash
# Increase cost ceiling
./scripts/submit_vastai_job.sh --max-cost 5.0

# Try different GPU
./scripts/submit_vastai_job.sh --gpu RTX_4090
```

**Model download fails**:
```bash
# Check GCS permissions
gcloud storage ls gs://goblin-llm-models/

# Verify service account
gcloud iam service-accounts list

# Check signed URL validity
python -c "from services.model_storage import GCSModelStorage; ..."
```

### Logs

```bash
# Celery worker logs
docker-compose logs -f celery-worker-training

# Orchestrator logs
docker-compose logs -f inference-orchestrator

# All cloud services
docker-compose -f docker-compose.yml -f docker-compose.cloud.yml logs -f
```

## Security

### Secrets Management

All secrets are stored in GCP Secret Manager and injected at runtime:

```hcl
# Terraform manages secrets
resource "google_secret_manager_secret" "runpod_api_key" {
  secret_id = "runpod-api-key"
}
```

### Encryption

- **At rest**: GCS with KMS encryption
- **In transit**: TLS 1.3 for all connections
- **Model weights**: Optional AES-256 encryption for sensitive models

### Access Control

- Service account with minimal permissions
- Signed URLs expire after 1 hour
- Vast.ai treated as untrusted (no persistent secrets)

## Files Reference

```
apps/goblin-assistant/
├── backend/
│   ├── config/
│   │   └── cloud_providers.py     # Provider configuration (us-east1, budget Vast.ai)
│   ├── providers/
│   │   ├── runpod_adapter.py      # RunPod API integration
│   │   └── vastai_adapter.py      # Vast.ai API integration
│   ├── services/
│   │   ├── model_storage.py       # GCS model management
│   │   ├── model_registry.py      # Hybrid registry (MLflow/W&B + GCS)
│   │   └── inference_orchestrator.py  # Multi-provider routing
│   ├── tasks/
│   │   └── model_training_worker.py   # Celery training tasks
│   ├── api/
│   │   └── chat_backend.py        # Fly.io chat service
│   ├── requirements-cloud.txt     # Cloud dependencies (MLflow, W&B)
│   └── requirements-chat.txt      # Fly.io chat dependencies
├── docker-compose.yml             # Base services
├── docker-compose.cloud.yml       # Cloud provider overlay
├── Dockerfile.orchestrator        # Orchestrator image
├── Dockerfile.chat                # Fly.io chat image
├── fly.toml                       # Main Fly.io config
├── fly.chat.toml                  # Chat backend Fly.io config
└── .env.example                   # Environment template

infra/cloud-providers/
├── main.tf                        # Terraform configuration (us-east1)
├── example.tfvars                 # Example variables
├── scripts/
│   ├── deploy_runpod_endpoint.sh  # RunPod deployment
│   └── submit_vastai_job.sh       # Vast.ai job submission

scripts/deploy/
└── deploy_flyio_chat.sh           # Fly.io chat deployment
└── generated/                     # Terraform outputs
```

## Next Steps

1. **Production deployment**: Set up CI/CD with GitHub Actions
2. **Monitoring**: Integrate with Datadog for full observability
3. **Auto-scaling**: Configure HPA for Kubernetes deployment
4. **Fine-tuning**: Add LoRA/QLoRA training pipelines
5. **RAG enhancement**: Integrate ChromaDB with document ingestion
