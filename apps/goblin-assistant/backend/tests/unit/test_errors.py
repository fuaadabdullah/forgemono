"""
Tests for the standardized error handling module.
"""

import pytest
from fastapi import HTTPException
from errors import (
    create_problem_detail,
    raise_validation_error,
    raise_internal_error,
    raise_service_unavailable,
    raise_problem,
    ErrorCodes,
)


class TestProblemDetails:
    """Test Problem Details error handling."""

    def test_create_problem_detail_basic(self):
        """Test creating a basic problem detail."""
        problem = create_problem_detail(
            status=400, title="Bad Request", detail="Invalid input provided"
        )

        assert problem.status == 400
        assert problem.title == "Bad Request"
        assert problem.detail == "Invalid input provided"
        assert problem.type == "about:blank"
        assert problem.code is None

    def test_create_problem_detail_with_code(self):
        """Test creating a problem detail with error code."""
        problem = create_problem_detail(
            status=500,
            title="Internal Error",
            code=ErrorCodes.INTERNAL_ERROR,
            type_uri="https://api.goblin.fuaad.ai/errors/internal",
        )

        assert problem.status == 500
        assert problem.title == "Internal Error"
        assert problem.code == ErrorCodes.INTERNAL_ERROR
        assert problem.type == "https://api.goblin.fuaad.ai/errors/internal"

    def test_raise_validation_error(self):
        """Test raising validation error."""
        with pytest.raises(HTTPException) as exc_info:
            raise_validation_error(
                "Request validation failed", errors={"field": ["error message"]}
            )

        assert exc_info.value.status_code == 400
        problem = exc_info.value.detail
        assert problem["title"] == "Validation Error"
        assert problem["status"] == 400
        assert problem["errors"]["field"] == ["error message"]

    def test_raise_internal_error(self):
        """Test raising internal error."""
        with pytest.raises(HTTPException) as exc_info:
            raise_internal_error("Something went wrong")

        assert exc_info.value.status_code == 500
        problem = exc_info.value.detail
        assert problem["title"] == "Internal Server Error"
        assert problem["status"] == 500
        assert problem["code"] == ErrorCodes.INTERNAL_ERROR

    def test_raise_service_unavailable(self):
        """Test raising service unavailable error."""
        with pytest.raises(HTTPException) as exc_info:
            raise_service_unavailable("Database")

        assert exc_info.value.status_code == 503
        problem = exc_info.value.detail
        assert problem["title"] == "Service Unavailable"
        assert problem["status"] == 503
        assert problem["code"] == ErrorCodes.SERVICE_UNAVAILABLE

    def test_raise_problem_custom(self):
        """Test raising custom problem."""
        with pytest.raises(HTTPException) as exc_info:
            raise_problem(
                status=422,
                title="Custom Error",
                detail="Custom detail",
                code="CUSTOM_ERROR",
            )

        assert exc_info.value.status_code == 422
        problem = exc_info.value.detail
        assert problem["title"] == "Custom Error"
        assert problem["detail"] == "Custom detail"
        assert problem["code"] == "CUSTOM_ERROR"
