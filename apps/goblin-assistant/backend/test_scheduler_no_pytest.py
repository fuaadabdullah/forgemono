#!/usr/bin/env python3
"""
Comprehensive Unit and Integration Tests for APScheduler Jobs

Tests Redis locking, job execution, error handling, and multi-instance behavior.
Uses pytest for proper test isolation and mocking.
"""

import os
import sys
import time
import asyncio
# import pytest
import redis
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Test imports
from scheduler import (
    redis_lock,
    with_redis_lock,
    create_scheduler,
    register_jobs,
    get_scheduler_status,
)
from jobs.provider_health import probe_all_providers_job, _probe_provider
from jobs.system_health import system_health_check_job
from jobs.cleanup import cleanup_expired_data_job


@pytest.fixture
def redis_client():
    """Redis client for testing."""
    return redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    with patch("database.SessionLocal") as mock_session:
        mock_instance = Mock()
        mock_session.return_value = mock_instance
        yield mock_instance


class TestRedisLock:
    """Test Redis distributed locking functionality."""

    def test_redis_lock_acquire_release(self, redis_client):
        """Test basic lock acquire and release."""
        lock_key = f"test_lock_{time.time()}"

        with redis_lock(lock_key, ttl=10) as acquired:
            assert acquired is True

            # Verify lock is held
            assert redis_client.get(lock_key) == b"1"

        # Verify lock is released
        assert redis_client.get(lock_key) is None

    def test_redis_lock_contention(self, redis_client):
        """Test lock contention between multiple instances."""
        lock_key = f"test_contention_{time.time()}"

        # First lock acquisition
        with redis_lock(lock_key, ttl=10) as acquired1:
            assert acquired1 is True

            # Second lock attempt should fail
            with redis_lock(lock_key, ttl=10) as acquired2:
                assert acquired2 is False

        # Lock should be available again
        with redis_lock(lock_key, ttl=10) as acquired3:
            assert acquired3 is True

    def test_redis_lock_ttl_expiry(self, redis_client):
        """Test lock TTL expiry."""
        lock_key = f"test_ttl_{time.time()}"

        with redis_lock(lock_key, ttl=1) as acquired:
            assert acquired is True
            assert redis_client.get(lock_key) == b"1"

        # Wait for TTL to expire
        time.sleep(1.1)

        # Lock should be available again
        with redis_lock(lock_key, ttl=10) as acquired:
            assert acquired is True


class TestSchedulerJobs:
    """Test individual scheduler jobs."""

    @patch("jobs.provider_health._probe_all_providers_async")
    def test_provider_health_job_success(self, mock_probe):
        """Test successful provider health check job."""
        mock_probe.return_value = None  # Success

        # Should not raise exception
        probe_all_providers_job()

        mock_probe.assert_called_once()

    @patch("jobs.provider_health._probe_all_providers_async")
    def test_provider_health_job_failure(self, mock_probe):
        """Test provider health check job with failure."""
        mock_probe.side_effect = Exception("Network error")

        # Should raise exception (let scheduler handle it)
        with pytest.raises(Exception, match="Network error"):
            probe_all_providers_job()

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    def test_system_health_job(self, mock_disk, mock_memory, mock_cpu):
        """Test system health check job."""
        # Mock system metrics
        mock_cpu.return_value = 45.5
        mock_memory.return_value = Mock(percent=67.8)
        mock_disk.return_value = Mock(percent=23.4)

        # Should not raise exception
        system_health_check_job()

    @patch("database.SessionLocal")
    def test_cleanup_job_success(self, mock_session):
        """Test successful cleanup job."""
        mock_db = Mock()
        mock_session.return_value = mock_db

        # Mock query results
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = None

        cleanup_expired_data_job()

        # Verify database operations
        mock_db.commit.assert_called()

    @patch("database.SessionLocal")
    def test_cleanup_job_failure(self, mock_session):
        """Test cleanup job with database failure."""
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.commit.side_effect = Exception("DB connection failed")

        with pytest.raises(Exception, match="DB connection failed"):
            cleanup_expired_data_job()


class TestSchedulerIntegration:
    """Integration tests for scheduler functionality."""

    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    @patch("scheduler.redis_client")
    def test_scheduler_creation(self, mock_redis, mock_scheduler_class):
        """Test scheduler creation and configuration."""
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler

        scheduler = create_scheduler()

        assert scheduler is not None
        mock_scheduler_class.assert_called_once()
        mock_scheduler.start.assert_not_called()  # Should be started separately

    def test_scheduler_status_not_started(self):
        """Test scheduler status when not started."""
        status = get_scheduler_status()
        assert status["status"] == "not_started"
        assert "jobs" not in status

    @patch("scheduler.scheduler")
    def test_scheduler_status_running(self, mock_scheduler):
        """Test scheduler status when running."""
        mock_scheduler.running = True
        mock_job = Mock()
        mock_job.id = "test_job"
        mock_job.name = "Test Job"
        mock_job.next_run_time = None
        mock_job.trigger = Mock()
        mock_job.trigger.__str__ = Mock(return_value="interval[0:05:00]")
        mock_scheduler.get_jobs.return_value = [mock_job]

        status = get_scheduler_status()

        assert status["status"] == "running"
        assert len(status["jobs"]) == 1
        assert status["jobs"][0]["id"] == "test_job"


