Local LLM Onboarding (Goblin Assistant)
======================================

This document describes recommended hardware, supported weight formats, download and conversion steps, and quick-start commands to run a local LLM for development and offline usage with Goblin Assistant.

Goals
-----

- Provide clear hardware guidance for local development and small servers.
- Describe supported weight formats and conversion options (HF, GGUF, GPTQ).
- Provide an automated provisioning script to download and place model files.
- Quick-start commands to run common runtimes (Ollama, llama.cpp, LM Studio).

Recommended hardware
--------------------

- Small developer laptop (CPU-only): 8+ CPU cores, 16+ GB RAM — good for tiny models (<= 3B) with quantized weights.
- Desktop with single decent GPU (e.g., NVIDIA RTX 3060 / 8GB+): OK for mid-sized models (7B) with reduced batch sizes and Q4 quantized weights.
- Heavy local inference / experimentation: NVIDIA 40-series (48GB) or multiple GPUs recommended for large models (13B+).

Notes:

- If you plan to use Apple Silicon GPU acceleration (M1/M2/M3), prefer models with GGUF/ggml builds and `llama.cpp` compiled with `-DLLAMA_METAL=on`.

Supported weight formats
------------------------

- Hugging Face Transformers (PyTorch state_dict) — used for conversion or running with `transformers`/`accelerate`.
- GGUF / GGML — efficient, often used by `llama.cpp`-based runtimes.
- GPTQ — quantized weights for larger models (Q4/Q8), often requires converter tools.

Directory layout (recommended)
-----------------------------

- `~/.cache/goblin-assistant/models/`  — default local cache (provisioning script will create).
- `goblin-assistant/models/`           — optional repo-local models directory (gitignored).

Set environment variable `LOCAL_MODEL_DIR` to override the default for your environment.

Provisioning script (quick overview)
-----------------------------------

We provide `goblin-assistant/tools/provision_local_model.sh` that:

- Downloads a model from Hugging Face (uses `huggingface-cli` if available, or `curl` with a token).
- Verifies checksum if provided (manual step currently).
- Optionally runs conversion tools (e.g., `convert-pth-to-ggml`, `gptq` quantizers) if you have them installed.
- Places the final artifact in `LOCAL_MODEL_DIR`.

Usage examples (see script for details):

```bash
# Dry-run
./goblin-assistant/tools/provision_local_model.sh --model facebook/llama-2-7b --dry-run

# Download to default cache
./goblin-assistant/tools/provision_local_model.sh --model facebook/llama-2-7b

# Override target dir
LOCAL_MODEL_DIR=~/my_models ./goblin-assistant/tools/provision_local_model.sh --model ggml-model-name
```

Conversion and Quantization
---------------------------

The provisioning script supports optional conversion and quantization flags:

- `--auto-convert`: If conversion tooling is available (e.g., `transformers` + conversion script) the script will attempt to detect and suggest conversion steps to create GGUF/GGML artifacts.
- `--quantize <level>`: If a quantizer like `gptq` is installed, the script will suggest quantization at the requested level (e.g., `q4`, `q8`).

Examples:

```bash

# Dry-run to verify conversion/quantization steps
./goblin-assistant/tools/provision_local_model.sh --model facebook/llama-2-7b --dry-run --auto-convert --quantize q4
```

If conversion or quantization tools are not installed, the script will print guidance and skip the conversion step. Typical steps to prepare conversion tooling:

- Install `transformers` for Python: `pip install transformers`.
- Install `gptq` quantization toolchain following the specific converter repo instructions (often a repo will provide a `convert_hf_to_gguf.py` script and a `gptq` converter tool).


Quick-start runtimes
--------------------

- Ollama (recommended for simplicity):
  - Install via brew on macOS: `brew install ollama`
  - Pull: `ollama pull <model>`

- llama.cpp (for GGUF/GGML):
  - Build: `git clone <https://github.com/ggerganov/llama.cpp> && cmake -B build && cmake --build build`.
  - Run: `./build/bin/llama-server -m models/<model>.gguf --port 8080`.

- LM Studio: download and use its GUI to serve models locally.

Environment variables and config
--------------------------------

- `LOCAL_MODEL_DIR` — directory to store / search local model files (default: `~/.cache/goblin-assistant/models`).
- `ENABLE_LOCAL_MODEL` — boolean to prefer local providers over cloud in routing (used by routing code).

Troubleshooting
---------------

- If the model is not discovered, check file permissions and ensure `LOCAL_MODEL_DIR` is set or the default exists.
- For GPU visibility, run `nvidia-smi` (Linux) or check `torch.cuda.is_available()` in Python.

Security
--------

- Never commit raw model weights to Git.
- Keep API keys out of source; use `.env` and environment variables.

Next steps
----------

- Use `goblin-assistant/tools/provision_local_model.sh` to automate the download and placement.
- Start the `goblin-assistant` backend and call the LLM health endpoint `/api/health/llm` to validate the model is available.
