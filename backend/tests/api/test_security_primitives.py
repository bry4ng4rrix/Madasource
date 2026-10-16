"""Primitives HTTP du Jour 8 : taille des corps, limitation de débit, en-têtes de sécurité."""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict

from app.core.rate_limit import RateLimitRule, rate_limit
from app.main import create_app
from tests.support import DEPLOYED_DATABASE_URL, make_settings

pytestmark = pytest.mark.api

LIMIT = 1024
PROBE_RULE = RateLimitRule(name="test-probe", limit=2, window_seconds=60)


class Probe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str


@pytest.fixture
def probe_client() -> Iterator[TestClient]:
    """Application réelle (middlewares, gestionnaires d'erreurs) et deux routes d'essai."""
    app = create_app(make_settings(max_request_body_bytes=LIMIT))

    @app.post("/test-probe/body")
    async def echo(payload: Probe) -> dict[str, int]:
        return {"length": len(payload.note)}

    @app.get("/test-probe/limited", dependencies=[Depends(rate_limit(PROBE_RULE))])
    async def limited() -> dict[str, bool]:
        return {"ok": True}

    with TestClient(app) as client:
        yield client


def _assert_problem(response: Any, status: int, code: str) -> None:
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == status
    assert body["code"] == code
    assert body["request_id"] == response.headers["x-request-id"]


def test_body_within_limit_is_accepted(probe_client: TestClient) -> None:
    response = probe_client.post("/test-probe/body", json={"note": "a" * 900})

    assert response.status_code == 200
    assert response.json() == {"length": 900}


def test_body_over_declared_limit_is_refused(probe_client: TestClient) -> None:
    response = probe_client.post("/test-probe/body", json={"note": "a" * (LIMIT + 1)})

    _assert_problem(response, 413, "PAYLOAD_TOO_LARGE")
    assert response.headers["cache-control"] == "no-store"


def test_streamed_body_over_limit_is_refused(probe_client: TestClient) -> None:
    # Sans Content-Length (transfert par morceaux) : comptage au fil de la lecture.
    def chunks() -> Iterator[bytes]:
        yield b'{"note": "'
        for _ in range(4):
            yield b"a" * 400
        yield b'"}'

    response = probe_client.post(
        "/test-probe/body", content=chunks(), headers={"Content-Type": "application/json"}
    )

    _assert_problem(response, 413, "PAYLOAD_TOO_LARGE")


@pytest.mark.parametrize("declared", ["-1", "abc", "1e3"])
def test_unreadable_content_length_is_a_bad_request(
    probe_client: TestClient, declared: str
) -> None:
    response = probe_client.post(
        "/test-probe/body",
        content=b'{"note": "a"}',
        headers={"Content-Type": "application/json", "Content-Length": declared},
    )

    _assert_problem(response, 400, "BAD_REQUEST")


def test_rate_limit_returns_problem_with_retry_after(probe_client: TestClient) -> None:
    assert probe_client.get("/test-probe/limited").status_code == 200
    assert probe_client.get("/test-probe/limited").status_code == 200

    response = probe_client.get("/test-probe/limited")

    _assert_problem(response, 429, "RATE_LIMITED")
    assert 1 <= int(response.headers["retry-after"]) <= 60


def test_rate_limit_is_per_application_instance(probe_client: TestClient) -> None:
    # Chaque application (processus) a son limiteur : rien ne fuit d'un test à l'autre.
    assert probe_client.get("/test-probe/limited").status_code == 200


def test_framing_is_refused_on_every_response(client: TestClient) -> None:
    headers = client.get("/api/v1/health/live").headers

    assert headers["content-security-policy"] == "frame-ancestors 'none'"
    assert headers["x-frame-options"] == "DENY"


def test_no_hsts_outside_deployed_environments(client: TestClient) -> None:
    assert "strict-transport-security" not in client.get("/api/v1/health/live").headers


@pytest.mark.parametrize("app_env", ["staging", "production"])
def test_hsts_in_deployed_environments(app_env: str) -> None:
    origins = ("https://app.example.com",)
    app: FastAPI = create_app(
        make_settings(
            app_env=app_env, database_url=DEPLOYED_DATABASE_URL, cors_allowed_origins=origins
        )
    )
    with TestClient(app) as deployed:
        headers = deployed.get("/api/v1/health/live").headers

    assert headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"
