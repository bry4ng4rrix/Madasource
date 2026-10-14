"""Contenu des journaux : jamais de secret, de chaîne de requête ni de message d'exception."""

import json
import logging
from collections.abc import Iterator
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError

from app.core.logging import DropServerErrorReplay, JsonFormatter, configure_logging, sanitize
from app.main import create_app
from tests.support import make_settings

pytestmark = pytest.mark.api

SENSITIVE_VALUES = ("FR7630006000011234567890189", "1250.00", "hunter2", "Failing row")


class _DriverError(Exception):
    def __init__(self) -> None:
        super().__init__("DETAIL: Failing row contains (FR7630006000011234567890189, 1250.00)")
        self.sqlstate = "23502"
        self.constraint_name = "ck_payment_records_amount_positive"


class _Payment(BaseModel):
    iban: str
    amount: str
    currency: str


@pytest.fixture
def logging_app(app: FastAPI) -> Iterator[TestClient]:
    async def boom() -> None:
        # Valeur construite à l'exécution : la pile journalisée reprend les lignes de code,
        # pas les valeurs (un littéral écrit ici apparaîtrait dans la ligne source).
        secret = "".join(["hun", "ter2"])
        raise RuntimeError(f"password={secret}")

    async def db_failure() -> None:
        raise DBAPIError("INSERT INTO payment_records ...", None, _DriverError())

    async def bad_response() -> _Payment:
        # Champ « currency » manquant : FastAPI lève ResponseValidationError, dont le
        # message recopie les données servies.
        incomplete: Any = {"iban": "FR7630006000011234567890189", "amount": "1250.00"}
        return cast("_Payment", incomplete)

    app.add_api_route("/api/v1/_test/boom", boom, methods=["GET"])
    app.add_api_route("/api/v1/_test/db-failure", db_failure, methods=["GET"])
    app.add_api_route("/api/v1/_test/bad-response", bad_response, methods=["GET"])
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def _formatted(caplog: pytest.LogCaptureFixture, logger: str) -> list[str]:
    formatter = JsonFormatter()
    return [formatter.format(record) for record in caplog.records if record.name == logger]


def test_access_log_never_contains_the_query_string(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG, logger="app.access")

    response = client.get("/api/v1/health/live?token=s3cr3t-token")

    [line] = _formatted(caplog, "app.access")
    entry = json.loads(line)
    assert entry["path"] == "/api/v1/health/live"
    assert entry["request_id"] == response.headers["x-request-id"]
    assert entry["status"] == 200
    assert "s3cr3t-token" not in line


def test_probe_access_logs_are_debug_level(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG, logger="app.access")

    client.get("/api/v1/health/live")
    client.get("/api/v1/does-not-exist")

    probe, other = (record for record in caplog.records if record.name == "app.access")
    assert probe.levelno == logging.DEBUG
    assert other.levelno == logging.INFO


@pytest.mark.parametrize(
    "path", ["/api/v1/_test/boom", "/api/v1/_test/db-failure", "/api/v1/_test/bad-response"]
)
def test_server_error_logs_contain_no_exception_message(
    logging_app: TestClient, caplog: pytest.LogCaptureFixture, path: str
) -> None:
    caplog.set_level(logging.INFO, logger="app.errors")

    response = logging_app.get(path)

    assert response.status_code == 500
    [line] = _formatted(caplog, "app.errors")
    entry = json.loads(line)
    assert entry["message"] == "unhandled_exception"
    assert entry["level"] == "ERROR"
    assert entry["request_id"] == response.headers["x-request-id"]
    assert entry["exception_types"]
    assert "exception" not in entry
    for value in SENSITIVE_VALUES:
        assert value not in line


def test_database_error_log_keeps_sqlstate_and_constraint(
    logging_app: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="app.errors")

    logging_app.get("/api/v1/_test/db-failure")

    [line] = _formatted(caplog, "app.errors")
    entry = json.loads(line)
    assert entry["sqlstate"] == "23502"


def test_response_validation_log_keeps_only_locations(
    logging_app: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="app.errors")

    logging_app.get("/api/v1/_test/bad-response")

    [line] = _formatted(caplog, "app.errors")
    entry = json.loads(line)
    assert entry["validation_errors"] == [{"loc": "response.currency", "type": "missing"}]


def test_uvicorn_replay_of_server_errors_is_dropped() -> None:
    replay = logging.makeLogRecord(
        {"name": "uvicorn.error", "msg": "Exception in ASGI application\n", "levelname": "ERROR"}
    )
    startup = logging.makeLogRecord({"name": "uvicorn.error", "msg": "Started server process"})

    assert DropServerErrorReplay().filter(replay) is False
    assert DropServerErrorReplay().filter(startup) is True


def test_configure_logging_redirects_uvicorn_once() -> None:
    configure_logging("INFO")
    configure_logging("INFO")

    error_logger = logging.getLogger("uvicorn.error")
    assert logging.getLogger("uvicorn.access").disabled is True
    assert error_logger.propagate is True
    assert sum(isinstance(f, DropServerErrorReplay) for f in error_logger.filters) == 1
    root_handlers = [
        h for h in logging.getLogger().handlers if type(h).__name__ == "_MadaSourceHandler"
    ]
    assert len(root_handlers) == 1


def test_sanitize_walks_sequences_and_hides_objects() -> None:
    assert sanitize("items", [{"password": "p1"}, ("ok", 1, {"token": "t"})]) == [
        {"password": "[REDACTED]"},
        ["ok", 1, {"token": "[REDACTED]"}],
    ]
    assert sanitize("settings", make_settings()) == "<Settings>"


def test_application_logs_never_reveal_the_database_password(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    url = "postgresql+asyncpg://user:VerySecretPw42@127.0.0.1:9/madasource"
    app = create_app(make_settings(database_url=url))

    with TestClient(app, raise_server_exceptions=False) as test_client:
        test_client.get("/api/v1/health/ready")

    formatter = JsonFormatter()
    assert all("VerySecretPw42" not in formatter.format(r) for r in caplog.records)


def test_database_unavailability_is_logged_as_error(
    app: FastAPI, caplog: pytest.LogCaptureFixture
) -> None:
    class _Lost(Exception):
        sqlstate = "08006"

    async def lost() -> None:
        raise DBAPIError("SELECT 1", None, _Lost("connection lost to db.internal"))

    app.add_api_route("/api/v1/_test/lost", lost, methods=["GET"])
    caplog.set_level(logging.INFO, logger="app.errors")
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/api/v1/_test/lost")

    assert response.status_code == 503
    [line] = _formatted(caplog, "app.errors")
    entry = json.loads(line)
    assert entry["level"] == "ERROR"
    assert entry["path"] == "/api/v1/_test/lost"
    assert "db.internal" not in line
