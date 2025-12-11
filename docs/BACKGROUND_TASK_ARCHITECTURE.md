# Background Task Architecture

## Overview

Goblin Assistant uses a multi-tier background task system designed to prevent conflicts and ensure reliable execution across replicas.

## Architecture

### Tier 1: APScheduler + Redis Locks (Primary)
**Purpose**: Lightweight periodic tasks that run inside the application
**Location**: `apps/goblin-assistant/backend/scheduler.py`
**Use Case**: Health checks, cleanup jobs, provider probing
**Benefits**:

- Redis distributed locks prevent duplicate execution across replicas
- Runs within app process (no external containers)
- Automatic startup/shutdown with app lifecycle

**Active Jobs**:

- `system_health_check_job` - Every minute (system resource monitoring)
- `probe_all_providers_job` - Every 5 minutes (provider health checks)
- `cleanup_expired_data_job` - Every hour (database cleanup)

### Tier 2: Celery Beat (Heavy Tasks)
**Purpose**: Resource-intensive background processing
**Location**: `apps/goblin-assistant/backend/celery_app.py`
**Use Case**: ML model training, heavy data processing
**Benefits**:

- Dedicated worker processes
- Horizontal scaling
- Complex workflow orchestration

**Current Status**: No active beat schedules (cleaned up duplicates)

### Tier 3: FastAPI BackgroundTasks (Request-Scoped)
**Purpose**: Async operations tied to HTTP requests
**Location**: Various route handlers
**Use Case**: Email sending, webhook processing
**Benefits**:

- Request lifecycle management
- Automatic cleanup on app shutdown

## Anti-Patterns (Blocked by CI)

### ❌ Multiple Schedulers for Same Job

```python
# BAD: Same job in both APScheduler and Celery
scheduler.add_job(health_check_job, 'interval', minutes=1)  # APScheduler
app.conf.beat_schedule['health-check'] = {...}  # Celery - DUPLICATE!
```

### ❌ Kubernetes CronJobs
```yaml

# BAD: External cron conflicts with in-app scheduling
apiVersion: batch/v1
kind: CronJob  # BLOCKED BY CI
```

### ❌ Uncoordinated Background Tasks

```python
# BAD: No coordination between replicas
asyncio.create_task(health_check())  # Runs on every replica
```

## Development Guidelines

### Adding New Background Tasks

1. **Choose the Right Tier**:
   - < 30 seconds runtime → APScheduler
   - > 30 seconds runtime → Celery
   - Request-scoped → FastAPI BackgroundTasks

2. **Use Redis Locks for APScheduler**:
   ```python

   @with_redis_lock('my-job-lock', timeout=30)
   def my_job():
       # Your job logic here
       pass
   ```

3. **Register in Scheduler**:

   ```python
   # In scheduler.py register_jobs()
   scheduler.add_job(
       my_job,
       'interval',
       minutes=5,
       id='my-job'
   )
   ```

4. **Test Locally**:
   ```bash

   # Run scheduler manually
   python -c "from backend.scheduler import start_scheduler; start_scheduler()"
   ```

### CI Protection

The repository includes automated checks to prevent duplicate tasks:

- **Pre-commit Hook**: `check-background-tasks` runs on every commit
- **CI Pipeline**: Background task analysis in `backend-lint-test` job
- **Detection**: Scans for duplicate job names across schedulers

Run manually:

```bash
python scripts/ci/check_background_tasks.py
```

## Migration History

### Phase 1 (Completed)
- ✅ Removed duplicate Kubernetes CronJobs
- ✅ Eliminated duplicate Celery beat schedules
- ✅ Cleaned disabled worker code
- ✅ Added CI gates and documentation

### Phase 2 (Future)
- Migrate remaining heavy tasks to appropriate schedulers
- Add monitoring dashboards
- Implement alerting for job failures

## Monitoring

Background jobs are monitored through:
- APScheduler logging (INFO level)
- Redis lock acquisition metrics
- Application health endpoints
- Structured logging with correlation IDs

## Troubleshooting

### Job Not Running
1. Check Redis connectivity
2. Verify scheduler startup logs
3. Confirm job registration in `register_jobs()`
4. Check for Redis lock conflicts

### Duplicate Execution
1. Run `python scripts/ci/check_background_tasks.py`
2. Look for jobs with same name in multiple schedulers
3. Check Redis lock configuration

### Performance Issues
1. Monitor Redis lock acquisition times
2. Check job execution duration logs
3. Consider moving heavy jobs to Celery

## Related Files

- `apps/goblin-assistant/backend/scheduler.py` - APScheduler configuration
- `apps/goblin-assistant/backend/celery_app.py` - Celery configuration
- `scripts/ci/check_background_tasks.py` - CI duplicate checker
- `background_tasks_inventory.csv` - Task inventory
