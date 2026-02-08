import os
import tempfile
import socket
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Body, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from .core import DocQualityChecker
from .adapters.copilot_proxy import CopilotProxyAdapter

# Initialize OpenTelemetry tracing
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.aiohttp import AIOHTTPClientInstrumentor
    from opentelemetry.distro import distro

    # Initialize distro
    distro.configure()

    # Create resource
    resource = Resource.create(
        {
            "service.name": "goblinmini-docqa",
            "service.version": "0.1.0",
        }
    )

    # Configure tracing
    trace.set_tracer_provider(TracerProvider(resource=resource))

    # Add OTLP trace exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4318",
        insecure=True,
    )
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Auto-instrument libraries
    HTTPXClientInstrumentor().instrument()
    AIOHTTPClientInstrumentor().instrument()

    print("✅ OpenTelemetry initialized for goblinmini-docqa")

except Exception as e:
    print(f"⚠️  OpenTelemetry not available: {e}")

# Conditionally import model adapters to avoid torch compatibility issues
import logging

logger = logging.getLogger(__name__)
try:
    from .adapters.local_model import LocalModelAdapter
    from .adapters.queued_local_model import QueuedLocalModelAdapter

    LOCAL_MODELS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️  Local model adapters not available: {e}")
    LocalModelAdapter = None
    QueuedLocalModelAdapter = None
    LOCAL_MODELS_AVAILABLE = False
from .job_queue import get_job_queue
from .jobs import analyze_content_job, analyze_file_job
from .inference_queue import InferenceQueue
from .middleware import (
    SlowAPIMiddleware,
    request_size_middleware,
    backpressure_middleware,
    advanced_rate_limit_middleware,
    init_rate_limiter,
)
from . import middleware as middleware_mod
from .metrics import (
    record_inference_request,
    record_inference_error,
    record_rate_limit_hit,
    record_copilot_usage,
    record_copilot_error,
    update_model_metrics,
    update_inference_queue_metrics,
    get_metrics,
    get_metrics_dict,
)
import redis
from dotenv import load_dotenv
import multiprocessing
import logging
import sys

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# config
API_TOKEN = os.getenv("DOCQA_TOKEN", "changeme")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ROOT_DIR = os.getenv("DOCQA_ROOT", "/mnt/allowed")
DOCQA_PORT = int(os.getenv("DOCQA_PORT", "8000"))
DOCQA_ENABLE_LOCAL_MODEL = os.getenv("DOCQA_ENABLE_LOCAL_MODEL", "True").lower() in (
    "true",
    "1",
    "yes",
    "on",
)
DOCQA_WORKERS = int(os.getenv("DOCQA_WORKERS", "1"))

# Deployment validation: Single listener rule
if DOCQA_WORKERS != 1:
    logger.warning(f"⚠️  WARNING: DOCQA_WORKERS={DOCQA_WORKERS} != 1")
    logger.warning("   This violates the single listener deployment rule!")
    logger.warning(
        "   Large models should be loaded once, not duplicated across workers."
    )
    logger.warning("   For scaling, use separate inference services instead.")
    logger.warning(
        "   Setting DOCQA_WORKERS=1 to maintain single listener architecture..."
    )
    DOCQA_WORKERS = 1

