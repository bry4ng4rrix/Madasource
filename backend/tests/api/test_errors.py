"""Format Problem Details de toutes les erreurs (error-handling.md §10)."""

import socket
from collections.abc import Iterator

import asyncpg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from starlette.exceptions import HTTPException

from app.core import exceptions
from app.db.session import DbSession
from tests.support import ALLOWED_ORIGIN

pytestmark = pytest.mark.api

PROBLEM_JSON = "application/problem+json"


class _Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str = Field(min_length=12)


class _DriverError(Exception):
    def __init__(self, sqlstate: str) -> None:
        super().__init__("driver error with internal detail")
        self.sqlstate = sqlstate


@pytest.fixture
def error_client(app: FastAPI) -> Iterator[TestClient]:
    """Application réelle, plus des routes de test qui lèvent chaque type d'erreur."""

    async def validate(credentials: _Credentials) -> dict[str, str]:
        return {"status": "ok"}

    async def raise_app_error(name: str) -> None:
        raise getattr(exceptions, name)("Explanation without sensitive data.")

    async def raise_database_error(sqlstate: str) -> None:
        raise DBAPIError("SELECT secret_column FROM t", None, _DriverError(sqlstate))

    async def raise_unexpected() -> None:
        raise RuntimeError("internal detail: /srv/app/secret.py password=hunter2")

    app.add_api_route("/api/v1/_test/validate", validate, methods=["POST"])
    app.add_api_route("/api/v1/_test/app-error/{name}", raise_app_error, methods=["GET"])
    app.add_api_route("/api/v1/_test/db-error/{sqlstate}", raise_database_error, methods=["GET"])

    async def raise_http_error(status: int) -> None:
        headers = {"WWW-Authenticate": "Bearer"}
        raise HTTPException(status, detail="framework detail", headers=headers)

    app.add_api_route("/api/v1/_test/boom", raise_unexpected, methods=["GET"])
    app.add_api_route("/api/v1/_test/http-error/{status}", raise_http_error, methods=["GET"])
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def _assert_problem(response_status: int, body: dict[str, object], code: str) -> None:
    assert body["type"] == "about:blank"
    assert body["status"] == response_status
    assert body["code"] == code


def test_unknown_route_is_a_404_problem(error_client: TestClient) -> None:
    response = error_client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"] == PROBLEM_JSON
    body = response.json()
    _assert_problem(404, body, "RESOURCE_NOT_FOUND")
    assert body["title"] == "Not Found"
    assert body["request_id"] == response.headers["x-request-id"]


def test_wrong_method_is_a_405_problem_with_allow(error_client: TestClient) -> None:
    response = error_client.post("/api/v1/health/live")

    assert response.status_code == 405
    assert response.headers["allow"] == "GET"
    _assert_problem(405, response.json(), "METHOD_NOT_ALLOWED")


def test_validation_error_lists_fields_without_the_submitted_values(
    error_client: TestClient,
) -> None:
    response = error_client.post(
        "/api/v1/_test/validate", json={"password": "tiny-pw", "role": "admin"}
    )

    assert response.status_code == 422
    assert response.headers["content-type"] == PROBLEM_JSON
    body = response.json()
    _assert_problem(422, body, "VALIDATION_ERROR")
    assert {(e["field"], e["code"]) for e in body["errors"]} == {
        ("body.password", "string_too_short"),
        ("body.role", "extra_forbidden"),
    }
    assert "tiny-pw" not in response.text
    assert "admin" not in response.text
    assert all(set(error) == {"field", "code", "message"} for error in body["errors"])


