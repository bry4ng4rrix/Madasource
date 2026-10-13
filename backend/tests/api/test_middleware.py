"""Identifiant de requête, en-têtes de sécurité, CORS, marquage DEMO."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.support import ALLOWED_ORIGIN, make_settings

pytestmark = pytest.mark.api

VALID_ID = "0199f2a4-1c44-7a51-8f0e-9a7d2b3c1e55"


def test_request_id_is_generated(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")

    assert uuid.UUID(response.headers["x-request-id"]).version == 7


def test_valid_request_id_is_echoed(client: TestClient) -> None:
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": VALID_ID})

    assert response.headers["x-request-id"] == VALID_ID


def test_invalid_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": "forged id"})

    assert response.headers["x-request-id"] != "forged id"
    assert uuid.UUID(response.headers["x-request-id"])


def test_security_headers_are_set(client: TestClient) -> None:
    headers = client.get("/api/v1/health/live").headers

    assert headers["x-content-type-options"] == "nosniff"
    assert headers["referrer-policy"] == "no-referrer"
    assert headers["cache-control"] == "no-store"
    assert "x-madasource-mode" not in headers
    assert "server" not in headers


def test_cors_preflight_for_allowed_origin(client: TestClient) -> None:
    response = client.options(
        "/api/v1/health/live",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, X-Request-ID",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "x-request-id" in response.headers


def test_cors_refuses_unknown_origin(client: TestClient) -> None:
    response = client.options(
        "/api/v1/health/live",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_simple_request_exposes_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/health/live", headers={"Origin": ALLOWED_ORIGIN})

    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "X-Request-ID" in response.headers["access-control-expose-headers"]


def test_demo_instance_marks_every_response() -> None:
    app = create_app(make_settings(app_env="demo", demo_mode=True))
    with TestClient(app) as demo_client:
        response = demo_client.get("/api/v1/health/live")

    assert response.headers["x-madasource-mode"] == "demo"
