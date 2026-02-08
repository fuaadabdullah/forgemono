"""
Integration tests for health check endpoints.

Tests API endpoints with database and external service interactions.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check API endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint_basic(self, client):
        """Test basic health endpoint returns valid response."""
        response = await client.get("/health")

        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "services" in data

        # Check that services contains expected keys
        services = data["services"]
        assert "database" in services
        assert "redis" in services

    @pytest.mark.asyncio
    async def test_comprehensive_health_endpoint(self, client):
        """Test comprehensive health endpoint with all service checks."""
        response = await client.get("/")

        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data

        # Check that comprehensive health includes more detailed checks
        checks = data["checks"]
        assert "database" in checks
        assert "redis" in checks
        assert "external_services" in checks

    @pytest.mark.asyncio
    async def test_health_all_endpoint(self, client):
        """Test /health/all endpoint returns service status overview."""
        response = await client.get("/health/all")

        assert response.status_code == 200

        data = response.json()
        assert "services" in data
        assert isinstance(data["services"], list)

        # Each service should have status and details
        for service in data["services"]:
            assert "name" in service
            assert "status" in service
            assert "response_time" in service

    @pytest.mark.asyncio
    async def test_chroma_status_endpoint(self, client):
        """Test Chroma database status endpoint."""
        response = await client.get("/health/chroma/status")

        # This might return 503 if Chroma is not available, but should not be a 500 error
        assert response.status_code in [200, 503]

        data = response.json()
        assert "status" in data
        assert "chroma_available" in data

    @pytest.mark.asyncio
    async def test_cost_tracking_endpoint(self, client):
        """Test cost tracking endpoint returns cost data."""
        response = await client.get("/health/cost-tracking")

        assert response.status_code == 200

        data = response.json()
        assert "total_cost" in data
        assert "costs_by_service" in data
        assert "time_range" in data

        # Costs should be numeric
        assert isinstance(data["total_cost"], (int, float))

    @pytest.mark.asyncio
    async def test_latency_history_endpoint(self, client):
        """Test latency history endpoint for a service."""
        # Test with database service
        response = await client.get("/health/latency-history/database")

        assert response.status_code == 200

        data = response.json()
        assert "service" in data
        assert "latency_data" in data
        assert "average_latency" in data

        assert data["service"] == "database"
        assert isinstance(data["latency_data"], list)

    @pytest.mark.asyncio
    async def test_service_errors_endpoint(self, client):
        """Test service errors endpoint returns error information."""
        # Test with database service
        response = await client.get("/health/service-errors/database")

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # If there are errors, each should have proper structure
        for error in data:
            assert "timestamp" in error
            assert "error_type" in error
            assert "message" in error

    @pytest.mark.asyncio
    async def test_retest_service_endpoint(self, client):
        """Test retest service endpoint triggers new health check."""
        # Test retesting database service
        response = await client.post("/health/retest/database")

        assert response.status_code == 200

        data = response.json()
        assert "service" in data
        assert "status" in data
        assert "response_time" in data
        assert "timestamp" in data

        assert data["service"] == "database"
