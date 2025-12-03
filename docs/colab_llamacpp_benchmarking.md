# Colab llama.cpp Server Setup & Benchmarking

This repository contains tools for running and benchmarking llama.cpp servers on Google Colab with public access via ngrok.

## Files Overview

### Colab Notebook
- `notebooks/colab_llamacpp_setup.ipynb` - Complete Colab setup with Drive persistence, ngrok tunneling, and benchmarking

### Scripts
- `scripts/colab_llamacpp_start.sh` - Automated server launcher with optimization flags
- `scripts/benchmark_llamacpp.py` - Comprehensive benchmarking tool for latency/throughput testing
- `scripts/generate_colab_link.py` - Generate shareable Colab links with embedded configuration

### Documentation
- `docs/colab_llamacpp.md` - Setup guide and optimization tips

## Quick Start

### 1. Colab Setup

1. Upload `colab_llamacpp_setup.ipynb` to Google Colab
2. Run all cells in order
3. The server will be available at the ngrok URL shown in the output

### 2. Local Benchmarking

```bash
# Install dependencies
pip install requests psutil

# Run benchmark
python3 scripts/benchmark_llamacpp.py --server-url http://localhost:8080 --threads 1,2,4,8
```

### 3. Generate Shareable Links

```bash
# Generate Colab link with ngrok config
python3 scripts/generate_colab_link.py \
  --notebook-url "https://colab.research.google.com/drive/YOUR_ID" \
  --ngrok-token "your_ngrok_token"
```

## Benchmarking Features

The `benchmark_llamacpp.py` script provides:

- **Thread Scalability Testing**: Test performance across different thread counts
- **Model Comparison**: Compare different models (requires manual server restarts)
- **Latency Measurement**: First token latency and total response time
- **Throughput Analysis**: Tokens per second calculation
- **Memory Monitoring**: Memory usage tracking (when psutil available)
- **Statistical Analysis**: Average, min/max, and standard deviation

### Example Benchmark Output

```text
Benchmarking thread scalability with prompt: 'Write a short story...'
============================================================

Testing with 1 threads...
Run 1: 2.345s (15.2 tokens/sec)
Run 2: 2.123s (16.1 tokens/sec)
Run 3: 2.456s (14.8 tokens/sec)
  Avg latency: 2.308s
  Tokens/sec: 15.4
  Tokens generated: 35.5

Testing with 2 threads...
...
```

## Colab Link Generation

The `generate_colab_link.py` script creates shareable links that:

- Embed ngrok authentication tokens
- Pre-configure server ports and model repos
- Auto-start servers when opened
- Include QR codes for easy sharing

### Example Usage

```bash
python3 scripts/generate_colab_link.py \
  --notebook-url "https://colab.research.google.com/drive/1abc123..." \
  --ngrok-token "2abcd..." \
  --model-repo "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF:q4_k_m"
```

## Optimization Tips

### Colab-Specific
- Use Colab Pro for better GPU/CPU resources
- Enable GPU runtime for GPU-accelerated models
- Keep Drive mounted for model persistence
- Use smaller quantizations (Q2_K, Q3_K_S) for faster inference

### llama.cpp Flags
- `--threads`: Match Colab's CPU cores (usually 2-8)
- `--cache-ram`: Increase for better performance (0.5-1.0)
- `--mmap`: Enable memory mapping for large models
- `--mlock`: Lock model in RAM (prevents swapping)

### Network
- Use ngrok for public access
- Consider regional ngrok servers for lower latency
- Monitor ngrok dashboard for connection limits

## Troubleshooting

### Common Issues
1. **Disk Space**: Colab has ~80GB, clear cache if needed
2. **Memory**: Use smaller models or increase swap
3. **ngrok Limits**: Free tier has time/connection limits
4. **Model Downloads**: Use `wget` for public models, `huggingface-cli` for private

### Performance Tuning
- Start with Q4_K_M quantization
- Test 1-4 threads based on model size
- Monitor memory usage with `htop` or Colab's metrics
- Use the benchmark script to find optimal settings

## Integration with Goblin Assistant

This Colab deployment integrates with your Goblin Assistant for multi-LLM routing:

1. **Ollama**: Remote model via API
2. **llama.cpp (Colab)**: Public tunnel access ⭐ *Now deployed*
3. **LMStudio**: Local GUI deployment

### API Configuration

After deploying to Colab, configure the Goblin Assistant backend:

```bash
# Configure the backend to connect to your Colab server
python3 scripts/configure_colab_llamacpp.py \
  --ngrok-url "https://your-ngrok-url.ngrok.io" \
  --model "tinyllama-1.1b-chat-v1.0.Q4_K_M" \
  --test-connection

# Restart the backend
cd goblin-assistant/api && python start_server.py
```

### Testing the Integration

```bash
# Test routing to Colab llama.cpp
curl -X POST http://localhost:8000/routing/route \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "chat",
    "payload": {
      "messages": [{"role": "user", "content": "Hello from Goblin Assistant!"}]
    }
  }'
```

### Provider Priority

The `llamacpp_colab` provider is configured with:

- **Priority Tier 0**: Highest priority for fast, free responses
- **Cost Score 0.0**: Recognized as free compute
- **Capabilities**: chat, reasoning, code
- **No CoT**: Optimized for small models

The routing system will automatically prefer the Colab deployment for supported tasks when available.
