from fastapi.testclient import TestClient
from app.server import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # Check that required fields are present
    assert "workers" in data
    assert "model_loaded" in data
    assert "inference_queue" in data
    assert "job_queue" in data
    assert "cpu_config" in data
    assert "rate_limits" in data
    assert "request_limits" in data
    assert "backpressure" in data
