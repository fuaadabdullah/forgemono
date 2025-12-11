"""Structured JSON logging middleware for production observability.

Features:
- JSON formatted logs for easy parsing
- Request/response logging with timing
- Error tracking with stack traces
- Correlation IDs for request tracing
- OpenTelemetry trace context integration
"""

import time
import logging
import uuid
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Try to import JSON logger, fall back to standard logging if not available
try:
    from pythonjsonlogger import jsonlogger

    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False

# Try to import OpenTelemetry for trace context
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    HAS_OPENTELEMETRY = True
except ImportError:
    HAS_OPENTELEMETRY = False


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests/responses with structured JSON format."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID for request tracing
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Get request ID if available (from RequestIDMiddleware)
        request_id = getattr(request.state, "request_id", None)

        # Start timer
        start_time = time.time()

        # Extract request details
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                request_body = await request.body()
                # Store for route handlers to access
                request.state.body = request_body
            except Exception:
                pass

        # Get trace context if OpenTelemetry is available
        trace_id = None
        span_id = None
        if HAS_OPENTELEMETRY:
            try:
                current_span = trace.get_current_span()
                if current_span and current_span.get_span_context().trace_id:
                    trace_id = format(current_span.get_span_context().trace_id, "032x")
                    span_id = format(current_span.get_span_context().span_id, "016x")
            except Exception:
                pass  # Ignore trace context extraction errors

        # Log incoming request
        log_extra = {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        if trace_id:
            log_extra["trace_id"] = trace_id
            log_extra["span_id"] = span_id

        logger.info("incoming_request", extra=log_extra)

        # Process request
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log successful response
            log_extra = {
                "request_id": request_id,
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            }
            if trace_id:
                log_extra["trace_id"] = trace_id
                log_extra["span_id"] = span_id

            logger.info("request_completed", extra=log_extra)

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Log error
            log_extra = {
                "request_id": request_id,
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration * 1000, 2),
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
            if trace_id:
                log_extra["trace_id"] = trace_id
                log_extra["span_id"] = span_id

            logger.error("request_failed", extra=log_extra, exc_info=True)

            raise


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure structured JSON logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("goblin_assistant")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter - use JSON if available, otherwise standard
    if HAS_JSON_LOGGER:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
        )
    else:
        # Fallback to standard formatter with JSON-like structure
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                # Add extra fields if present
                if hasattr(record, "request_id"):
                    log_entry["request_id"] = record.request_id
                if hasattr(record, "correlation_id"):
                    log_entry["correlation_id"] = record.correlation_id
                if hasattr(record, "method"):
                    log_entry["method"] = record.method
                if hasattr(record, "path"):
                    log_entry["path"] = record.path
                if hasattr(record, "status_code"):
                    log_entry["status_code"] = record.status_code
                if hasattr(record, "duration_ms"):
                    log_entry["duration_ms"] = record.duration_ms
                return json.dumps(log_entry)

        formatter = JSONFormatter()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Global logger instance
logger = setup_logging()
