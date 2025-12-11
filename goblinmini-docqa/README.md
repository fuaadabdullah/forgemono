# GoblinMini DocQA

A lightweight, modular documentation quality analysis tool that evaluates documentation files using multiple analysis methods including heuristics, local LLMs, and AI services.

## Features

- **Multiple Analysis Methods**: Choose from heuristic analysis, local LLM models, or AI service proxies
- **Web API**: RESTful API for integration with other tools
- **CLI Interface**: Command-line tool for batch processing
- **Modular Architecture**: Easy to extend with new analysis adapters
- **Docker Support**: Containerized deployment with docker-compose
- **Comprehensive Testing**: Full test coverage with pytest
- **Type Safety**: Full mypy type checking
- **Backpressure Protection**: Automatic queue management with 429 responses when overloaded
- **Rate Limiting**: Per-IP sliding window rate limits using Redis
- **Request Size Limits**: Prevents memory exhaustion from large documents
- **Graceful Shutdown**: Proper cleanup of models and queues on termination

## Quick Start

### Using Supervisor (Recommended for Production)

```bash
# Clone and navigate to the project
cd goblinmini-docqa

# Configure environment (port, tokens, etc.)
cp .env.example .env
# Edit .env with your settings

# Start with supervision (prevents ghost processes)
make server

# Or run in background
make server-bg

# Check status
make status

# Stop server
make stop-server

# Clean up lockfiles
make clean-locks
```

### Using Docker

```bash

# Start the application
make up

# The API will be available at http://localhost:8000

# CLI is available via: docker-compose exec app goblinmini-docqa --help
```

### Local Development

```bash
# Install dependencies
make dev-install

# Run the CLI
python -m app.cli --help

# Start the web server
uvicorn app.server:app --reload

# Run tests
make test
```

## Usage

### CLI

```bash

# Analyze a single file
goblinmini-docqa analyze docs/README.md

# Analyze multiple files
goblinmini-docqa analyze docs/*.md

# Use specific analysis method
goblinmini-docqa analyze --method heuristic docs/README.md

# Output results to JSON
goblinmini-docqa analyze --output results.json docs/README.md
```

### API

```bash
# Analyze documentation
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"content": "Your documentation content here"}'

# Get analysis methods
curl http://localhost:8000/methods
```

## Protection Features

### Backpressure & Queue Management

The API implements intelligent backpressure to prevent system overload:

- **Queue Capacity Checks**: Requests are rejected with `429 Too Many Requests` when job queues are at 80%+ capacity
- **Inference Queue Monitoring**: Model inference requests are throttled when the inference queue is near capacity
- **Graceful Degradation**: System continues operating but refuses new work when overloaded
- **Retry-After Headers**: Clients receive guidance on when to retry failed requests

### Rate Limiting

Multi-layer rate limiting protects against abuse:

- **Per-IP Rate Limits**: Sliding window limits using Redis (configurable per minute/hour)
- **Fallback Limits**: SlowAPI provides memory-based limits when Redis is unavailable
- **Endpoint-Specific Limits**: Different limits can be applied to different API endpoints
- **Redis Sliding Windows**: Advanced rate limiting with `limits` library for precise control

### Request Size Limits

Memory protection through request size validation:

- **Content Size Checks**: Request bodies are validated against configurable size limits
- **File Size Validation**: File analysis requests check file sizes before queuing
- **Early Rejection**: Large requests are rejected with `413 Request Entity Too Large` before processing
- **Configurable Limits**: Default 50MB limit, adjustable via `MAX_REQUEST_SIZE_MB`

### Graceful Shutdown

Proper cleanup ensures system stability:

- **Lifespan Events**: FastAPI lifespan events handle startup/shutdown
- **Model Cleanup**: Local models are properly shut down and memory freed
- **Queue Draining**: Running jobs get time to complete before shutdown
- **Connection Cleanup**: Redis and other connections are properly closed

### Configuration

Configure protection features in your `.env` file:

```bash

# Rate limiting (requests per IP)
RATE_LIMIT_REQUESTS_PER_MINUTE=10
RATE_LIMIT_REQUESTS_PER_HOUR=100

# Request size limits (MB)
MAX_REQUEST_SIZE_MB=50

# Backpressure timeout (seconds)
QUEUE_BACKPRESSURE_TIMEOUT=0.5
```

### Health Monitoring

Check system status including protection metrics:

```bash
curl http://localhost:8000/health
```

Returns queue sizes, rate limit settings, and backpressure status.

## Configuration

Create a `.env` file based on `.env.example`:

```bash

# Analysis method (heuristic, local_llm, copilot_proxy)
ANALYSIS_METHOD=heuristic

# Local LLM configuration
LOCAL_LLM_URL=<http://localhost:11434>
LOCAL_LLM_MODEL=llama2

# GitHub Copilot configuration
GITHUB_TOKEN=your_github_token
COPILOT_API_URL=<https://api.github.com/copilot>

# Server configuration
DOCQA_PORT=8000
```

### Portability & Process Management

The service includes built-in supervisor functionality to prevent ghost processes:

