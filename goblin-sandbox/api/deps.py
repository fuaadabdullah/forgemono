from __future__ import annotations

from functools import lru_cache

import redis
from redis import Redis

from .settings import Settings, get_settings


@lru_cache
def _get_redis() -> Redis:
    settings = get_settings()
    # decode_responses=True makes Redis return str instead of bytes.
    return redis.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> Redis:
    return _get_redis()


def clear_dependency_caches_for_tests() -> None:
    """Best-effort cache clear for unit tests."""
    _get_redis.cache_clear()
    get_settings.cache_clear()