@pytest.mark.parametrize(
    ("name", "status", "code"),
    [
        ("ValidationAppError", 422, "BUSINESS_RULE_VIOLATION"),
        ("BadRequestError", 400, "BAD_REQUEST"),
        ("AuthenticationError", 401, "AUTHENTICATION_REQUIRED"),
        ("PermissionDeniedError", 403, "PERMISSION_DENIED"),
        ("NotFoundError", 404, "RESOURCE_NOT_FOUND"),
        ("ConflictError", 409, "CONFLICT"),
        ("InvalidStateTransitionError", 409, "INVALID_STATE_TRANSITION"),
        ("ConcurrentModificationError", 409, "CONCURRENT_MODIFICATION"),
        ("RateLimitedError", 429, "RATE_LIMITED"),
        ("ServiceUnavailableError", 503, "SERVICE_UNAVAILABLE"),
    ],
)
def test_app_errors_become_problems(
    error_client: TestClient, name: str, status: int, code: str
) -> None:
    response = error_client.get(f"/api/v1/_test/app-error/{name}")

    assert response.status_code == status
    assert response.headers["content-type"] == PROBLEM_JSON
    body = response.json()
    _assert_problem(status, body, code)
    assert body["detail"] == "Explanation without sensitive data."


def test_authentication_error_has_www_authenticate(error_client: TestClient) -> None:
    response = error_client.get("/api/v1/_test/app-error/AuthenticationError")

    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    ("sqlstate", "status", "code"),
    [
        ("40P01", 409, "CONCURRENT_MODIFICATION"),
        ("40001", 409, "CONCURRENT_MODIFICATION"),
        ("55P03", 409, "CONCURRENT_MODIFICATION"),
        ("57014", 503, "SERVICE_UNAVAILABLE"),
        ("08006", 503, "SERVICE_UNAVAILABLE"),
        ("28P01", 503, "SERVICE_UNAVAILABLE"),
        ("3D000", 503, "SERVICE_UNAVAILABLE"),
        ("53300", 503, "SERVICE_UNAVAILABLE"),
        ("57P01", 503, "SERVICE_UNAVAILABLE"),
        ("23505", 500, "INTERNAL_ERROR"),
    ],
)
def test_database_errors_are_translated(
    error_client: TestClient, sqlstate: str, status: int, code: str
) -> None:
    response = error_client.get(f"/api/v1/_test/db-error/{sqlstate}")

    assert response.status_code == status
    _assert_problem(status, response.json(), code)
    assert response.headers.get("retry-after") == ("5" if status == 503 else None)
    for fragment in ("secret_column", "SELECT", "internal detail", sqlstate):
        assert fragment not in response.text


def test_unexpected_error_is_a_generic_500_with_request_id_and_cors(
    error_client: TestClient,
) -> None:
    response = error_client.get("/api/v1/_test/boom", headers={"Origin": ALLOWED_ORIGIN})

    assert response.status_code == 500
    assert response.headers["content-type"] == PROBLEM_JSON
    body = response.json()
    _assert_problem(500, body, "INTERNAL_ERROR")
    assert body["detail"] == "An unexpected error occurred."
    assert body["request_id"] == response.headers["x-request-id"]
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert response.headers["x-content-type-options"] == "nosniff"
    for fragment in ("hunter2", "secret.py", "RuntimeError", "Traceback"):
        assert fragment not in response.text


def test_unexpected_error_has_no_cors_header_for_unknown_origin(error_client: TestClient) -> None:
    response = error_client.get("/api/v1/_test/boom", headers={"Origin": "https://evil.example"})

    assert response.status_code == 500
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (401, "AUTHENTICATION_REQUIRED"),
        (409, "CONFLICT"),
        (410, "RESOURCE_NOT_FOUND"),
        (418, "BAD_REQUEST"),
    ],
)
def test_framework_http_errors_keep_status_code_and_safe_headers(
    error_client: TestClient, status: int, code: str
) -> None:
    response = error_client.get(f"/api/v1/_test/http-error/{status}")

    assert response.status_code == status
    _assert_problem(status, response.json(), code)
    assert "framework detail" not in response.text
    # WWW-Authenticate est transmis quelle que soit sa casse (RFC 9110 §15.5.2).
    assert response.headers["www-authenticate"] == "Bearer"


