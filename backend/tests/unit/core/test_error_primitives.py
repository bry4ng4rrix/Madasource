"""Construction des erreurs, sans base ni HTTP."""

import uuid

import pytest
from sqlalchemy.exc import DBAPIError
from starlette.datastructures import Headers

from app.core import exceptions
from app.core.errors import sanitize_validation_errors, sqlstate_of
from app.core.middleware import incoming_request_id

pytestmark = pytest.mark.unit


class _DriverError(Exception):
    def __init__(self, sqlstate: str | None) -> None:
        super().__init__("driver error")
        self.sqlstate = sqlstate


def test_validation_errors_never_keep_the_input() -> None:
    raw = [
        {
            "type": "string_too_short",
            "loc": ("body", "password"),
            "msg": "String should have at least 12 characters",
            "input": "short-secret",
            "ctx": {"min_length": 12},
            "url": "https://errors.pydantic.dev/",
        }
    ]

    [error] = sanitize_validation_errors(raw)

    assert error.model_dump() == {
        "field": "body.password",
        "code": "string_too_short",
        "message": "String should have at least 12 characters",
    }


@pytest.mark.parametrize("sqlstate", ["40P01", "57014", None])
def test_sqlstate_is_read_from_driver_error(sqlstate: str | None) -> None:
    error = DBAPIError("SELECT 1", None, _DriverError(sqlstate))

    assert sqlstate_of(error) == sqlstate


@pytest.mark.parametrize(
    ("error_class", "status", "code"),
    [
        (exceptions.ValidationAppError, 422, "BUSINESS_RULE_VIOLATION"),
        (exceptions.BadRequestError, 400, "BAD_REQUEST"),
        (exceptions.AuthenticationError, 401, "AUTHENTICATION_REQUIRED"),
        (exceptions.PermissionDeniedError, 403, "PERMISSION_DENIED"),
        (exceptions.NotFoundError, 404, "RESOURCE_NOT_FOUND"),
        (exceptions.ConflictError, 409, "CONFLICT"),
        (exceptions.InvalidStateTransitionError, 409, "INVALID_STATE_TRANSITION"),
        (exceptions.ConcurrentModificationError, 409, "CONCURRENT_MODIFICATION"),
        (exceptions.RateLimitedError, 429, "RATE_LIMITED"),
        (exceptions.ServiceUnavailableError, 503, "SERVICE_UNAVAILABLE"),
    ],
)
def test_exception_catalogue(
    error_class: type[exceptions.AppError], status: int, code: str
) -> None:
    assert (error_class.status_code, error_class.code) == (status, code)


def test_retry_after_header() -> None:
    error = exceptions.ServiceUnavailableError("down", retry_after=5)

    assert error.headers == {"Retry-After": "5"}


def test_authentication_error_carries_www_authenticate() -> None:
    assert exceptions.AuthenticationError().headers == {"WWW-Authenticate": "Bearer"}


def test_default_headers_are_not_shared_between_instances() -> None:
    first = exceptions.AuthenticationError()
    first.headers["X-Extra"] = "1"

    assert exceptions.AuthenticationError().headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0199f2a4-1c44-7a51-8f0e-9a7d2b3c1e55", "0199f2a4-1c44-7a51-8f0e-9a7d2b3c1e55"),
        ("0199F2A4-1C44-7A51-8F0E-9A7D2B3C1E55", "0199f2a4-1c44-7a51-8f0e-9a7d2b3c1e55"),
        ("not-a-uuid", None),
        ("0199f2a4-1c44-7a51-8f0e-9a7d2b3c1e55\nforged-log-line", None),
        ("x" * 500, None),
    ],
)
def test_incoming_request_id_must_be_a_uuid(value: str, expected: str | None) -> None:
    assert incoming_request_id(Headers({"X-Request-ID": value})) == expected


def test_incoming_request_id_absent() -> None:
    assert incoming_request_id(Headers({})) is None
    assert uuid.UUID(str(uuid.uuid7())).version == 7
