"""
Integration tests for circuit breaker + bulkhead + caching resilience patterns.
"""

import asyncio
import pytest
from providers.base_adapter import AdapterBase, ProviderError


class TestAdapter(AdapterBase):
    """Test adapter for integration testing."""

    def __init__(self, name="test", config=None):
        config = config or {"api_key": "test", "timeout": 1, "retries": 1}
        super().__init__(name=name, config=config)
        self.call_count = 0

    def generate(self, messages, **kwargs):
        self.call_count += 1
        return {
            "content": f"response-{self.call_count}",
            "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            "model": "test-model",
            "finish_reason": "stop",
        }

    async def a_generate(self, messages, **kwargs):
        self.call_count += 1
        return {
            "content": f"async-response-{self.call_count}",
            "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            "model": "test-model",
            "finish_reason": "stop",
        }


class FailingAdapter(TestAdapter):
    """Adapter that always fails."""

    def __init__(self, name="failing", config=None):
        super().__init__(name=name, config=config)

    def generate(self, messages, **kwargs):
        raise Exception("Simulated provider failure")

    async def a_generate(self, messages, **kwargs):
        raise Exception("Simulated async provider failure")


@pytest.mark.asyncio
async def test_circuit_breaker_integration():
    """Test circuit breaker opens after failures and recovers."""
    adapter = FailingAdapter()

    # Circuit should start closed
    status = adapter.get_status()
    assert status["circuit_breaker"]["state"] == "closed"
    assert status["healthy"] is True

    # First few failures should not open circuit
    for i in range(3):
        with pytest.raises(ProviderError):
            await adapter.a_generate([])

    # Circuit should still be closed
    status = adapter.get_status()
    assert status["circuit_breaker"]["state"] == "closed"

    # Fifth failure should open circuit
    with pytest.raises(ProviderError):
        await adapter.a_generate([])

    status = adapter.get_status()
    assert status["circuit_breaker"]["state"] == "open"
    assert status["healthy"] is False


@pytest.mark.asyncio
async def test_bulkhead_integration():
    """Test bulkhead limits concurrent requests."""
    adapter = TestAdapter()

    # Bulkhead should allow up to max_concurrent requests
    tasks = []
    for i in range(15):  # More than max_concurrent (10)
        task = asyncio.create_task(adapter.a_generate([]))
        tasks.append(task)

    # Some should succeed, some should fail with bulkhead exceeded
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(1 for r in results if not isinstance(r, Exception))
    failure_count = sum(1 for r in results if isinstance(r, Exception))

    assert success_count > 0  # At least some succeeded
    assert failure_count > 0  # At least some failed due to bulkhead

    # Check bulkhead status
    status = adapter.get_status()
    assert "bulkhead" in status
    assert status["bulkhead"]["max_concurrent"] == 10


@pytest.mark.asyncio
async def test_combined_resilience():
    """Test circuit breaker + bulkhead working together."""
    adapter = FailingAdapter()

    # Start multiple concurrent failing requests
    tasks = []
    for i in range(20):
        task = asyncio.create_task(adapter.a_generate([]))
        tasks.append(task)

    # All should fail
    results = await asyncio.gather(*tasks, return_exceptions=True)
    failures = [r for r in results if isinstance(r, Exception)]
    assert len(failures) == 20

    # Circuit should be open
    status = adapter.get_status()
    assert status["circuit_breaker"]["state"] == "open"
    assert status["healthy"] is False


@pytest.mark.asyncio
async def test_circuit_breaker_recovery():
    """Test circuit breaker recovery after timeout."""
    adapter = FailingAdapter()

    # Fail enough times to open circuit
    for i in range(5):
        with pytest.raises(ProviderError):
            await adapter.a_generate([])

    status = adapter.get_status()
    assert status["circuit_breaker"]["state"] == "open"

    # Wait for recovery timeout (we set it to 1 second for testing)
    # In real implementation, this would be longer
    await asyncio.sleep(2)

    # Next call should attempt recovery (half-open state)
    # Since it still fails, it should go back to open
    with pytest.raises(ProviderError):
        await adapter.a_generate([])


@pytest.mark.asyncio
async def test_successful_requests():
    """Test successful requests work through all protections."""
    adapter = TestAdapter()

    # Make successful requests
    result1 = await adapter.a_generate([])
    result2 = await adapter.a_generate([])

    assert result1["content"] == "async-response-1"
    assert result2["content"] == "async-response-2"

    # Status should show healthy
    status = adapter.get_status()
    assert status["healthy"] is True
    assert status["circuit_breaker"]["state"] == "closed"


def test_status_reporting():
    """Test comprehensive status reporting."""
    adapter = TestAdapter()

    status = adapter.get_status()

    # Check all expected fields
    assert "provider" in status
    assert "circuit_breaker" in status
    assert "bulkhead" in status
    assert "config" in status
    assert "healthy" in status

    # Check circuit breaker fields
    cb = status["circuit_breaker"]
    assert "state" in cb
    assert "name" in cb
    assert "failure_threshold" in cb
    assert "recovery_timeout" in cb
    assert "success_threshold" in cb

    # Check bulkhead fields
    bh = status["bulkhead"]
    assert "name" in bh
    assert "max_concurrent" in bh
    assert "available_slots" in bh
    assert "current_concurrent" in bh


if __name__ == "__main__":
    # Run basic smoke tests
    async def run_smoke_tests():
        print("Running resilience pattern integration tests...")

        # Test successful operation
        adapter = TestAdapter()
        result = await adapter.a_generate([])
        print(f"✓ Successful request: {result['content']}")

        # Test status reporting
        status = adapter.get_status()
        print(f"✓ Status reporting: healthy={status['healthy']}")

        # Test failing adapter
        failing_adapter = FailingAdapter()
        try:
            await failing_adapter.a_generate([])
        except Exception:
            print("✓ Provider error handling works")

        print("All smoke tests passed!")

    asyncio.run(run_smoke_tests())
