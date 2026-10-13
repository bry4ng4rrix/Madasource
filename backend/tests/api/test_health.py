"""Test smoke : l'application démarre et la sonde de vivacité répond."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_live_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_live_is_documented_in_openapi() -> None:
    with TestClient(app) as client:
        schema = client.get("/api/v1/openapi.json").json()

    assert "/api/v1/health/live" in schema["paths"]


def test_openapi_is_not_served_outside_api_prefix() -> None:
    with TestClient(app) as client:
        assert client.get("/openapi.json").status_code == 404
        assert client.get("/docs").status_code == 404
