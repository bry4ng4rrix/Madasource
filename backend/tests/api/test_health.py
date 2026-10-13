"""Sondes de santé, sans base disponible."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.api


def test_live_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_503_problem_when_database_is_unreachable(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["retry-after"] == "5"
    body = response.json()
    assert body == {
        "type": "about:blank",
        "title": "Service Unavailable",
        "status": 503,
        "detail": "The database is not available.",
        "code": "SERVICE_UNAVAILABLE",
        "request_id": response.headers["x-request-id"],
    }


def test_ready_failure_does_not_reveal_connection_details(client: TestClient) -> None:
    text = client.get("/api/v1/health/ready").text

    for fragment in ("127.0.0.1", "unreachable", "unused", "asyncpg", "Errno"):
        assert fragment not in text
