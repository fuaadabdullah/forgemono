from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InMemoryRedis:
    hashes: dict[str, dict[str, str]] = field(default_factory=dict)
    lists: dict[str, list[Any]] = field(default_factory=dict)

    def ping(self) -> bool:
        return True

    def hset(self, name: str, mapping: dict[str, Any] | None = None, **kwargs):
        if mapping is None:
            mapping = {}
        h = self.hashes.setdefault(name, {})
        for k, v in mapping.items():
            h[str(k)] = "" if v is None else str(v)

    def hgetall(self, name: str) -> dict[str, str]:
        return dict(self.hashes.get(name, {}))

    def rpush(self, name: str, value: Any):
        self.lists.setdefault(name, []).append(value)

    def blpop(self, name: str, timeout: int = 0):
        q = self.lists.get(name)
        if not q:
            return None
        value = q.pop(0)
        return (name, value)

    def expire(self, name: str, ttl_seconds: int):
        # TTL is ignored in-memory.
        return True
