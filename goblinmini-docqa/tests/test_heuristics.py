from app.heuristics import analyze_text_heuristic


def test_heuristic_simple():
    result = analyze_text_heuristic("hi # header\n```py\nprint(1)\n```")
    assert isinstance(result["score"], int)
