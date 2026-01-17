# app/jobs.py
"""
Job definitions for RQ workers.
These functions are executed asynchronously by RQ workers.
"""

import os
import time
from typing import Dict, Any
from .core import DocQualityChecker
from .adapters.copilot_proxy import CopilotProxyAdapter
from .adapters.local_model import LocalModelAdapter
from .adapters.queued_local_model import QueuedLocalModelAdapter
from .inference_queue import InferenceQueue
from .metrics import (
    record_inference_request,
    record_inference_error,
)
import multiprocessing
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global variables for model and queue (initialized once per worker)
_model_adapter = None
_inference_queue = None
_queued_adapter = None


def _init_model_components():
    """Initialize model components once per worker process."""
    global _model_adapter, _inference_queue, _queued_adapter

    if _model_adapter is not None:
        return  # Already initialized

    try:
        # CPU-aware threading for llama-cpp
        cpu_count = multiprocessing.cpu_count()
        LLAMA_N_THREADS = max(1, cpu_count // 2)
        LLAMA_N_THREADS = int(os.getenv("LLAMA_N_THREADS", LLAMA_N_THREADS))

        # GPU detection and adaptive worker configuration
        gpu_available = False
        gpu_count = 0
        try:
            import torch

            gpu_available = torch.cuda.is_available()
            gpu_count = torch.cuda.device_count() if gpu_available else 0
        except ImportError:
            pass

        # Adaptive worker configuration based on hardware
        if gpu_available and gpu_count > 0:
            DEFAULT_MAX_WORKERS = min(4, gpu_count * 2)
            DEFAULT_QUEUE_SIZE = 16
        else:
            DEFAULT_MAX_WORKERS = 1
            DEFAULT_QUEUE_SIZE = 4

        MAX_INFERENCE_WORKERS = int(
            os.getenv("MAX_INFERENCE_WORKERS", DEFAULT_MAX_WORKERS)
        )
        MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", DEFAULT_QUEUE_SIZE))

        # Model quantization configuration
        MODEL_QUANTIZATION = os.getenv("MODEL_QUANTIZATION", "auto")
        MODEL_PATH = os.getenv("MODEL_PATH", "/models")
        MODEL_NAME = os.getenv("MODEL_NAME", "Phi-3-mini-4k.gguf")

        # Create and initialize the local model adapter
        _model_adapter = LocalModelAdapter(
            n_threads=LLAMA_N_THREADS,
            quantization=MODEL_QUANTIZATION,
            n_gpu_layers=-1 if gpu_available else 0,
            model_path=MODEL_PATH,
            model_name=MODEL_NAME,
        )
        _model_adapter.init()

        # Create inference queue
        def invoke_model(payload):
            return _model_adapter.generate(**payload)

        _inference_queue = InferenceQueue(
            model_callable=invoke_model,
            max_workers=MAX_INFERENCE_WORKERS,
            max_queue=MAX_QUEUE_SIZE,
        )

        # Start the inference queue
        import asyncio

        asyncio.run(_inference_queue.start())

        # Create queued adapter
        _queued_adapter = QueuedLocalModelAdapter(_inference_queue)

        print(f"✅ Worker model initialized: {_model_adapter.metadata()}")

    except Exception as e:
        print(f"⚠️  Failed to initialize model in worker: {e}")
        # Continue without local model - proxy will be used
        _model_adapter = None
        _inference_queue = None
        _queued_adapter = None


def analyze_content_job(
    content: str, filename: str = None, root_dir: str = None
) -> Dict[str, Any]:
    """Job function to analyze document content asynchronously."""
    # Initialize model components if needed
    _init_model_components()

    # Set up adapters
    adapters = []
    if _queued_adapter:
        adapters.append(_queued_adapter)

    # Proxy adapter (fallback)
    proxy = CopilotProxyAdapter()
    adapters.append(proxy)

    # Create checker and run analysis with metrics
    checker = DocQualityChecker(adapters=adapters, root_dir=root_dir or "/mnt/allowed")

    try:
        # Record inference request start
        record_inference_request("proxy", "analyze_content", "started")

        start_time = time.time()
        result = checker.analyze_content(content, filename=filename or "content.md")
        duration = time.time() - start_time

        # Record successful inference with duration
        record_inference_request(
            "proxy", "analyze_content", "success", duration=duration
        )

        return result

    except Exception:
        # Record inference error
        record_inference_error("proxy", "analyze_content", "job_failed")
        raise


def analyze_file_job(file_path: str, root_dir: str = None) -> Dict[str, Any]:
    """Job function to analyze a file asynchronously."""
    # Initialize model components if needed
    _init_model_components()

    # Validate path
    if ".." in file_path or os.path.isabs(file_path):
        raise ValueError("Invalid file path")

    # Set up adapters
    adapters = []
    if _queued_adapter:
        adapters.append(_queued_adapter)

    # Proxy adapter (fallback)
    proxy = CopilotProxyAdapter()
    adapters.append(proxy)

    # Create checker and run analysis with metrics
    checker = DocQualityChecker(adapters=adapters, root_dir=root_dir or "/mnt/allowed")

    try:
        # Record inference request start
        record_inference_request("proxy", "analyze_file", "started")

        start_time = time.time()
        result = checker.analyze_file(file_path)
        duration = time.time() - start_time

        # Record successful inference with duration
        record_inference_request("proxy", "analyze_file", "success", duration=duration)

        return result

    except Exception:
        # Record inference error
        record_inference_error("proxy", "analyze_file", "job_failed")
        raise


def health_check_job() -> Dict[str, Any]:
    """Job function for worker health checks."""
    _init_model_components()

    health_info = {
        "worker_pid": os.getpid(),
        "model_loaded": _model_adapter is not None,
        "inference_queue_running": _inference_queue is not None
        and _inference_queue.running,
    }

    if _model_adapter:
        health_info["model_metadata"] = _model_adapter.metadata()

    if _inference_queue:
        health_info["queue_info"] = {
            "max_workers": _inference_queue.semaphore._value,
            "queue_size": _inference_queue.queue.maxsize,
            "running": _inference_queue.running,
        }

    return health_info
