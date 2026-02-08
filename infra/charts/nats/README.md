---title: NATS JetStream for Overmind
type: reference
project: GoblinOS/Overmind
status: published
owner: GoblinOS
goblin_name: Overmind NATS
description: "README"

---

# NATS JetStream Messaging

Event-driven architecture for Overmind using [NATS JetStream](https://docs.nats.io/nats-concepts/jetstream).

## Overview

NATS JetStream provides:

- ✅ **Persistent messaging** - At-least-once delivery guarantees
- ✅ **Event streaming** - Replay events from any point in time
- ✅ **Horizontal scaling** - Clustered for high availability
- ✅ **Performance** - Millions of messages per second
- ✅ **KEDA integration** - Autoscale based on queue depth
- ✅ **Observability** - Prometheus metrics and Grafana dashboards

## Architecture

```
Publishers                  NATS JetStream Cluster              Consumers
┌─────────────┐            ┌──────────────────────┐           ┌──────────────┐
│   Bridge    │──routing─→ │  routing-decisions   │──→        │  API Server  │
│             │            │  - model.selected    │           │              │
└─────────────┘            │  - fallback.triggered│           └──────────────┘
                           │  - cost.calculated   │
┌─────────────┐            └──────────────────────┘           ┌──────────────┐
│ Memory API  │──memory──→ ┌──────────────────────┐──→        │  Temporal    │
│             │            │   memory-events      │           │   Worker     │
└─────────────┘            │  - added             │           └──────────────┘
                           │  - consolidated      │
┌─────────────┐            │  - retrieved         │           ┌──────────────┐
│   LiteLLM   │──llm────→  │  - expired           │──→        │  Analytics   │
│   Gateway   │            └──────────────────────┘           │   Service    │
└─────────────┘            ┌──────────────────────┐           └──────────────┘
                           │   llm-requests       │
                           │  - request.started   │
                           │  - request.completed │
                           │  - request.failed    │
                           └──────────────────────┘
```

## Quick Start

### Install NATS JetStream

```bash
# Add Helm repo
helm repo add nats https://nats-io.github.io/k8s/helm/charts/
helm repo update

# Install NATS with JetStream
helm install nats-jetstream nats/nats \
  --namespace overmind-prod \
  --values values.yaml \
  --wait

# Verify installation
kubectl get pods -n overmind-prod -l app.kubernetes.io/name=nats
```

### Create Streams and Consumers

```bash

# Apply stream configurations
kubectl apply -f streams/

# Verify streams
nats stream list --server=nats://nats:4222
```

### Test Connectivity

```bash
# Port forward NATS
kubectl port-forward -n overmind-prod svc/nats 4222:4222

# Publish test message
nats pub --server=nats://localhost:4222 routing.model.selected '{"model":"gemini-pro","cost":0.001}'

# Subscribe to stream
nats sub --server=nats://localhost:4222 'routing.>'
```

## Streams

### routing-decisions

Routing decisions made by the bridge for LLM model selection.

**Subjects:**
- `routing.model.selected` - Model selected for request
- `routing.fallback.triggered` - Fallback to alternative model
- `routing.cost.calculated` - Cost calculation for request

**Configuration:**
- Retention: 7 days
- Max size: 1GB
- Storage: File (persistent)
- Replicas: 3

**Message Schema:**

```typescript

interface RoutingDecision {
  requestId: string;
  timestamp: string;
  selectedModel: string;
  reason: 'cost-optimized' | 'performance' | 'balanced';
  estimatedCost: number;
  estimatedLatency: number;
  alternatives: Array<{
    model: string;
    cost: number;
    latency: number;
  }>;
}
```

### memory-events

Memory tier transitions and consolidation events.

**Subjects:**

- `memory.added` - New memory added to short-term
- `memory.consolidated` - Memory moved to working/long-term
- `memory.retrieved` - Memory accessed from any tier
- `memory.expired` - Memory removed due to TTL

**Configuration:**

- Retention: 30 days
- Max size: 5GB
- Storage: File (persistent)
- Replicas: 3

**Message Schema:**

```typescript
interface MemoryEvent {
  eventId: string;
  timestamp: string;
  memoryId: string;
  eventType: 'added' | 'consolidated' | 'retrieved' | 'expired';
  tier: 'short-term' | 'working' | 'long-term';
  importance?: number;
  accessCount?: number;
  metadata?: Record<string, unknown>;
}
```

### llm-requests

LLM request lifecycle events for metrics and cost tracking.

**Subjects:**
- `llm.request.started` - Request initiated
- `llm.request.completed` - Request completed successfully
- `llm.request.failed` - Request failed with error

**Configuration:**
- Retention: 24 hours
- Max size: 500MB
- Storage: File (persistent)
- Replicas: 3

**Message Schema:**

```typescript

interface LLMRequest {
  requestId: string;
  timestamp: string;
  provider: string;
  model: string;
  tokens: {
    prompt: number;
    completion: number;
    total: number;
  };
  cost: number;
  latency: number;
  status: 'started' | 'completed' | 'failed';
  error?: string;
}
```

## Consumers

### api-consumer

API server consumes routing decisions for analytics.

- **Stream:** routing-decisions
- **Filter:** `routing.>`
- **Ack Policy:** Explicit
- **Max Deliver:** 3 attempts
- **Ack Wait:** 30 seconds

### analytics-consumer

Analytics service consumes all routing decisions for reporting.

- **Stream:** routing-decisions
- **Filter:** `routing.>`
- **Ack Policy:** Explicit
- **Max Deliver:** 5 attempts
- **Batch:** 1000 messages
- **Ack Wait:** 60 seconds

### consolidation-consumer

Temporal worker consumes memory consolidation events.

- **Stream:** memory-events
- **Filter:** `memory.consolidated`
- **Ack Policy:** Explicit
- **Max Deliver:** 3 attempts
- **Ack Wait:** 120 seconds

### metrics-consumer

Metrics collector consumes LLM request events.

- **Stream:** llm-requests
- **Filter:** `llm.>`
- **Ack Policy:** Explicit
- **Max Deliver:** 3 attempts
- **Ack Wait:** 30 seconds

## Client Integration

### Node.js/TypeScript (Bridge)

```typescript
import { connect, StringCodec, JetStreamClient } from 'nats';

// Connect to NATS
const nc = await connect({
  servers: process.env.NATS_URL |  | 'nats://localhost:4222',
  token: process.env.NATS_TOKEN,
});

// Get JetStream client
const js = nc.jetstream();
const sc = StringCodec();

// Publish routing decision
async function publishRoutingDecision(decision: RoutingDecision) {
  const subject = 'routing.model.selected';
  const data = sc.encode(JSON.stringify(decision));

  const ack = await js.publish(subject, data);
  console.log(`Published to ${subject}, seq: ${ack.seq}`);
}

// Subscribe to routing decisions
async function subscribeRoutingDecisions() {
  const consumer = await js.consumers.get('routing-decisions', 'api-consumer');
  const messages = await consumer.consume();

  for await (const msg of messages) {
    const data = JSON.parse(sc.decode(msg.data));
    console.log('Received:', data);
    msg.ack();
  }
}
```

### Python (API)

```python

import os
import json
import asyncio
from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig

# Connect to NATS
async def connect_nats():
    nc = NATS()
    await nc.connect(
        servers=[os.getenv("NATS_URL", "nats://localhost:4222")],
        token=os.getenv("NATS_TOKEN"),
    )
    return nc

# Publish memory event
async def publish_memory_event(nc: NATS, event: dict):
    js = nc.jetstream()
    subject = f"memory.{event['eventType']}"
    data = json.dumps(event).encode()

    ack = await js.publish(subject, data)
    print(f"Published to {subject}, seq: {ack.seq}")

# Subscribe to memory events
async def subscribe_memory_events(nc: NATS):
    js = nc.jetstream()

    # Pull-based consumer
    psub = await js.pull_subscribe(
        "memory.>",
        "consolidation-consumer",
        stream="memory-events"
    )

    while True:
        msgs = await psub.fetch(batch=10, timeout=5)
        for msg in msgs:
            data = json.loads(msg.data.decode())
            print(f"Received: {data}")
            await msg.ack()
```

## Monitoring

### Prometheus Metrics

NATS exposes metrics on port 7777:

```bash
# Port forward metrics
kubectl port-forward -n overmind-prod svc/nats 7777:7777

# Query metrics
curl http://localhost:7777/metrics | grep nats

# Key metrics
# nats_jetstream_stream_messages
# nats_jetstream_consumer_num_pending
# nats_jetstream_consumer_delivered
# nats_jetstream_consumer_ack_pending
```

### Grafana Dashboard

Import NATS dashboard (ID: 2279):

```bash

# In Grafana UI

# Dashboards → Import → 2279
```

### Stream Status

```bash
# List streams
nats stream list --server=nats://nats:4222

# Stream info
nats stream info routing-decisions --server=nats://nats:4222

# Consumer info
nats consumer info routing-decisions api-consumer --server=nats://nats:4222
```

## KEDA Integration

NATS JetStream triggers KEDA autoscaling:

```yaml

apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: api-scaler-nats
spec:
  scaleTargetRef:
    name: overmind-api
  triggers:

  - type: nats-jetstream
    metadata:
      natsServerMonitoringEndpoint: nats:8222
      stream: routing-decisions
      consumer: api-consumer
      lagThreshold: "10"
```

See `infra/charts/keda/scaledobjects/overmind-api-scaler.yaml` for full configuration.

## Troubleshooting

### Connection refused

```bash
# Verify NATS is running
kubectl get pods -n overmind-prod -l app.kubernetes.io/name=nats

# Check logs
kubectl logs -n overmind-prod deployment/nats

# Test connectivity
kubectl run -it --rm nats-test --image=natsio/nats-box:latest -- \
  nats pub --server=nats://nats:4222 test.subject "hello"
```

### Authentication failed

```bash

# Verify secret exists
kubectl get secret nats-auth -n overmind-prod

# Check token
kubectl get secret nats-auth -n overmind-prod -o jsonpath='{.data.token}' | base64 -d
```

### Stream not found

```bash
# List streams
nats stream list --server=nats://nats:4222

# Create stream manually
nats stream add routing-decisions \
  --subjects="routing.>" \
  --retention=limits \
  --max-age=168h \
  --max-bytes=1GB \
  --storage=file \
  --replicas=3 \
  --server=nats://nats:4222
```

### Consumer lag growing

```bash

# Check consumer status
nats consumer info routing-decisions api-consumer --server=nats://nats:4222

# Check KEDA scaling
kubectl get hpa -n overmind-prod

# Manually scale if needed
kubectl scale deployment overmind-api --replicas=5 -n overmind-prod
```

## Best Practices

1. **Use durable consumers** - Survive pod restarts
1. **Set ack timeouts** - Match processing time
1. **Configure max deliver** - Prevent infinite retries
1. **Monitor lag** - Use KEDA for autoscaling
1. **Use file storage** - Memory storage for ephemeral data only
1. **Enable clustering** - 3+ replicas for HA
1. **Set retention policies** - Balance storage vs history

## References

- [NATS JetStream Documentation](https://docs.nats.io/nats-concepts/jetstream)
- [NATS CLI](https://docs.nats.io/using-nats/nats-tools/nats_cli)
- [NATS Helm Chart](https://github.com/nats-io/k8s/tree/main/helm/charts/nats)
- [KEDA NATS Scaler](https://keda.sh/docs/scalers/nats-jetstream/)

## License

MIT
