from fastapi.testclient import TestClient

from ..main import app


client = TestClient(app)


def test_metrics_ping():
    r = client.get("/metrics/ping")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_equity_curve():
    payload = {"r": [1, -0.5, 2, -1]}
    r = client.post("/metrics/equity-curve", json=payload)
    assert r.status_code == 200
    assert r.json()["equity_curve"] == [1, 0.5, 2.5, 1.5]


def test_summary():
    payload = {"trades": [{"r_multiple": 1}, {"r_multiple": -0.5}, {"r_multiple": 2}]}
    r = client.post("/metrics/summary", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["total_trades"] == 3
    assert abs(data["win_rate"] - (2 / 3)) < 1e-6
    assert data["best_r"] == 2
    assert data["worst_r"] == -0.5
    assert abs(data["avg_r"] - ((1 - 0.5 + 2) / 3)) < 1e-6
    assert data["equity_curve"] == [1.0, 0.5, 2.5]


def test_summary_from_trades():
    payload = {
        "trades": [
            {"entry": 100, "stop": 95, "exit": 110, "direction": "long"},  # +2R
            {"entry": 100, "stop": 105, "exit": 95, "direction": "short"},  # +1R
            {"entry": 50, "stop": 55, "exit": 55, "direction": "long"},    # -1R
        ]
    }
    r = client.post("/metrics/summary-from-trades", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["total_trades"] == 3
    assert abs(data["avg_r"] - ((2 + 1 - 1) / 3)) < 1e-6
