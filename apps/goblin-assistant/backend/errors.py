"""
Standardized error handling using Problem Details RFC 7807.

This module provides consistent error responses across the API following
the Problem Details specification (RFC 7807).
"""

from typing import Dict, Optional, List
from fastapi import HTTPException
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class ProblemDetail(BaseModel):
    """Problem Details response model following RFC 7807."""

    type: str = Field(
        default="about:blank",
        description="A URI reference that identifies the problem type",
    )
    title: str = Field(
        ..., description="A short, human-readable summary of the problem type"
    )
    detail: Optional[str] = Field(
        default=None,
        description="A human-readable explanation specific to this occurrence of the problem",
    )
    instance: Optional[str] = Field(
        default=None,
        description="A URI reference that identifies the specific occurrence of the problem",
    )
    status: int = Field(..., description="The HTTP status code")
    errors: Optional[Dict[str, List[str]]] = Field(
        default=None, description="Field-specific validation errors"
    )
    code: Optional[str] = Field(
        default=None, description="Application-specific error code"
    )
    timestamp: Optional[str] = Field(
        default=None, description="ISO 8601 timestamp of when the error occurred"
    )


class ErrorCodes:
    """Standardized error codes for consistent error identification."""

    # Authentication & Authorization
    INVALID_API_KEY = "INVALID_API_KEY"
    MISSING_API_KEY = "MISSING_API_KEY"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # Validation
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_VALUE = "INVALID_FIELD_VALUE"
    REQUEST_TOO_LARGE = "REQUEST_TOO_LARGE"

    # Business Logic
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # System
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"


def create_problem_detail(
    status: int,
    title: str,
    detail: Optional[str] = None,
    type_uri: Optional[str] = None,
    code: Optional[str] = None,
    errors: Optional[Dict[str, List[str]]] = None,
    instance: Optional[str] = None,
) -> ProblemDetail:
    """
    Create a standardized ProblemDetail response.

    Args:
        status: HTTP status code
        title: Human-readable summary of the problem
        detail: Specific explanation of this occurrence
        type_uri: URI identifying the problem type
        code: Application-specific error code
        errors: Field-specific validation errors
        instance: URI identifying this specific occurrence

    Returns:
        ProblemDetail object
    """
    import datetime

    problem = ProblemDetail(
        type=type_uri or "about:blank",
        title=title,
        detail=detail,
        status=status,
        code=code,
        errors=errors,
        instance=instance,
        timestamp=datetime.datetime.utcnow().isoformat() + "Z",
    )

    return problem


def raise_problem(
    status: int,
    title: str,
    detail: Optional[str] = None,
    type_uri: Optional[str] = None,
    code: Optional[str] = None,
    errors: Optional[Dict[str, List[str]]] = None,
    instance: Optional[str] = None,
) -> None:
    """
    Raise an HTTPException with ProblemDetail content.

    This function creates a standardized problem detail response and raises
    an HTTPException that FastAPI will serialize as JSON.
    """
    problem = create_problem_detail(
        status=status,
        title=title,
        detail=detail,
        type_uri=type_uri,
        code=code,
        errors=errors,
        instance=instance,
    )

    raise HTTPException(status_code=status, detail=problem.model_dump())


# Convenience functions for common error types


def raise_validation_error(
    detail: str,
    errors: Optional[Dict[str, List[str]]] = None,
    instance: Optional[str] = None,
) -> None:
    """Raise a validation error (400)."""
    raise_problem(
        status=400,
        title="Validation Error",
        detail=detail,
        type_uri="https://api.goblin.fuaad.ai/errors/validation",
        code=ErrorCodes.INVALID_REQUEST,
        errors=errors,
        instance=instance,
    )


def raise_unauthorized(
    detail: str = "Authentication required", instance: Optional[str] = None
) -> None:
    """Raise an unauthorized error (401)."""
    raise_problem(
        status=401,
        title="Unauthorized",
        detail=detail,
        type_uri="https://api.goblin.fuaad.ai/errors/unauthorized",
        code=ErrorCodes.INVALID_API_KEY,
        instance=instance,
    )


def raise_forbidden(
    detail: str = "Insufficient permissions", instance: Optional[str] = None
) -> None:
    """Raise a forbidden error (403)."""
    raise_problem(
        status=403,
        title="Forbidden",
        detail=detail,
        type_uri="https://api.goblin.fuaad.ai/errors/forbidden",
        code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
        instance=instance,
    )


def raise_not_found(resource: str, instance: Optional[str] = None) -> None:
    """Raise a not found error (404)."""
    raise_problem(
        status=404,
        title="Not Found",
        detail=f"{resource} not found",
        type_uri="https://api.goblin.fuaad.ai/errors/not-found",
        instance=instance,
    )


def raise_rate_limited(
    detail: str = "Rate limit exceeded", instance: Optional[str] = None
) -> None:
    """Raise a rate limit exceeded error (429)."""
    raise_problem(
        status=429,
        title="Too Many Requests",
        detail=detail,
        type_uri="https://api.goblin.fuaad.ai/errors/rate-limited",
        code=ErrorCodes.RATE_LIMIT_EXCEEDED,
        instance=instance,
    )


def raise_internal_error(
    detail: str = "An internal error occurred", instance: Optional[str] = None
) -> None:
    """Raise an internal server error (500)."""
    logger.error(f"Internal error: {detail}", extra={"instance": instance})
    raise_problem(
        status=500,
        title="Internal Server Error",
        detail=detail,
        type_uri="https://api.goblin.fuaad.ai/errors/internal",
        code=ErrorCodes.INTERNAL_ERROR,
        instance=instance,
    )


def raise_service_unavailable(service: str, instance: Optional[str] = None) -> None:
    """Raise a service unavailable error (503)."""
    raise_problem(
        status=503,
        title="Service Unavailable",
        detail=f"{service} is currently unavailable",
        type_uri="https://api.goblin.fuaad.ai/errors/service-unavailable",
        code=ErrorCodes.SERVICE_UNAVAILABLE,
        instance=instance,
    )
