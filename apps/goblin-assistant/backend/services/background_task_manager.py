"""
BackgroundTaskManager Service for managing background tasks.

This service handles all background task management,
separating it from the main application logic for better organization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from contextlib import asynccontextmanager

from .scheduler import start_scheduler, stop_scheduler
from .autoscaling_service import AutoscalingService

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Service for managing background tasks and periodic operations."""

    def __init__(self):
        """Initialize the BackgroundTaskManager."""
        self.tasks: Dict[str, asyncio.Task] = {}
        self.autoscaling_service: Optional[AutoscalingService] = None
        self.scheduler_started = False

    async def start_background_tasks(self) -> None:
        """Start all background tasks."""
        logger.info("🔧 Starting background tasks...")

        try:
            # Start challenge cleanup task
            self._start_challenge_cleanup_task()

            # Start rate limiter cleanup task
            self._start_rate_limiter_cleanup_task()

            # Start autoscaling service
            await self._start_autoscaling_service()

            # Start scheduler
            self._start_scheduler()

            logger.info(f"✅ Started {len(self.tasks)} background tasks")

        except Exception as e:
            logger.error(f"❌ Failed to start background tasks: {e}")
            await self.stop_background_tasks()
            raise

    async def stop_background_tasks(self) -> None:
        """Stop all background tasks."""
        logger.info("🛑 Stopping background tasks...")

        # Stop autoscaling service
        if self.autoscaling_service:
            try:
                await self.autoscaling_service.close()
                logger.info("✅ Stopped autoscaling service")
            except Exception as e:
                logger.warning(f"⚠️  Failed to stop autoscaling service: {e}")

        # Stop scheduler
        if self.scheduler_started:
            try:
                stop_scheduler()
                logger.info("✅ Stopped scheduler")
            except Exception as e:
                logger.warning(f"⚠️  Failed to stop scheduler: {e}")

        # Cancel all tasks
        for task_name, task in self.tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"✅ Cancelled task: {task_name}")
                except Exception as e:
                    logger.warning(f"⚠️  Error cancelling task {task_name}: {e}")

        self.tasks.clear()
        logger.info("✅ All background tasks stopped")

    def _start_challenge_cleanup_task(self) -> None:
        """Start the challenge cleanup background task."""
        task = asyncio.create_task(self._challenge_cleanup_worker())
        self.tasks["challenge_cleanup"] = task
        logger.info("✅ Started challenge cleanup background task")

    def _start_rate_limiter_cleanup_task(self) -> None:
        """Start the rate limiter cleanup background task."""
        task = asyncio.create_task(self._rate_limiter_cleanup_worker())
        self.tasks["rate_limiter_cleanup"] = task
        logger.info("✅ Started rate limiter cleanup background task")

    async def _start_autoscaling_service(self) -> None:
        """Start the autoscaling service."""
        try:
            self.autoscaling_service = AutoscalingService()
            await self.autoscaling_service.initialize()
            logger.info("✅ Started autoscaling service")
        except Exception as e:
            logger.warning(f"⚠️  Failed to start autoscaling service: {e}")

    def _start_scheduler(self) -> None:
        """Start the scheduler."""
        try:
            start_scheduler()
            self.scheduler_started = True
            logger.info("✅ Started scheduler for lightweight periodic tasks")
        except Exception as e:
            logger.warning(f"⚠️  Failed to start scheduler: {e}")

    async def _challenge_cleanup_worker(self) -> None:
        """Background worker to clean up expired challenges every 10 minutes."""
        while True:
            try:
                await asyncio.sleep(600)  # Run every 10 minutes
                # Note: This would need to be implemented based on the actual challenge system
                logger.debug("Challenge cleanup worker running")
            except asyncio.CancelledError:
                logger.info("Challenge cleanup worker cancelled")
                break
            except Exception as e:
                logger.error(f"Error in challenge cleanup worker: {e}")

    async def _rate_limiter_cleanup_worker(self) -> None:
        """Background worker to clean up old rate limiter entries every 5 minutes."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                # Import limiter here to avoid circular imports
                from .middleware.rate_limiter import limiter
                limiter.cleanup_old_entries()
                logger.info("Rate limiter cleanup completed")
            except asyncio.CancelledError:
                logger.info("Rate limiter cleanup worker cancelled")
                break
            except Exception as e:
                logger.error(f"Error in rate limiter cleanup worker: {e}")

    def get_task_status(self) -> Dict[str, bool]:
        """Get status of all background tasks."""
        status = {}
        for task_name, task in self.tasks.items():
            status[task_name] = not task.done()
        return status

    def add_custom_task(self, task_name: str, task_coroutine: Callable) -> None:
        """Add a custom background task."""
        if task_name in self.tasks:
            logger.warning(f"Task {task_name} already exists, replacing...")
            self.tasks[task_name].cancel()

        task = asyncio.create_task(task_coroutine())
        self.tasks[task_name] = task
        logger.info(f"✅ Added custom background task: {task_name}")

    def remove_task(self, task_name: str) -> bool:
        """Remove a background task."""
        if task_name in self.tasks:
            task = self.tasks.pop(task_name)
            if not task.done():
                task.cancel()
                try:
                    asyncio.run(task)
                except asyncio.CancelledError:
                    pass
            logger.info(f"✅ Removed background task: {task_name}")
            return True
        return False

    def cleanup(self) -> None:
        """Clean up background task resources."""
        logger.info("Background task resources cleaned up")