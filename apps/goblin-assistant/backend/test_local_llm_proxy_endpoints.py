import os
import sys
import pathlib
import pytest
from fastapi.testclient import TestClient

# Ensure the backend directory is importable (module names with dashes are not valid),
# so add the backend folder directly to sys.path and import the module.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import local_llm_proxy as proxy

app = proxy.app


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    monkeypatch.delenv("LOCAL_LLM_API_KEY", raising=False)
    monkeypatch.setenv(
        "OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    monkeypatch.setenv(
        "LLAMACPP_URL", os.getenv("LLAMACPP_URL", "http://localhost:8080")
    )
    yield


def test_health_endpoint():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "healthy"


def test_v1_models_dev_mode():
    client = TestClient(app)
    r = client.get("/v1/models")
    assert r.status_code == 200
    data = r.json()
    assert data.get("object") == "list"


def test_v1_generate_returns_mock_text_dev_mode():
    client = TestClient(app)
    payload = {"prompt": "Testing prompt", "max_tokens": 10}
    r = client.post("/v1/generate", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert "response" in data.get("result", {})
