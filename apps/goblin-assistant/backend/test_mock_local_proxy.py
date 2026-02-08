import pytest

# Deprecated mock tests — prefer local model integration tests via `test_local_model_integration.py`.
pytest.skip(
    "Deprecated: mock-based tests replaced by real local model integration tests. See scripts/pull_ollama_model.sh.",
    allow_module_level=True,
)
