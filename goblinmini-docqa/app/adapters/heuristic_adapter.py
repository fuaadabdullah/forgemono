"""Heuristic adapter for rule-based analysis"""

from ..heuristics import analyze_text_heuristic


class HeuristicAdapter:
    """Adapter for heuristic-based analysis"""

    name = "heuristic"

    def __init__(self):
        pass

    def init(self):
        pass

    def health_check(self, timeout: float = 3.0) -> bool:
        return True

    def generate(self, prompt: str, **kwargs):
        result = analyze_text_heuristic(prompt)
        return {
            "content": f"Quality Score: {result['score']}/100\nReasons: {', '.join(result['reasons'])}",
            "score": result["score"],
            "reasons": result["reasons"],
        }

    def metadata(self):
        return {"name": self.name, "type": "local"}

    def shutdown(self):
        pass
