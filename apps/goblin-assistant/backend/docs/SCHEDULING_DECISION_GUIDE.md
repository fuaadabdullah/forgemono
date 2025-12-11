# APScheduler vs Celery vs K8s CronJob Decision Guide

## Quick Decision Rules

### Use APScheduler (with Redis locks) when

- ✅ **Runtime < 30 seconds** - Jobs complete quickly
- ✅ **Runs inside app** - No separate worker processes needed
- ✅ **Tolerant of occasional single-instance execution** - OK if job occasionally skipped
- ✅ **Simple periodic tasks** - Health checks, cleanup, metrics collection
- ✅ **No complex workflow orchestration** - Single-step tasks only

### Use Celery when

- ✅ **Runtime > 30 seconds** - Long-running tasks
- ✅ **Complex workflows** - Multi-step processes with dependencies
- ✅ **External API calls** - Tasks triggered by web requests
- ✅ **Result tracking** - Need to monitor task completion/results
- ✅ **Retry logic** - Built-in retry mechanisms for failures
- ✅ **Task queuing** - Handle spikes in task volume

### Use Kubernetes CronJob when

- ✅ **Infrastructure-level tasks** - Database backups, log rotation
- ✅ **Resource-intensive** - Need guaranteed resources (CPU/memory)
- ✅ **Independent of app lifecycle** - Should run even if app is down
- ✅ **Standard tooling** - Leverage existing K8s ecosystem
- ✅ **Multi-container jobs** - Need sidecar containers or init containers

## Task Classification Matrix

| Task Type | Runtime | Complexity | Frequency | Recommended Tool |
|-----------|---------|------------|-----------|------------------|
| Health checks | < 5s | Simple | 1-5 min | APScheduler |
| Metrics collection | < 10s | Simple | 1-15 min | APScheduler |
| Data cleanup | < 30s | Medium | 1-6 hours | APScheduler |
| Cache warming | < 30s | Medium | 5-15 min | APScheduler |
| Report generation | 30s-5m | Medium | Daily | Celery |
| Bulk data processing | 5m-1h | High | Daily/Weekly | Celery |
| API synchronization | 1m-10m | Medium | 15-60 min | Celery |
| Database backups | 5m-2h | Medium | Daily | K8s CronJob |
| Log aggregation | 1m-30m | Medium | Hourly | K8s CronJob |
| Certificate renewal | < 5m | Simple | Daily | K8s CronJob |

## Implementation Patterns

### APScheduler Pattern

```python
@with_redis_lock("task_name", ttl=300)
def my_task():
    # Task logic here
    # - Keep under 30 seconds
    # - Handle failures gracefully
    # - No external dependencies
    pass

# Schedule in scheduler.py
scheduler.add_job(my_task, "interval", minutes=5)
```

### Celery Pattern
```python

@app.task(bind=True, max_retries=3)
def my_task(self):
    try:
        # Task logic here
        # - Can be long-running
        # - Complex workflows OK
        # - Built-in retry logic
        pass
    except Exception as exc:
        self.retry(countdown=60, exc=exc)

# Call from anywhere
my_task.delay()
```

### K8s CronJob Pattern

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: my-task
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: task
            image: my-app:latest
            command: ["python", "scripts/my_task.py"]
          restartPolicy: OnFailure
```

## Migration Checklist

### From Celery to APScheduler
- [ ] Runtime < 30 seconds?
- [ ] No complex workflows?
- [ ] OK with occasional skips?
- [ ] Add Redis lock decorator
- [ ] Update scheduler registration
- [ ] Remove Celery task decorator
- [ ] Test distributed locking

### From APScheduler to Celery
- [ ] Runtime > 30 seconds?
- [ ] Need reliable execution?
- [ ] Complex error handling needed?
- [ ] Add Celery task decorator
- [ ] Update task invocation
- [ ] Configure Celery worker
- [ ] Add monitoring/alerting

### From CronJob to APScheduler
- [ ] Task runs inside app?
- [ ] No special resource requirements?
- [ ] OK with app restart delays?
- [ ] Add to scheduler registration
- [ ] Remove cron configuration
- [ ] Test with Redis locks

## Monitoring & Alerting

### APScheduler Metrics to Monitor
- `apscheduler_job_failure_total` - Job failure rate
- `apscheduler_redis_lock_failed_total` - Lock acquisition failures
- `apscheduler_job_duration_seconds` - Job execution time
- `apscheduler_missed_runs_total` - Missed scheduled runs

### Celery Metrics to Monitor
- `celery_task_failed_total` - Task failure rate
- `celery_task_runtime` - Task execution time
- `celery_worker_active_tasks` - Active worker tasks
- `celery_queue_length` - Queue backlog

### CronJob Metrics to Monitor
- Job completion status
- Pod restart counts
- Resource utilization
- Execution timing drift

## Best Practices

### APScheduler
- Always use Redis locks for multi-replica deployments
- Set appropriate TTL values (job runtime + buffer)
- Monitor lock acquisition failures
- Keep jobs idempotent
- Handle exceptions gracefully

### Celery
- Configure proper retry policies
- Monitor queue lengths
- Use result backends for tracking
- Implement circuit breakers for external services
- Set appropriate timeouts

### CronJob
- Use appropriate resource limits
- Implement proper logging
- Handle job failures with restart policies
- Consider anti-affinity for multi-node clusters
- Monitor for cron drift