# CPU-aware threading for llama-cpp
# Reserve half the cores for other processes (system, web server, etc.)
cpu_count = multiprocessing.cpu_count()
LLAMA_N_THREADS = max(1, cpu_count // 2)
# Allow override via environment
LLAMA_N_THREADS = int(os.getenv("LLAMA_N_THREADS", LLAMA_N_THREADS))

logger.info(
    f"🔧 CPU cores detected: {cpu_count}, using {LLAMA_N_THREADS} threads for llama-cpp"
)

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
    # GPU available - can handle more concurrent inference
    DEFAULT_MAX_WORKERS = min(4, gpu_count * 2)  # 2 workers per GPU, max 4
    DEFAULT_QUEUE_SIZE = 16  # Larger queue for GPU throughput
    logger.info(
        f"🎮 GPU detected ({gpu_count} GPUs), allowing "
        f"{DEFAULT_MAX_WORKERS} concurrent workers"
    )
else:
    # CPU-only - single worker to prevent thrashing
    DEFAULT_MAX_WORKERS = 1
    DEFAULT_QUEUE_SIZE = 4  # Smaller queue for CPU
    logger.info("🖥️  CPU-only mode, single worker to prevent thrashing")

# Allow environment overrides
MAX_INFERENCE_WORKERS = int(os.getenv("MAX_INFERENCE_WORKERS", DEFAULT_MAX_WORKERS))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", DEFAULT_QUEUE_SIZE))

# Model quantization configuration for memory optimization
MODEL_QUANTIZATION = os.getenv(
    "MODEL_QUANTIZATION", "auto"
)  # auto, int4, int8, f16, f32
MODEL_PATH = os.getenv("MODEL_PATH", "/models")
MODEL_NAME = os.getenv("MODEL_NAME", "Phi-3-mini-4k.gguf")

logger.info(
    f"📊 Inference config: {MAX_INFERENCE_WORKERS} workers, queue size {MAX_QUEUE_SIZE}"
)
logger.info(
    f"🧠 Model config: {MODEL_QUANTIZATION} quantization, path: "
    f"{MODEL_PATH}/{MODEL_NAME}"
)

# Global model instance and inference queue
model_adapter = None
inference_queue = None
queued_adapter = None
model_loaded_pid = None  # Track which process loaded the model

# Global job queue
job_queue = None

# Initialize job queue at module level
try:
    from .job_queue import get_job_queue

    job_queue = get_job_queue()
    logging.getLogger(__name__).info("✅ Job queue initialized at module level")
except Exception as exc:
    logging.getLogger(__name__).warning(f"⚠️  Failed to initialize job queue: {exc}")
    job_queue = None


async def init_inference_components():
    """Initialize the model and inference queue once at startup."""
    global model_adapter, inference_queue, queued_adapter, model_loaded_pid

    # Job queue is now initialized at module level

    # Check if model is already loaded (shouldn't happen with single worker)
    if model_adapter is not None:
        logger.warning(
            (
                f"⚠️  WARNING: Model already loaded by PID {model_loaded_pid},"
                f" current PID {os.getpid()}"
            )
        )
        logger.warning("   This indicates multiple processes trying to load the model!")
        logger.warning("   Ensure DOCQA_WORKERS=1 and no other instances are running.")
        return

    try:
        # Check if local models are available
        if not LOCAL_MODELS_AVAILABLE or not DOCQA_ENABLE_LOCAL_MODEL:
            raise RuntimeError(
                "Local model adapters not available (torch or environment "
                "compatibility issue)"
            )

        # Create and initialize the local model adapter with CPU-aware threading
        model_adapter = LocalModelAdapter(
            n_threads=LLAMA_N_THREADS,
            quantization=MODEL_QUANTIZATION,
            n_gpu_layers=-1 if gpu_available else 0,  # Use GPU if available
            model_path=MODEL_PATH,
            model_name=MODEL_NAME,
        )
        model_adapter.init()  # Load model once
        model_loaded_pid = os.getpid()  # Record which process loaded it
        logger.info(
            f"✅ Model loaded by PID {model_loaded_pid}: {model_adapter.metadata()}"
        )

        # Create inference queue with the model
        def invoke_model(payload):
            """Invoke the loaded model's generate method with the given payload."""
            return model_adapter.generate(**payload)

        inference_queue = InferenceQueue(
            model_callable=invoke_model,
            max_workers=MAX_INFERENCE_WORKERS,
            max_queue=MAX_QUEUE_SIZE,
        )

        # Start the inference queue
        await inference_queue.start()
        logger.info(
            f"✅ Inference queue started: {MAX_INFERENCE_WORKERS} workers,"
            f" queue size {MAX_QUEUE_SIZE}"
        )

        # Create queued adapter for use in DocQualityChecker
        queued_adapter = QueuedLocalModelAdapter(inference_queue)

    except Exception as e:
        logger.warning(f"⚠️  Failed to initialize inference components: {e}")
        logger.warning("   Continuing without local model - proxy adapter will be used")
        # Continue without local model - proxy will handle requests


logger = logging.getLogger(__name__)

LOCKFILE_DIR = os.path.join(tempfile.gettempdir(), "goblinmini-docqa")
LOCKFILE_PATH = os.path.join(LOCKFILE_DIR, f"port-{DOCQA_PORT}.lock")


def check_port_available(port: int) -> bool:
    """Check if a port is available for binding."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("localhost", port))
            return True
        except OSError:
            return False


def create_lockfile() -> bool:
    """Create a lockfile to prevent multiple instances. Returns True if successful."""
    try:
        os.makedirs(LOCKFILE_DIR, exist_ok=True)
        if os.path.exists(LOCKFILE_PATH):
            # Check if the process is still running
            try:
                with open(LOCKFILE_PATH, "r") as lockfile:
                    pid = int(lockfile.read().strip())
                os.kill(pid, 0)  # Check if process exists
                return False  # Process is still running
            except (OSError, ValueError):
                # Process doesn't exist, remove stale lockfile
                os.remove(LOCKFILE_PATH)

        # Create new lockfile
        with open(LOCKFILE_PATH, "w") as lockfile:
            lockfile.write(str(os.getpid()))
        return True
    except Exception:
        return False


def cleanup_lockfile():
    """Remove the lockfile on shutdown."""
    try:
        if os.path.exists(LOCKFILE_PATH):
            os.remove(LOCKFILE_PATH)
    except Exception:
        pass


# Startup checks
if not check_port_available(DOCQA_PORT):
    logger.error(f"❌ Port {DOCQA_PORT} is already in use. Cannot start server.")
    sys.exit(1)

if not create_lockfile():
    logger.error(f"❌ Another instance is already running on port {DOCQA_PORT}.")
    logger.error(f"   Check lockfile: {LOCKFILE_PATH}")
    sys.exit(1)

logger.info(f"✅ Starting Goblin Mini DocQA on port {DOCQA_PORT}")
logger.info(f"   Lockfile: {LOCKFILE_PATH}")

# Redis client with error handling
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_available = True
except Exception:
    redis_client = None
    redis_available = False

# 'app' will be initialized after the lifespan function is declared


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("🚀 Starting Goblin Mini DocQA server...")

    # Initialize rate limiter
    await init_rate_limiter()
    # Ensure slowapi limiter is available on app.state (used by middleware)
    try:
        app.state.limiter = middleware_mod.limiter
    except Exception:
        logger.warning(
            "⚠️  Failed to set limiter on app.state; rate limiting may not work"
        )

    # Initialize inference components
    await init_inference_components()

    logger.info("✅ Server startup complete")

    yield

    # Shutdown - graceful cleanup
    logger.info("🛑 Shutting down Goblin Mini DocQA server...")

    # Stop inference queue gracefully
    if inference_queue and hasattr(inference_queue, "stop"):
        try:
            await inference_queue.stop()
            logger.info("✅ Inference queue stopped")
        except Exception as e:
            logger.warning(f"⚠️  Error stopping inference queue: {e}")

    # Shutdown model adapter
    if model_adapter and hasattr(model_adapter, "shutdown"):
        try:
            model_adapter.shutdown()
            logger.info("✅ Model adapter shut down")
        except Exception as e:
            logger.warning(f"⚠️  Error shutting down model adapter: {e}")

    # Clean up job queue connections
    if job_queue:
        try:
            # Give jobs a chance to complete
            logger.info("⏳ Waiting for running jobs to complete...")
            await asyncio.sleep(2)  # Brief grace period
        except Exception as e:
            logger.warning(f"⚠️  Error during job queue cleanup: {e}")

    logger.info("✅ Server shutdown complete")


app = FastAPI(title="Goblin DocQA", version="0.1.0", lifespan=lifespan)

# Instrument FastAPI app
try:
    FastAPIInstrumentor().instrument_app(app)
    print("✅ FastAPI instrumentation enabled")
except Exception as e:
    print(f"⚠️  FastAPI instrumentation failed: {e}")

# Add middleware for protection and rate limiting
app.add_middleware(SlowAPIMiddleware)
app.middleware("http")(request_size_middleware)
app.middleware("http")(backpressure_middleware)
app.middleware("http")(advanced_rate_limit_middleware)
# Ensure slowapi limiter is available on app.state synchronously for middleware
try:
    # Initialize a safe in-memory limiter immediately so middleware has a valid
    # limiter reference even if Redis initialization is deferred or fails.
    app.state.limiter = middleware_mod.Limiter(
        key_func=middleware_mod.get_remote_address,
        default_limits=[
            f"{int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', 10))}/minute",
            f"{int(os.getenv('RATE_LIMIT_REQUESTS_PER_HOUR', 100))}/hour",
        ],
        storage_uri="memory://",
    )
except Exception:
    logger.warning("Failed to attach limiter to app.state at startup")


@app.on_event("shutdown")
def shutdown_event():
    """Clean up lockfile on shutdown."""
    cleanup_lockfile()
    logger.info("🧹 Cleaned up lockfile on shutdown")


def require_token(auth: str | None):
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth")
    token = auth.split(" ", 1)[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")


class ContentPayload(BaseModel):
    filename: str | None = None
    content: str


@app.get("/health")
async def health():
    queue_info = {}
    if inference_queue:
        queue_info = {
            "queue_size": inference_queue.queue.qsize(),
            "queue_max": inference_queue.queue.maxsize,
            "workers": inference_queue.semaphore._value,
            "running": inference_queue.running,
        }

    job_queue_info = {}
    if job_queue:
        job_queue_info = job_queue.get_queue_stats()

    return {
        "status": "ok",
        "workers": DOCQA_WORKERS,
        "model_loaded": model_adapter is not None,
        "inference_queue": queue_info,
        "job_queue": job_queue_info,
        "cpu_config": {"cpu_count": cpu_count, "llama_threads": LLAMA_N_THREADS},
        "rate_limits": {
            "requests_per_minute": int(
                os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "10")
            ),
            "requests_per_hour": int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "100")),
        },
        "request_limits": {
            "max_request_size_mb": int(os.getenv("MAX_REQUEST_SIZE_MB", "50")),
        },
        "backpressure": {
            "queue_backpressure_timeout": float(
                os.getenv("QUEUE_BACKPRESSURE_TIMEOUT", "0.5")
            ),
        },
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=get_metrics(), media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@app.get("/job/{job_id}")
async def get_job_status(job_id: str, authorization: str | None = Header(None)):
    """Get the status and result of a job."""
    require_token(authorization)

    status = job_queue.get_job_status(job_id)
    return status


@app.post("/analyze/content")
async def analyze_content(
    payload: ContentPayload, authorization: str | None = Header(None)
):
    require_token(authorization)

    # Record API request metrics - will be recorded by middleware
    # record_api_request("analyze_content", "POST")

    if job_queue is None:
        raise HTTPException(status_code=503, detail="Job queue not initialized")

    # Check request size against content
    content_size_mb = len(payload.content.encode("utf-8")) / (1024 * 1024)
    max_size = int(os.getenv("MAX_REQUEST_SIZE_MB", "50"))
    if content_size_mb > max_size:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Content too large: {content_size_mb:.1f}MB exceeds {max_size}MB limit"
            ),
        )

    # Try to submit job with backpressure timeout
    try:
        # Check queue capacity before submitting
        queue_stats = job_queue.get_queue_stats()
        if queue_stats.get("queued", 0) >= queue_stats.get("max_queued", 10):
            raise HTTPException(
                status_code=429,
                detail="Server busy; job queue is full. Try again later.",
                headers={"Retry-After": "30"},
            )

        # Submit job asynchronously
        job_id = job_queue.submit_job(
            analyze_content_job,
            payload.content,
            filename=payload.filename,
            root_dir=ROOT_DIR,
        )

        # Update queue metrics after job submission
        update_inference_queue_metrics(0)

        # Return 202 Accepted with job ID
        return {
            "job_id": job_id,
            "status": "accepted",
            "message": "Document analysis job submitted successfully",
            "check_status_url": f"/job/{job_id}",
        }

    except Exception as e:
        # Record error metrics
        record_inference_error("job_submission_failed")

        # If job submission fails due to queue pressure, return 429
        if "queue" in str(e).lower() or "busy" in str(e).lower():
            raise HTTPException(
                status_code=429,
                detail="Server busy; try again later",
                headers={"Retry-After": "30"},
            )
        raise


@app.post("/analyze/file")
async def analyze_file(
    path: str = Body(..., embed=True), authorization: str | None = Header(None)
):
    require_token(authorization)

    # Record API request metrics - will be recorded by middleware
    # record_api_request("analyze_file", "POST")

    if ".." in path or os.path.isabs(path):
        raise HTTPException(status_code=400, detail="Bad path")

    # Check file size before submitting job
    full_path = os.path.join(ROOT_DIR, path)
    if os.path.exists(full_path):
        file_size_mb = os.path.getsize(full_path) / (1024 * 1024)
        max_size = int(os.getenv("MAX_REQUEST_SIZE_MB", "50"))
        if file_size_mb > max_size:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File too large: {file_size_mb:.1f}MB exceeds {max_size}MB limit"
                ),
            )

    # Try to submit job with backpressure timeout
    try:
        # Check queue capacity before submitting
        queue_stats = job_queue.get_queue_stats()
        if queue_stats.get("queued", 0) >= queue_stats.get("max_queued", 10):
            raise HTTPException(
                status_code=429,
                detail="Server busy; job queue is full. Try again later.",
                headers={"Retry-After": "30"},
            )

        # Submit job asynchronously
        job_id = job_queue.submit_job(analyze_file_job, path, root_dir=ROOT_DIR)

        # Update queue metrics after job submission
        update_inference_queue_metrics(0)

        # Return 202 Accepted with job ID
        return {
            "job_id": job_id,
            "status": "accepted",
            "message": "File analysis job submitted successfully",
            "check_status_url": f"/job/{job_id}",
        }

    except Exception as e:
        # Record error metrics
        record_inference_error("job_submission_failed")

        # If job submission fails due to queue pressure, return 429
        if "queue" in str(e).lower() or "busy" in str(e).lower():
            raise HTTPException(
                status_code=429,
                detail="Server busy; try again later",
                headers={"Retry-After": "30"},
            )
        raise
