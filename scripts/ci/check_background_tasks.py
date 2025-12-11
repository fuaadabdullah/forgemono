#!/usr/bin/env python3
"""
Background Task Duplicate Checker

This script scans the codebase for potential duplicate background tasks
and scheduling conflicts. It should be run as part of CI to prevent
future duplicate task creation.

Checks for:
- Multiple schedulers running the same job
- Duplicate Celery beat schedules
- Conflicting Kubernetes CronJobs
- Background tasks without proper coordination
"""

import re
import sys
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class BackgroundTask:
    name: str
    location: str
    scheduler_type: str
    schedule_pattern: str = ""
    notes: str = ""


class BackgroundTaskChecker:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.tasks: List[BackgroundTask] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def scan_codebase(self) -> None:
        """Scan the entire codebase for background tasks."""
        self._scan_python_files()
        self._scan_yaml_files()
        self._scan_docker_compose()

    def _scan_python_files(self) -> None:
        """Scan Python files for background task patterns."""
        python_files = list(self.repo_root.rglob("*.py"))

        for file_path in python_files:
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue

            content = file_path.read_text(encoding="utf-8", errors="ignore")

            # APScheduler jobs
            if "@with_redis_lock" in content or "scheduler.add_job" in content:
                self._extract_apscheduler_jobs(file_path, content)

            # Celery tasks and beat schedules
            if "celery_app" in str(file_path) or "beat_schedule" in content:
                self._extract_celery_schedules(file_path, content)

            # FastAPI BackgroundTasks
            if "BackgroundTasks" in content and "add_task" in content:
                self._extract_fastapi_background_tasks(file_path, content)

    def _scan_yaml_files(self) -> None:
        """Scan YAML files for Kubernetes CronJobs."""
        yaml_files = list(self.repo_root.rglob("*.yaml")) + list(
            self.repo_root.rglob("*.yml")
        )

        for file_path in yaml_files:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            if "kind: CronJob" in content or "schedule:" in content:
                self._extract_kubernetes_cronjobs(file_path, content)

    def _scan_docker_compose(self) -> None:
        """Scan docker-compose files for scheduled services."""
        compose_files = ["docker-compose.yml", "docker-compose.yaml"]
        for compose_file in compose_files:
            file_path = self.repo_root / compose_file
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if "celery" in content.lower():
                    self._extract_docker_celery_services(file_path, content)

    def _extract_apscheduler_jobs(self, file_path: Path, content: str) -> None:
        """Extract APScheduler jobs from Python files."""
        # Find job function definitions
        job_pattern = r"def\s+(\w+_job)\s*\("
        for match in re.finditer(job_pattern, content):
            job_name = match.group(1)
            self.tasks.append(
                BackgroundTask(
                    name=job_name,
                    location=str(file_path.relative_to(self.repo_root)),
                    scheduler_type="APScheduler",
                    notes="Redis-locked periodic job",
                )
            )

    def _extract_celery_schedules(self, file_path: Path, content: str) -> None:
        """Extract Celery beat schedules."""
        # Find beat_schedule definitions
        beat_pattern = r'"(\w+)":\s*{\s*"task":'
        for match in re.finditer(beat_pattern, content):
            task_name = match.group(1)
            self.tasks.append(
                BackgroundTask(
                    name=task_name,
                    location=str(file_path.relative_to(self.repo_root)),
                    scheduler_type="Celery Beat",
                    notes="Heavy background task",
                )
            )

    def _extract_fastapi_background_tasks(self, file_path: Path, content: str) -> None:
        """Extract FastAPI BackgroundTasks usage."""
        if "BackgroundTasks" in content:
            self.tasks.append(
                BackgroundTask(
                    name="fastapi_background_task",
                    location=str(file_path.relative_to(self.repo_root)),
                    scheduler_type="FastAPI BackgroundTasks",
                    notes="Request-scoped background task",
                )
            )

    def _extract_kubernetes_cronjobs(self, file_path: Path, content: str) -> None:
        """Extract Kubernetes CronJobs."""
        # Extract cronjob name and schedule
        name_match = re.search(r"metadata:\s*name:\s*(\S+)", content)
        schedule_match = re.search(r'schedule:\s*["\']([^"\']+)["\']', content)

        if name_match:
            job_name = name_match.group(1)
            schedule = schedule_match.group(1) if schedule_match else "unknown"
            self.tasks.append(
                BackgroundTask(
                    name=job_name,
                    location=str(file_path.relative_to(self.repo_root)),
                    scheduler_type="Kubernetes CronJob",
                    schedule_pattern=schedule,
                    notes="Containerized scheduled job",
                )
            )

    def _extract_docker_celery_services(self, file_path: Path, content: str) -> None:
        """Extract Celery services from docker-compose."""
        service_pattern = r"(\w+):\s*image:.*celery"
        for match in re.finditer(service_pattern, content, re.IGNORECASE):
            service_name = match.group(1)
            self.tasks.append(
                BackgroundTask(
                    name=service_name,
                    location=str(file_path.relative_to(self.repo_root)),
                    scheduler_type="Docker Celery Worker",
                    notes="Containerized Celery worker",
                )
            )

    def check_for_duplicates(self) -> None:
        """Check for duplicate or conflicting background tasks."""
        # Group tasks by name
        task_names: Dict[str, List[BackgroundTask]] = {}
        for task in self.tasks:
            if task.name not in task_names:
                task_names[task.name] = []
            task_names[task.name].append(task)

        # Check for exact name duplicates
        for name, tasks in task_names.items():
            if len(tasks) > 1:
                schedulers = [t.scheduler_type for t in tasks]
                if len(set(schedulers)) > 1:  # Different scheduler types
                    self.errors.append(
                        f"DUPLICATE TASK: '{name}' found in multiple schedulers: {schedulers}"
                    )
                    for task in tasks:
                        self.errors.append(
                            f"  - {task.scheduler_type} in {task.location}"
                        )

        # Check for health/probe related tasks (common duplication pattern)
        health_tasks = [
            t
            for t in self.tasks
            if "health" in t.name.lower() or "probe" in t.name.lower()
        ]
        if len(health_tasks) > 1:
            schedulers = list(set(t.scheduler_type for t in health_tasks))
            if len(schedulers) > 1:
                self.warnings.append(
                    f"POTENTIAL HEALTH TASK DUPLICATION: Found {len(health_tasks)} health/probe tasks "
                    f"across schedulers: {schedulers}"
                )

        # Check for cleanup tasks
        cleanup_tasks = [t for t in self.tasks if "cleanup" in t.name.lower()]
        if len(cleanup_tasks) > 1:
            self.warnings.append(
                f"MULTIPLE CLEANUP TASKS: Found {len(cleanup_tasks)} cleanup tasks - ensure they don't conflict"
            )

    def validate_architecture(self) -> None:
        """Validate that the background task architecture follows best practices."""
        apscheduler_tasks = [t for t in self.tasks if t.scheduler_type == "APScheduler"]
        celery_tasks = [t for t in self.tasks if t.scheduler_type == "Celery Beat"]
        k8s_cronjobs = [
            t for t in self.tasks if t.scheduler_type == "Kubernetes CronJob"
        ]

        # Warn if there are Kubernetes CronJobs (should be avoided)
        if k8s_cronjobs:
            self.warnings.append(
                f"FOUND KUBERNETES CRONJOBS: {len(k8s_cronjobs)} CronJobs detected. "
                "Prefer APScheduler with Redis locks for in-app scheduling."
            )

        # Check for proper separation
        if not apscheduler_tasks and not celery_tasks:
            self.warnings.append(
                "NO BACKGROUND TASKS FOUND: No schedulers detected in codebase"
            )

        # Ensure Celery is only used for heavy tasks
        if celery_tasks and len(celery_tasks) > 2:
            self.warnings.append(
                f"MANY CELERY TASKS: {len(celery_tasks)} Celery beat tasks found. "
                "Consider moving lightweight tasks to APScheduler."
            )

    def report(self) -> int:
        """Generate and return exit code based on findings."""
        print("🔍 Background Task Analysis Report")
        print("=" * 50)

        print(f"\n📊 Found {len(self.tasks)} background tasks:")
        for task in self.tasks:
            print(f"  • {task.name} ({task.scheduler_type}) - {task.location}")

        if self.errors:
            print(f"\n❌ CRITICAL ISSUES ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ No duplicate background tasks or architecture issues found!")

        return 1 if self.errors else 0


def main():
    """Main entry point."""
    # Get the repository root (two levels up from scripts/ci/)
    script_dir = Path(__file__).parent  # scripts/ci
    repo_root = script_dir.parent.parent  # ForgeMonorepo root

    print(f"Scanning repository root: {repo_root}")
    checker = BackgroundTaskChecker(repo_root)
    checker.scan_codebase()
    checker.check_for_duplicates()
    checker.validate_architecture()

    exit_code = checker.report()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
