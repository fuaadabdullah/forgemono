# Running llama.cpp (llama-server) on Google Colab

This guide describes how to run `llama.cpp` on Google Colab, download models to Google Drive, run `llama-server`, and expose the server via `ngrok` for testing.

## Quick summary

1. Mount Google Drive to persist the model file.
2. Clone and build `llama.cpp`.
3. Download a quantized GGUF model into Drive (Q2/Q3/Q4 trade-offs).
4. Run the server and tunnel with `ngrok`.
5. Test locally and via the public ngrok URL.

## Best practices & optimization

- Choose the model quantization based on use-case: Q2 for best speed and smaller size, Q4_K for better quality.
- Set `--threads` to the number of vCPUs available in Colab.
- Use `--mmap` / mmap-enabled builds for faster loads and lower memory consumption.
- Tune `-c` (context length) based on app needs; smaller context saves RAM and speeds up generation.
- Use `--cache-ram` for prompt caching if memory allows; this increases latency predictability.
- Monitor timings in server logs; look for `predicted_per_second` and `prompt_ms` values to track performance.

## Sample run (Colab / local test)

- Start the server:

```bash
nohup ./llama.cpp/llama-server --model /content/drive/MyDrive/llama_models/tinyllama.gguf --host 0.0.0.0 --port 8080 -c 2048 --threads 4 > /content/llama_server.log 2>&1 &
```

- Test with a simple POST request:

```bash
curl -X POST http://127.0.0.1:8080/completions -H "Content-Type: application/json" -d '{"prompt": "Hello from Colab", "max_tokens": 50}'
```

- To expose to the web (ngrok):

```bash
ngrok http 8080
```

## Security & tokens

- For private models on Hugging Face, run `huggingface-cli login` and paste your token into Colab. For public models, wget works fine.
- Keep Drive tokens private; if you plan to share your notebook, replace tokens with local secrets or avoid including them.

## KPI/Monitoring integration

If you want to collect KPIs (latency, success rate, tokens / second) from the Colab-deployed server, we support wiring provider-specific KPI outlets (Datadog and Prometheus pushgateway are supported by the tooling).

1. Add KPI config in `goblin-assistant/config/providers.toml` under your provider. For example:

```toml
[providers.llamacpp_colab.kpi]
enabled = true
provider = "datadog"
api_key_env = "LLAMACPP_COLAB_DATADOG_API_KEY"
endpoint = "https://api.datadoghq.com/api/v1/series"
metric_prefix = "goblin.llamacpp_colab"
tags = ["env:colab", "region:colab"]
```

2. Export the API key locally or in your runtime (do NOT commit secrets):

```bash
export LLAMACPP_COLAB_DATADOG_API_KEY=your_real_api_key_here
```

3. Test the metric send using the repo script (no secret is stored in the repo):

```bash
python3 scripts/test_send_llamacpp_kpi.py --provider llamacpp_colab
```

If you prefer Prometheus, use a pushgateway and set `provider = "prometheus"` and `endpoint` to the pushgateway address. The scripts will be extended to handle prom/pushgateway in a future change. For now, Datadog is supported for an end-to-end test.

## Next steps

- Run the `notebooks/colab_llamacpp_setup.ipynb` notebook in Google Colab end-to-end.
- Tweak model quantization and thread counts, and re-run to find optimal performance.
- After verifying, update the `scripts/colab_llamacpp_start.sh` with tuned flags and put the chosen model into Drive for reuse.
