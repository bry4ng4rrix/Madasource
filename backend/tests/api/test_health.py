"""Test smoke : l'application démarre et la sonde de vivacité répond."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_live_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_live_is_documented_in_openapi() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert "/health/live" in schema["paths"]
