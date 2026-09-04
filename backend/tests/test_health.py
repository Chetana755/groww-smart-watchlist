from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_status_and_version() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_unknown_route_uses_shared_error_envelope() -> None:
    response = TestClient(app).get("/api/v1/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"