def test_database_fallback_500_has_a_single_vary_origin(error_client: TestClient) -> None:
    response = error_client.get("/api/v1/_test/db-error/23505", headers={"Origin": ALLOWED_ORIGIN})

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert response.headers.get_list("vary") == ["Origin"]


def test_wildcard_cors_on_500_answers_star() -> None:
    from app.main import create_app
    from tests.support import make_settings

    app = create_app(make_settings(cors_allowed_origins=("*",)))

    async def boom() -> None:
        raise RuntimeError("unexpected")

    app.add_api_route("/api/v1/_test/boom", boom, methods=["GET"])
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/api/v1/_test/boom", headers={"Origin": "https://any.example"})

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "*"


def test_uuid_parsing_error_does_not_echo_the_input(app: FastAPI) -> None:
    import uuid

    async def by_id(item_id: uuid.UUID) -> dict[str, str]:
        return {"id": str(item_id)}

    app.add_api_route("/api/v1/_test/items/{item_id}", by_id, methods=["GET"])
    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/_test/items/zz-SECRET-zz")

    assert response.status_code == 422
    assert "SECRET" not in response.text
    [error] = response.json()["errors"]
    assert error == {"field": "path.item_id", "code": "uuid_parsing", "message": "Invalid value."}


def test_unreachable_database_during_a_request_is_a_503(app: FastAPI) -> None:
    async def query(session: DbSession) -> dict[str, int]:
        return {"value": (await session.execute(text("SELECT 1"))).scalar_one()}

    app.add_api_route("/api/v1/_test/query", query, methods=["GET"])
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/api/v1/_test/query")

    assert response.status_code == 503
    assert response.headers["content-type"] == PROBLEM_JSON
    assert response.headers["retry-after"] == "5"
    _assert_problem(503, response.json(), "SERVICE_UNAVAILABLE")
    assert "127.0.0.1" not in response.text


@pytest.mark.parametrize(
    "failure",
    [
        ConnectionRefusedError(111, "Connection refused"),
        OSError("Multiple exceptions: [Errno 111] ..., [Errno 99] ..."),
        socket.gaierror(-2, "Name or service not known"),
        TimeoutError(),
    ],
    ids=["refused", "all-addresses-failed", "dns-failure", "timeout"],
)
def test_database_connection_failures_are_503(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch, failure: OSError
) -> None:
    """Erreurs levées par asyncpg à l'ouverture d'une connexion, simulées sans réseau."""

    async def failing_connect(*args: object, **kwargs: object) -> None:
        raise failure

    monkeypatch.setattr(asyncpg, "connect", failing_connect)

    async def query(session: DbSession) -> dict[str, int]:
        return {"value": (await session.execute(text("SELECT 1"))).scalar_one()}

    app.add_api_route("/api/v1/_test/query", query, methods=["GET"])
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/api/v1/_test/query")
        ready = test_client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"
    _assert_problem(503, response.json(), "SERVICE_UNAVAILABLE")
    assert ready.status_code == 503
    for fragment in ("Connection refused", "Multiple exceptions", "Name or service", "127.0.0.1"):
        assert fragment not in response.text


def test_timeouts_outside_the_database_remain_500(error_client: TestClient, app: FastAPI) -> None:
    """La conversion en 503 est limitée à l'ouverture d'une connexion à la base."""

    async def file_error() -> None:
        raise FileNotFoundError("missing.pdf")

    async def other_timeout() -> None:
        raise TimeoutError

    app.add_api_route("/api/v1/_test/file-error", file_error, methods=["GET"])
    app.add_api_route("/api/v1/_test/timeout", other_timeout, methods=["GET"])

    file_response = error_client.get("/api/v1/_test/file-error")
    assert file_response.status_code == 500
    assert "missing.pdf" not in file_response.text
    assert error_client.get("/api/v1/_test/timeout").status_code == 500
