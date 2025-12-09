# This worker now uses Celery instead of RQ
# Start with: celery -A celery_app worker --loglevel=info --queues=default,high_priority

if __name__ == "__main__":
    # This file is now deprecated - use Celery worker command instead
    print(
        "This RQ worker is deprecated. Use: celery -A celery_app worker --loglevel=info"
    )
    print("Available queues: high_priority, default, low_priority, batch, scheduled")
