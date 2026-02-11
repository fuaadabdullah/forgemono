import os
from dataclasses import dataclass
from functools import lru_cache


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw


@dataclass(frozen=True)
class Settings:
    redis_url: str

    queue_key: str
    job_key_prefix: str

    max_code_chars: int
    min_timeout_seconds: int
    max_timeout_seconds: int

    output_limit_bytes: int
    mem_bytes: int
    fds: int

    job_ttl_seconds: int

    run_mode: str  # queue|sync
    api_key: str

    allowed_languages: frozenset[str]


@lru_cache
def get_settings() -> Settings:
    allowed_raw = _env_str("SANDBOX_ALLOWED_LANGUAGES", "python")
    allowed = frozenset(
        {lang.strip().lower() for lang in allowed_raw.split(",") if lang.strip()}
    )

    run_mode = _env_str("SANDBOX_RUN_MODE", "queue").strip().lower()
    if run_mode not in {"queue", "sync"}:
        run_mode = "queue"

    return Settings(
        redis_url=_env_str("REDIS_URL", "redis://localhost:6379/0").strip(),
        queue_key=_env_str("SANDBOX_QUEUE_KEY", "sandbox:jobs").strip(),
        job_key_prefix=_env_str("SANDBOX_JOB_KEY_PREFIX", "sandbox:job:").strip(),
        max_code_chars=_env_int("SANDBOX_MAX_CODE_CHARS", 10_000),
        min_timeout_seconds=_env_int("SANDBOX_MIN_TIMEOUT_SECONDS", 1),
        max_timeout_seconds=_env_int("SANDBOX_MAX_TIMEOUT_SECONDS", 10),
        output_limit_bytes=_env_int("SANDBOX_OUTPUT_LIMIT_BYTES", 40_000),
        mem_bytes=_env_int("SANDBOX_MEM_BYTES", 200 * 1024 * 1024),
        fds=_env_int("SANDBOX_NOFILE", 32),
        job_ttl_seconds=_env_int("SANDBOX_JOB_TTL_SECONDS", 60 * 60),
        run_mode=run_mode,
        api_key=_env_str("SANDBOX_API_KEY", "").strip(),
        allowed_languages=allowed,
    )
