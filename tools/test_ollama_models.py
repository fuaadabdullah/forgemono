#!/usr/bin/env python3
"""
Simple utility to test installed Ollama models by running a small prompt against each.
"""

import subprocess
import shlex
import os
import argparse

SMOKE_PROMPT = "Write a single sentence introducing yourself."  # generic prompt
CODE_PROMPT = (
    "Write a short Python function that returns 'Hello world'"  # for code models
)


def run_cmd(cmd, env=None):
    try:
        result = subprocess.run(
            shlex.split(cmd), capture_output=True, text=True, check=True, env=env
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.stderr.strip()}"


def get_installed_models():
    try:
        out = run_cmd("ollama list", env=os.environ.copy())
        lines = out.splitlines()
        if len(lines) < 2:
            return []
        models = []
        for line in lines[1:]:
            if line.strip():
                parts = line.split()
                models.append(parts[0])
        return models
    except Exception as e:
        print(f"Failed to get models: {e}")
        return []


def test_model(model_name):
    """Run a smoke test for a single model using ollama run."""
    # For code models, adjust prompt
    code_models = ["codellama", "deepseek-coder"]
    if any(cm in model_name for cm in code_models):
        prompt = CODE_PROMPT
    else:
        prompt = SMOKE_PROMPT

    # pass prompt as positional argument per ollama CLI
    cmd = f"ollama run {model_name} {shlex.quote(prompt)}"
    print(f"\n== Testing {model_name} ==")
    out = run_cmd(cmd, env=os.environ.copy())
    print(out)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple Ollama smoke tester")
    parser.add_argument("--host", help="Ollama host (overrides OLLAMA_HOST env var)")
    args = parser.parse_args()

    if args.host:
        # Set env var for subprocesses
        os.environ["OLLAMA_HOST"] = args.host

    models = get_installed_models()
    if not models:
        print("No Ollama models installed (or 'ollama' not on PATH).")
        raise SystemExit(1)

    print("Found models:")
    for m in models:
        print(" - ", m)

    results = {}
    for m in models:
        results[m] = test_model(m)

    print("\nSummary:")
    for k, v in results.items():
        summary = v[:200] + ("..." if len(v) > 200 else "")
        print(f"{k}: {summary}")

    print("\nDone")
