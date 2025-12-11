# Raptor Mini

A lightweight diagnostics and AI-powered documentation analysis system for the ForgeMonorepo.

## Overview

Raptor Mini provides two main capabilities:

1. **AI Documentation Analysis API**: FastAPI-based server for analyzing documentation quality using advanced language models
1. **Lightweight Diagnostics**: CPU/memory monitoring and exception tracing for Python applications

## Components

### API Server (`raptor_mini_local.py`)

- FastAPI-based local deployment equivalent to Colab notebook
- REST API for document quality analysis
- Automatic ngrok tunneling for external access
- Package management and dependency installation

### API Client (`use_raptor_api.py`)

- Python client library for interacting with Raptor Mini API
- Health checks, single/batch document analysis
- Error handling and timeout management
- Command-line interface for testing

### Diagnostics Module (`../../GoblinOS/raptor_mini.py`)

- Lightweight monitoring system integrated with GoblinOS
- INI file configuration (`config/raptor.ini`)
- CPU/memory sampling and exception tracing
- FastAPI integration decorators

### Colab Notebooks

- `raptor_mini_colab.ipynb` - Original Google Colab implementation
- `updated_raptor_mini_colab.ipynb` - Token-configured version

### Automation (`automate_raptor_colab.py`)

- Automated Colab notebook deployment
- ngrok authentication token management
- Alternative to Google Drive upload approach

### Tests

- `test_raptor.py` - Basic API functionality tests
- `test_raptor_optimization.py` - Performance optimization tests
- `test_raptor_ready.py` - Readiness validation tests

## Quick Start

### Running the API Server

```bash
# Start local Raptor Mini server
python3 raptor_mini_local.py

# The server will automatically
# - Install required dependencies
# - Set up ngrok tunneling
# - Start FastAPI server on localhost
# - Provide public URL for API access
```

### Using the API Client

```python

from use_raptor_api import RaptorMiniClient

client = RaptorMiniClient()
if client.health_check():
    result = client.analyze_document("Your document content here")
    print(f"Quality Score: {result['score']}/100")
```

### Command Line Usage

```bash
# Test API connectivity
python3 use_raptor_api.py

# Analyze documentation files
python3 use_raptor_api.py analyze docs/README.md

## Dual model orchestration

Raptor Mini supports combining a local Phi-3 model for instant dev feedback and the hosted Raptor API for production-grade polishing.

Modes:
- `phi_only`: Local Phi-3 for fast, free feedback
- `raptor_only`: Hosted Raptor API for high-quality polish
- `dual`: Run Phi-3 first; if score < threshold, polish with Raptor

Quick start:
```bash

# Start Phi-3 local model
docker-compose up -d phi3-mini
export RAPTOR_MODE=phi_only
python3 ../doc-quality/doc_quality_check.py --path ../../docs/ --mode phi_only
```

#### Soft fallback

If you want `phi_only` runs to automatically fall back to the hosted Raptor API when the local Phi-3 model is not available, enable soft fallback.

CLI:

```bash
python3 ../doc-quality/doc_quality_check.py --path ../../docs/ --mode phi_only --soft-fallback
```

Configuration (persist across runs):

```yaml

models:
  phi3:
    soft_fallback: true
```

Pre-commit / CI:

```bash
export DOC_QUALITY_SOFT_FALLBACK=true
```

This instructs the Doc Quality tool to attempt a Raptor API call when the local Phi process fails instead of failing the run.
```

## API Endpoints

### Health Check
```
GET /health
```
Returns server status and API availability.

### Document Analysis
```
POST /analyze
Content-Type: application/json

{
  "content": "Document content to analyze",
  "analysis_type": "quality_score"
}
```

### Batch Analysis
```
POST /analyze/batch
Content-Type: application/json

{
  "documents": [
    {"content": "First document", "filename": "doc1.md"},
    {"content": "Second document", "filename": "doc2.md"}
  ]
}
```

## Configuration

### API Configuration
Default settings in `use_raptor_api.py`:
```python

base_url = "<https://thomasena-auxochromic-joziah.ngrok-free.dev">
```

### Diagnostics Configuration
Create `config/raptor.ini`:

```ini
[logging]
level = INFO
file = logs/raptor.log

[performance]
enable_cpu = true
enable_memory = true
sample_rate_ms = 5000

[features]
trace_exceptions = true
enable_dev_flags = false
```

## Integration Examples

### FastAPI Application Integration

```python

from GoblinOS.raptor_mini import raptor

app = FastAPI()

@app.on_event("startup")
def startup():
    raptor.start()

@app.on_event("shutdown")
def shutdown():
    raptor.stop()

@app.post("/analyze")
@raptor.trace
def analyze_document(content: str):
    # Your analysis logic here
    return {"result": "analysis_result"}
```

### Exception Tracing

```python
from GoblinOS.raptor_mini import raptor

@raptor.trace
def critical_function():
    # Function will be monitored for exceptions
    # and performance metrics will be logged
    pass
```

## Dependencies

- Python 3.9+
- fastapi
- uvicorn
- requests
- python-multipart
- pyngrok
- psutil (optional, for diagnostics)

## Colab Deployment

### Automated Setup
```bash

python3 automate_raptor_colab.py raptor_mini_colab.ipynb YOUR_NGROK_TOKEN
```

### Manual Setup

1. Open `raptor_mini_colab.ipynb` in Google Colab
1. Replace `YOUR_NGROK_AUTH_TOKEN` with your token
1. Run all cells in sequence
1. Note the public ngrok URL for API access

## Testing

### Run All Tests

```bash
python3 -m pytest test_raptor*.py -v
```

### API Connectivity Test
```bash

python3 test_raptor.py
```

### Performance Tests

```bash
python3 test_raptor_optimization.py
```

## Troubleshooting

### API Connection Issues
- Verify ngrok tunnel is active
- Check API URL in client configuration
- Ensure server is running and accessible

### Colab Issues
- Verify ngrok authentication token
- Check Colab runtime (use GPU for better performance)
- Monitor ngrok tunnel logs for errors

### Diagnostics Issues
- Ensure `config/raptor.ini` exists
- Check file permissions for log directory
- Verify psutil installation for performance monitoring

## Architecture

```
Raptor Mini System
├── API Layer (FastAPI)
│   ├── Health checks
│   ├── Document analysis
│   └── Batch processing
├── Client Layer (Python)
│   ├── API client library
│   └── CLI interface
├── Diagnostics Layer (GoblinOS)
│   ├── Performance monitoring
│   └── Exception tracing
└── Deployment Layer
    ├── Local server
    ├── Colab notebooks
    └── Automation scripts
```

## Performance

- **Analysis Speed**: ~2-5 seconds per document
- **Batch Processing**: Up to 10 concurrent requests
- **Memory Usage**: ~200-500MB for server
- **CPU Usage**: Minimal background monitoring

## Security

- Server-side only API keys (never exposed to client)
- Input sanitization and validation
- Rate limiting via ngrok configuration
- No persistent data storage of sensitive content</content>
<parameter name="filePath">/Users/fuaadabdullah/ForgeMonorepo/tools/raptor-mini/README.md
