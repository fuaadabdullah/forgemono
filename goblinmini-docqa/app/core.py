import os
from typing import Any, Dict, List, Optional
from .heuristics import analyze_text_heuristic
from .adapters.base import Adapter
from .decision import DecisionRouter


class DocQualityChecker:
    def __init__(
        self,
        adapters: Optional[List[Adapter]] = None,
        root_dir: Optional[str] = None,
    ):
        self.adapters = adapters or []
        self.root_dir = root_dir or os.getenv("DOCQA_ROOT", "/mnt/allowed")
        self.router = DecisionRouter()

    def analyze_content(
        self, content: str, filename: str = "content.md"
    ) -> Dict[str, Any]:
        # Quick heuristic first
        heuristic = analyze_text_heuristic(content)
        # If heuristic is high confidence, return it immediately
        if heuristic["score"] >= 80:
            return {"source": "heuristic", "heuristic": heuristic}
        # Otherwise try adapters via router
        task = {"type": "doc_scan", "content": content, "filename": filename}
        source, resp = self.router.run(task, adapters=self.adapters)
        if source == "heuristic" and resp is None:
            return {"source": "heuristic", "heuristic": heuristic}
        return {"source": source, "result": resp, "heuristic": heuristic}

    def analyze_file(self, relative_path: str) -> Dict[str, Any]:
        if ".." in relative_path or os.path.isabs(relative_path):
            raise ValueError("Invalid path")
        full = os.path.join(self.root_dir, relative_path)
        if not os.path.exists(full):
            raise FileNotFoundError(full)
        with open(full, "r", encoding="utf-8") as file_handle:
            content = file_handle.read()
        return self.analyze_content(content, filename=relative_path)