- **Port Configuration**: Set `DOCQA_PORT` in `.env` to configure the service port
- **Lockfile Protection**: Prevents multiple instances from running simultaneously
- **Health Checks**: Automatic port availability checking before startup
- **Graceful Shutdown**: Lockfile cleanup on service termination

### Supervisor Commands

```bash
# Check port availability
./utils/check_port.sh 8000

# Start with supervision
make server

# Start in background
make server-bg

# Check status
make status

# Stop server
make stop-server

# Clean lockfiles
make clean-locks
```

## Security

This application implements enterprise-grade security measures for production deployment.

### 🔐 API Authentication

All API endpoints require authentication using a secure token:

```bash

# Generate a secure token
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Use in API requests
curl -X POST "<http://localhost:8000/analyze"> \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"content": "Your documentation content here"}'
```

### 🛡️ Container Security

- **Read-only filesystem**: Prevents unauthorized modifications
- **Non-root user**: Runs with minimal privileges (UID 1001)
- **Secure token management**: Tokens stored in environment variables only
- **No sensitive data persistence**: All data encrypted in transit

### 🔄 Token Rotation

Regular token rotation is recommended for security:

```bash
# Monthly rotation procedure
make rotate-token
# Follows the procedure in SECURITY.md
```

See [SECURITY.md](SECURITY.md) for complete security configuration and incident response procedures.

## Deployment Architecture

### Single Listener Rule + Inference Queue

This application enforces **"Deployment rule #1 — one listener only"** with a **single model host + bounded worker pool** pattern:

- **Single Worker Deployment**: Always run with `--workers 1` (configured as `DOCQA_WORKERS=1`)
- **Inference Queue**: Bounded queue (`MAX_QUEUE_SIZE=8`) with worker pool (`MAX_INFERENCE_WORKERS=1`)
- **Single Model Instance**: Model loads once at startup, shared across all requests
- **Backpressure**: Queue rejects requests when full, preventing resource exhaustion

#### Why This Architecture?

- **Model Efficiency**: AI model loads once in memory (not duplicated)
- **Resource Control**: Hard concurrency limits prevent GPU/CPU overload
- **Backpressure**: Queue fullness signals when to scale instances
- **Predictable Performance**: Bounded workers ensure consistent response times

#### Inference Queue Pattern

```python

# Single model instance loaded at startup
model = LocalModelAdapter()
model.init()  # Loads model once

# Bounded queue with worker pool
inference_queue = InferenceQueue(
  model_callable=lambda payload: model.generate(**payload),
    max_workers=1,    # Sequential inference
    max_queue=8       # Backpressure at 8 requests
)

# Requests submit to queue
result = await inference_queue.submit({
    "prompt": user_prompt,
    "max_tokens": 512
}, timeout=30.0)
```

#### CPU-Aware Threading

The service automatically configures llama-cpp threading based on available CPU cores:

```python
cpu_count = multiprocessing.cpu_count()
LLAMA_N_THREADS = max(1, cpu_count // 2)  # Reserve half for other processes
```

**Example on 8-core system:**
- Total cores: 8
- Reserved for system/web server: 4 cores
- Used for llama-cpp inference: 4 threads

**Override via environment:**
```bash

# Force specific thread count
LLAMA_N_THREADS=2 make server
```

**Health endpoint shows configuration:**

```json
{
  "cpu_config": {
    "cpu_count": 8,
    "llama_threads": 4
  }
}
```

## Architecture

```
goblinmini-docqa/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Command-line interface
│   ├── server.py            # FastAPI web server
│   ├── core.py              # Main analysis orchestrator
│   ├── decision.py          # Analysis method selection
│   ├── heuristics.py        # Rule-based quality scoring
│   ├── adapters/            # Analysis method adapters
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract base adapter
│   │   ├── heuristic_adapter.py
│   │   ├── local_model.py   # Local LLM integration
│   │   └── copilot_proxy.py # GitHub Copilot proxy
│   └── templates/           # Jinja2 templates
├── tests/                   # Test suite
├── docker/                  # Docker configuration
└── docs/                    # Documentation
```

## Analysis Methods

### Heuristic Analysis
- Rule-based scoring using predefined quality metrics
- Fast and lightweight, no external dependencies
- Good for basic quality checks

### Local LLM Analysis
- Uses local LLM models (e.g., Llama.cpp, Ollama)
- More sophisticated analysis with natural language understanding
- Requires local LLM setup

### Copilot Proxy Analysis
- Integrates with GitHub Copilot API
- Advanced AI-powered analysis
- Requires GitHub token and API access

## Development

### Setup

```bash

# Install development dependencies
make dev-install

# Run tests
make test

# Run linting
make lint

# Format code
make format
```

### Adding New Adapters

1. Create a new adapter class inheriting from `BaseAnalysisAdapter`
2. Implement the `analyze` method
3. Add the adapter to the factory in `adapters/__init__.py`
4. Add configuration options if needed

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_heuristics.py
```

## Docker Deployment

### Single Container

```bash

docker build -t goblinmini-docqa .
docker run -p 8000:8000 goblinmini-docqa
```

### Multi-Service (with Local LLM)

```bash
docker-compose up -d
```

## API Documentation

When running the server, visit `http://localhost:8000/docs` for interactive API documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.
