from fastapi.testclient import TestClient

from ..main import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_risk_calc_long_with_target():
    payload = {
        "entry": 100.0,
        "stop": 95.0,
        "equity": 10_000.0,
        "risk_pct": 0.01,
        "target": 110.0,
    }
    r = client.post("/risk/calc", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["direction"] == "long"
    assert data["risk_per_share"] == 5.0
    assert data["risk_amount"] == 100.0  # 1% of 10k
    assert data["position_size"] == 20   # 100 / 5
    assert data["r_multiple_stop"] == -1.0
    assert data["r_multiple_target"] == 2.0  # (110-100)/5
    assert data["projected_pnl"] == 200.0    # 2R * $100


def test_risk_calc_short_with_target():
    payload = {
        "entry": 100.0,
        "stop": 105.0,
        "equity": 10_000.0,
        "risk_pct": 0.01,
        "target": 90.0,
    }
    r = client.post("/risk/calc", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["direction"] == "short"
    assert data["risk_per_share"] == 5.0
    assert data["risk_amount"] == 100.0
    assert data["position_size"] == 20
    assert data["r_multiple_stop"] == -1.0
    assert data["r_multiple_target"] == 2.0  # (100-90)/5
    assert data["projected_pnl"] == 200.0


def test_invalid_equal_entry_stop():
    payload = {
        "entry": 100.0,
        "stop": 100.0,
        "equity": 10_000.0,
        "risk_pct": 0.01,
    }
    r = client.post("/risk/calc", json=payload)
    assert r.status_code == 400

