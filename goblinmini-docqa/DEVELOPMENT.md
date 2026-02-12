# Goblin DocQA - Development Quick Start

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/goblinmini-docqa
pip install -r requirements.txt
```

### 2. Configure Environment
```bash

cp .env.example .env

# Edit .env with your tokens and settings
```

### 3. Start Service (Development Mode)

```bash
./bin/start-dev.sh
```

### 4. Verify Metrics Endpoint
```bash

curl <http://localhost:9000/metrics>
```

### 5. Start Monitoring Stack (Optional)

```bash
cd docker
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## 📊 Monitoring URLs
- **Goblin DocQA**: http://localhost:9000
- **Metrics**: http://localhost:9000/metrics
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093
- **Grafana**: http://localhost:3000 (admin/admin)

## 🔧 Troubleshooting

### Connection Refused on /metrics
1. Check if service is running: `ps aux | grep uvicorn`
2. Check if port 8000 is bound: `lsof -i :8000`
3. Restart service: `./bin/start-dev.sh`

### Service Won't Start
1. Check environment: `cat .env`
2. Check logs: Look for error messages in terminal
3. Check dependencies: `pip list | grep fastapi`

### Metrics Not Updating
1. Verify endpoint: `curl http://localhost:8000/metrics | head -20`
2. Check Redis: `redis-cli ping` (if using Redis features)
3. Restart service to reset metrics

## 🐳 Docker Development
```bash

cd docker
docker-compose up -d

# Service will be available at http://localhost:8000
```

## 🧹 Code Style & Pre-commit

We use Black, isort, and Ruff for a consistent Python style. Please install dev tools and enable pre-commit hooks:

```bash
python3 -m pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files
```
## Optional: Local Model Support (Torch)

If you want to run local models (e.g., CPU/GPU-backed inference), install the optional dependencies:

```bash

# Option A: Use the local requirements file (includes torch + llama-cpp-python)
python3 -m pip install -r requirements-local.txt

# Option B: Use optional extras (pip install with local-model extra from pyproject)
python3 -m pip install -e '.[local-model]'
```


Notes:

- `torch` provides PyTorch support for local model adapters.
- `llama-cpp-python` is used for llama.cpp bindings and does not require torch.
- Use the method that matches your local model backend and platform.


CI will run style checks (isort/black/ruff) on push.
