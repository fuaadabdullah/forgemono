"""
Test anomaly detection integration with gateway service.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock
import sys
import os

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(__file__))

from gateway_service import get_gateway_service
from anomaly_detector import get_anomaly_detector


@pytest.mark.asyncio
async def test_anomaly_detection_integration():
    """Test that anomaly detection is properly integrated with gateway service."""

    # Mock Redis for testing
    mock_redis = AsyncMock()

    # Get services with mocked Redis
    gateway = get_gateway_service(mock_redis)
    anomaly_detector = get_anomaly_detector(mock_redis)

    # Mock the alert handler to capture alerts
    alerts_received = []

    async def mock_alert_handler(alert):
        alerts_received.append(alert)

    anomaly_detector.alert_manager.add_alert_handler(mock_alert_handler)

    # Test successful request recording
    messages = [{"role": "user", "content": "Write a Python function to sort a list"}]

    # Process request through gateway
    result = await gateway.process_request(
        messages=messages, api_key="test_key_123", max_tokens=100
    )

    print(
        f"Gateway result: intent={result.intent.value}, tokens={result.estimated_tokens}"
    )

    # Record successful usage
    await gateway.record_usage(
        "test_key_123",
        50,  # tokens used
        intent=result.intent,
        success=True,
    )

    # Check that metrics were recorded
    assert anomaly_detector.metrics.token_usage_window

    # Test failed request recording
    await gateway.record_usage(
        "test_key_123",
        0,  # no tokens used
        intent=result.intent,
        success=False,
        error_type="InternalServerError",
    )

    # Check that error was recorded
    assert anomaly_detector.metrics.error_rate_window

    print("✓ Anomaly detection integration test passed")


if __name__ == "__main__":
    asyncio.run(test_anomaly_detection_integration())
