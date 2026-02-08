from typing import Any, Dict, List, Optional
from .adapters.base import Adapter
from .heuristics import estimate_complexity


class DecisionRouter:
    def __init__(self, cache_client=None):
        self.cache = cache_client  # optional external cache like Redis

    def run(self, task: Dict[str, Any], adapters: Optional[List[Adapter]] = None):
        # task: {"type":..., "content":..., "files": [...]}
        mode = self.decide(task)
        if mode == "cache":
            return "cache", self.cache.get(task["id"]) if self.cache else None

        # Define adapter preferences based on the decided mode
        adapter_preference = []
        if mode == "proxy":
            adapter_preference = ["proxy", "local", "queued_local"]
        elif mode == "local":
            adapter_preference = ["local", "queued_local"]

        for adapter_type in adapter_preference:
            candidate = self._try_adapters_by_type(adapter_type, task, adapters)
            if candidate:
                return candidate

        # Fallback if no suitable adapter was found or worked
        return "heuristic", None

    def _try_adapters_by_type(
        self, adapter_type: str, task: Dict[str, Any], adapters: Optional[List[Adapter]]
    ):
        for adapter in adapters or []:
            if adapter.metadata().get("type") == adapter_type:
                try:
                    adapter.init()
                    if adapter.health_check():
                        if task.get("type") == "doc_scan" and hasattr(
                            adapter, "analyze_content"
                        ):
                            return adapter.name, adapter.analyze_content(
                                task["content"], task.get("filename")
                            )
                        return adapter.name, adapter.generate(task["content"])
                except Exception:
                    continue  # Try the next adapter
        return None

    def decide(self, task: Dict[str, Any]) -> str:
        # deterministic rules
        task_type = task.get("type", "generic")
        content = task.get("content", "") or ""
        size = len(content.encode("utf-8"))
        files = task.get("files", [])
        complexity = estimate_complexity(
            size=size, files=len(files), task_type=task_type
        )

        if task.get("force_mode") in ["local", "proxy"]:
            return task["force_mode"]

        if task.get("cache_hit"):
            return "cache"
        if size < 4000 and task_type in (
            "lint_fix",
            "format",
            "generate_snippet",
            "doc_scan",
            "create_test",
        ):
            return "local"
        if complexity >= 0.7:
            return "proxy"
        return "local"
