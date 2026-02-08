import os
import pytest
import requests


def _get_headers():
    """Build headers using configured env vars for API key or Authorization"""
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("LOCAL_RAPTOR_API_KEY") or os.getenv("LOCAL_LLM_API_KEY")
    if api_key:
        headers["X-API-Key"] = api_key
    return headers


@pytest.mark.skipif(
    os.getenv("USE_LOCAL_LLM", "false").lower() != "true",
    reason="Local LLM integration test skipped unless USE_LOCAL_LLM is true",
)
def test_local_raptor_or_ollama_available():
    """Try to call local raptor or Ollama endpoints. If neither responds, fail the test (developer must pull model locally)."""
    raptor_url = os.getenv("LOCAL_RAPTOR_URL", "http://127.0.0.1:8080/v1/generate")
    ollama_url = os.getenv("LOCAL_LLM_PROXY_URL", "http://localhost:11434")
    headers = _get_headers()

    # Try raptor endpoint
    try:
        payload = {"prompt": "Hello world", "max_tokens": 10}
        r = requests.post(raptor_url, json=payload, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            assert data.get("ok") is True and "result" in data
            return
    except Exception:
        pass

    # Try Ollama OpenAI-compatible endpoint
    try:
        payload = {
            "model": "raptor-mini",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 10,
        }
        r = requests.post(
            f"{ollama_url}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=5,
        )
        if r.status_code == 200:
            data = r.json()
            assert "choices" in data and len(data["choices"]) > 0
            return
    except Exception:
        pass

    pytest.fail(
        "No local LLM endpoint responded. Ensure a local model is installed and the service is running."
    )
