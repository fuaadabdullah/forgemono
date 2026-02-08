#!/usr/bin/env python3
"""Lightweight test to validate local inference runtime (llama-cpp-python or torch).
This script is safe to run in production; it does a small import and optionally test load.
"""

import os
import sys
import argparse


def import_check():
    ok = False
    try:
        import llama_cpp as _llama_cpp

        version = getattr(_llama_cpp, "__version__", "unknown")
        print(f"llama_cpp import OK (version={version})", file=sys.stdout)
        ok = True
    except Exception as e:
        print(f"llama_cpp not available: {e}", file=sys.stderr)

    try:
        import torch as _torch

        version = getattr(_torch, "__version__", "unknown")
        print(f"torch import OK (version={version})", file=sys.stdout)
        ok = True
    except Exception as e:
        print(f"torch not available: {e}", file=sys.stderr)

    return ok


def try_load_model(model_path):
    """Try to load model metadata; avoid heavy calls. Use llama_cpp Llama.model_info or similar."""
    try:
        from llama_cpp import Llama

        # Attempt to open model with minimal memory usage (n_ctx small)
        if not os.path.exists(model_path):
            print(f"Model path does not exist: {model_path}")
            return False
        llm = Llama(model_path=model_path)
        try:
            print("Model metadata:", llm.metadata())
        finally:
            del llm
        return True
    except Exception as e:
        print(f"Model load test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path", default=os.getenv("MODEL_PATH", "/opt/goblinmini-docqa/models")
    )
    parser.add_argument("--model-name", default=os.getenv("MODEL_NAME", ""))
    parser.add_argument(
        "--test-load",
        action="store_true",
        help="Attempt to load the model file (may be heavy)",
    )
    args = parser.parse_args()

    ok = import_check()
    if not ok:
        print(
            "No inference runtime available (neither llama_cpp nor torch).",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.test_load and args.model_name:
        model_path = os.path.join(args.model_path, args.model_name)
        if try_load_model(model_path):
            print("Model load test OK")
            sys.exit(0)
        else:
            sys.exit(3)

    print("LLM runtime check passed (imports OK)")
    sys.exit(0)


if __name__ == "__main__":
    main()
