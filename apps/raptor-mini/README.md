# Raptor Mini Service

Cloud-hosted Raptor Mini LLM service with local development fallback.

## Architecture

- **Cloud Primary**: Hosted on Kamatera VM with Docker containerization
- **Local Fallback**: Development instance using Ollama
- **API**: FastAPI with API key authentication
- **Proxy**: Nginx reverse proxy with authentication

## Quick Start

### Local Development

1. **Install Ollama and pull model (local)**:

  ```bash
  # Install Ollama (if not already installed)
  brew install ollama

  # Pull Raptor Mini model
  ollama pull raptor-mini
  # Alternatively use the convenience script if present
  ./scripts/pull_ollama_model.sh raptor-mini
  ```

2. **Run locally**:
   ```bash

   cd apps/raptor-mini
   docker-compose up --build
   ```

3. **Test the service**:

   ```bash
   curl -X POST "http://localhost:8080/v1/generate" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, how are you?", "max_tokens": 50}'
   ```

### Cloud Deployment (Existing Kamatera Server)

Your existing Kamatera server at `66.55.77.147` is already configured. Deploy Raptor Mini alongside your existing LLM service:

```bash

# From your local machine
cd apps/raptor-mini
./deploy-kamatera.sh
```

This will:

- SSH into your existing Kamatera server (66.55.77.147)
- Deploy Raptor Mini on port 8080 (existing LLM service uses port 8000)
- Configure API key authentication
- Set up automatic restarts

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check
- `POST /v1/generate` - Generate text

### Generate Request

```json
{
  "prompt": "Your prompt here",
  "max_tokens": 128
}
```

### Generate Response

```json

{
  "ok": true,
  "result": {
    "response": "Generated text here"
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | "" | API key for authentication (empty = dev mode) |
| `MODEL_NAME` | "raptor-mini" | Ollama model name |
| `PORT` | "8080" | Service port |
| `MODEL_PATH` | "/models/raptor-mini" | Model file path (legacy) |

## Integration with Goblin Backend

The service integrates with Goblin Assistant backend using circuit-breaker pattern and your existing Kamatera infrastructure:

```python
from backend.inference_clients import call_raptor

# This will try Kamatera (66.55.77.147:8080) first, then fallback to local
result = await call_raptor("Hello world", max_tokens=50)
```

The integration uses your existing environment variables:

```bash

# Already configured in your setup
KAMATERA_HOST=66.55.77.147
KAMATERA_LLM_API_KEY=goblin-llm-hrDD-3IO83-YpusDBHXV_V0r7Lx9sMtvEs4CWBnF2kE

# Optional: override local fallback URL
LOCAL_RAPTOR_URL=<http://127.0.0.1:8080/v1/generate>
```

## Monitoring

- **Health Check**: `GET /health`
- **Logs**: Structured JSON logging

## Security

- API key authentication required for production
- Internal networking only (no public exposure)
- Nginx proxy with request validation
- Circuit breaker prevents cascade failures

## Development

### Testing Locally

```bash
# With API key
curl -X POST "http://localhost:8080/v1/generate" \
  -H "X-API-Key: supersecretkey" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test prompt", "max_tokens": 50}'

# Health check
curl http://localhost:8080/health

# Metrics
curl http://localhost:8080/metrics
```

### Model Management

```bash

# List available models
ollama list

# Pull specific model
ollama pull raptor-mini

# Remove model
ollama rm raptor-mini
```

## Deployment Checklist

- [ ] Kamatera VM provisioned with Docker
- [ ] Strong API key generated and stored securely
- [ ] Model downloaded (`ollama pull raptor-mini`)
- [ ] Container built and running
- [ ] Nginx proxy configured (if used)
- [ ] Health checks passing
- [ ] Goblin backend environment variables set
- [ ] Circuit breaker tested (disconnect cloud, verify fallback)

## Troubleshooting

### Common Issues

1. **Model not found**: Run `ollama pull raptor-mini`
2. **Port already in use**: Change `PORT` environment variable
3. **API key rejected**: Check `X-API-Key` header format
4. **Connection refused**: Ensure service is running and port is accessible

### Logs

```bash
# Container logs
docker logs raptor-mini

# Ollama logs
ollama logs
```

## Performance Tuning

- **Concurrent requests**: Increase VM CPU cores
- **Memory**: Monitor with `/metrics` endpoint
- **Load balancing**: Run multiple containers behind proxy
- **GPU support**: Switch to CUDA base image for GPU inference
