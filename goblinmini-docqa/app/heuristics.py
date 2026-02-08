import re
from typing import Dict


def analyze_text_heuristic(text: str) -> Dict[str, int]:
    score = 0
    reasons = []
    if len(text) > 1000:
        score += 15
        reasons.append("length>1000")
    if text.count("\n#") >= 1:
        score += 10
        reasons.append("has_headers")
    if "`" in text:
        score += 10
        reasons.append("has_code_blocks")
    sentences = [sentence for sentence in re.split(r"[.!?]", text) if sentence.strip()]
    avg_words = sum(len(sentence.split()) for sentence in sentences) / (
        len(sentences) or 1
    )
    if 10 <= avg_words <= 25:
        score += 5
        reasons.append("readable_sentences")
    if len(text.split()) > 100:
        score += 5
        reasons.append("words>100")
    return {"score": min(100, score), "reasons": reasons}


def estimate_complexity(
    size: int = 0, files: int = 0, task_type: str = "generic"
) -> float:
    score = 0.0
    if files > 1:
        score += 0.4
    if task_type in ("refactor", "rewrite"):
        score += 0.3
    if "test" in task_type:
        score += 0.2
    if size > 1500:
        score += 0.3
    return min(1.0, score)
