"""Request ID middleware for generating unique request identifiers.

Features:
- Generates unique request IDs for each incoming request
- Adds request ID to request state and response headers
- Integrates with correlation ID for complete request tracing
"""

import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and attach unique request IDs to all requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in request state for access by route handlers
        request.state.request_id = request_id

        # Process the request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
