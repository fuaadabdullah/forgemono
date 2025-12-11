from app.decision import DecisionRouter


def test_decision_local():
    router = DecisionRouter()
    task = {"type": "generate_snippet", "content": "def a(): pass"}
    assert router.decide(task) == "local"