class TestRedisLockDecorator:
    """Test the Redis lock decorator."""

    def test_with_redis_lock_success(self, redis_client):
        """Test decorator with successful execution."""

        @with_redis_lock("test_decorator_lock", ttl=10)
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    def test_with_redis_lock_skip(self, redis_client):
        """Test decorator skips execution when lock held."""
        lock_key = f"test_skip_{time.time()}"

        # Hold the lock
        redis_client.set(lock_key, "1", ex=10)

        @with_redis_lock(lock_key, ttl=10)
        def test_function():
            return "should_not_run"

        result = test_function()
        assert result is None  # Function should not execute

    def test_with_redis_lock_exception(self, redis_client):
        """Test decorator handles exceptions properly."""

        @with_redis_lock("test_exception_lock", ttl=10)
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()


class TestProviderProbing:
    """Test provider probing functionality."""

    @patch("database.SessionLocal")
    @patch("jobs.provider_health._probe_provider")
    def test_probe_provider_success(self, mock_probe_func, mock_session):
        """Test successful provider probing."""
        # Mock database
        mock_db = Mock()
        mock_session.return_value = mock_db

        # Mock provider
        mock_provider = Mock()
        mock_provider.id = 1
        mock_provider.name = "openai"
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_provider
        )

        # Mock successful probe
        mock_probe_func.return_value = {"status": "success"}

        result = asyncio.run(_probe_provider(mock_provider))

        assert result["status"] == "success"
        mock_probe_func.assert_called_once_with(mock_provider)

    @patch("database.SessionLocal")
    def test_probe_provider_not_found(self, mock_session):
        """Test probing non-existent provider."""
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_provider = Mock()
        mock_provider.id = 999

        result = asyncio.run(_probe_provider(mock_provider))

        assert result["status"] == "error"
        assert "not found" in result["error"]


# Legacy test functions for backward compatibility
async def test_scheduler():
    """Legacy test function for basic scheduler testing."""
    print("🧪 Testing APScheduler + Redis locks implementation...")

    try:
        # Test imports
        print("📦 Testing imports...")
        from scheduler import create_scheduler, stop_scheduler, get_scheduler_status
        from jobs.provider_health import probe_all_providers_job
        from jobs.system_health import get_system_health
        from jobs.cleanup import get_cleanup_stats

        print("✅ All imports successful")

        # Test scheduler creation
        print("🏗️  Testing scheduler creation...")
        scheduler = create_scheduler()
        print("✅ Scheduler created successfully")

        # Test job registration
        print("📋 Testing job registration...")
        from scheduler import register_jobs

        register_jobs(scheduler)
        print("✅ Jobs registered successfully")

        # Test scheduler status
        print("📊 Testing scheduler status...")
        status = get_scheduler_status()
        print(f"✅ Scheduler status: {status}")

        print("🎉 Basic tests passed!")

        # Cleanup
        stop_scheduler()
        print("🧹 Scheduler stopped")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


async def test_redis_lock():
    """Legacy test function for Redis locking."""
    print("🔒 Testing Redis lock mechanism...")

    try:
        from scheduler import redis_lock

        lock_key = "test:lock:123"

        # Test acquiring lock
        print("  - Testing lock acquisition...")
        with redis_lock(lock_key, ttl=10) as acquired:
            if acquired:
                print("    ✅ Lock acquired successfully")

                # Test that second attempt fails
                print("  - Testing lock contention...")
                with redis_lock(lock_key, ttl=10) as acquired2:
                    if not acquired2:
                        print("    ✅ Lock contention handled correctly")
                    else:
                        print("    ❌ Lock should have been contended")
                        return False
            else:
                print("    ❌ Failed to acquire lock")
                return False

        print("✅ Redis lock tests passed!")
        return True

    except Exception as e:
        print(f"❌ Redis lock test failed: {e}")
        return False


async def main():
    """Run legacy tests for backward compatibility."""
    print("🚀 Starting APScheduler tests...\n")

    # Set test environment
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("DATABASE_URL", "sqlite:///test_scheduler.db")

    results = []

    # Test Redis lock
    results.append(await test_redis_lock())

    print()

    # Test scheduler
    results.append(await test_scheduler())

    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All tests passed! APScheduler is ready to use.")
        print("\nTo use in production:")
        print("1. Install dependencies: pip install APScheduler psutil")
        print("2. Start your FastAPI app (scheduler starts automatically)")
        print("3. Monitor jobs at: GET /v1/health/scheduler/status")
    else:
        print("❌ Some tests failed. Check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    # Run pytest if available, otherwise run legacy tests
    try:
        # import pytest

        # Run pytest programmatically
        pytest.main([__file__, "-v"])
    except ImportError:
        # Fallback to legacy tests
        asyncio.run(main())
        print("🔄 Testing individual jobs...")

        # Test system health check
        print("  - Testing system health check...")
        health = get_system_health()
        print(f"    System health: {health['status']}")

        # Test cleanup stats
        print("  - Testing cleanup stats...")
        cleanup_stats = get_cleanup_stats()
        print(f"    Cleanup stats: {cleanup_stats}")

        # Test provider probe (this will be a no-op since no providers configured)
        print("  - Testing provider probe...")
        probe_all_providers_job()
        print("    Provider probe completed")
        print("    Provider probe completed")
        print("    Provider probe completed")

        print("\n" + "=" * 50)
        print("🎉 All tests passed! APScheduler is ready to use.")
        print("\nTo use in production:")
        print("1. Install dependencies: pip install APScheduler psutil")
        print("2. Start your FastAPI app (scheduler starts automatically)")
        print("3. Monitor jobs at: GET /v1/health/scheduler/status")
