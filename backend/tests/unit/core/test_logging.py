"""Journaux JSON nettoyés (D-12)."""

import json
import logging
import sys
from datetime import UTC, datetime

import pytest

from app.core.logging import REDACTED, JsonFormatter, request_id_var, sanitize

pytestmark = pytest.mark.unit


def _record(**extra: object) -> logging.LogRecord:
    record = logging.makeLogRecord({"name": "app.test", "levelname": "INFO", "msg": "event"})
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_log_line_is_json_with_required_fields() -> None:
    line = json.loads(JsonFormatter().format(_record(status=200)))

    assert line["level"] == "INFO"
    assert line["logger"] == "app.test"
    assert line["message"] == "event"
    assert line["timestamp"].endswith("Z")
    assert line["status"] == 200


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "new_password",
        "password_hash",
        "access_token",
        "refresh_token",
        "Authorization",
        "cookie",
        "iban",
        # Jour 8
        "auth_signing_key",
        "private_key",
        "credentials",
        "pepper",
        "otp_code",
    ],
)
def test_sensitive_extra_fields_are_redacted(key: str) -> None:
    line = json.loads(JsonFormatter().format(_record(**{key: "s3cr3t-value"})))

    assert line[key] == REDACTED
    assert "s3cr3t-value" not in json.dumps(line)


def test_nested_sensitive_fields_are_redacted() -> None:
    assert sanitize("payload", {"user": "u-1", "password": "x", "inner": {"token": "y"}}) == {
        "user": "u-1",
        "password": REDACTED,
        "inner": {"token": REDACTED},
    }


def test_request_id_from_context_is_added() -> None:
    token = request_id_var.set("0199f2a4-0000-7000-8000-000000000001")
    try:
        line = json.loads(JsonFormatter().format(_record()))
    finally:
        request_id_var.reset(token)

    assert line["request_id"] == "0199f2a4-0000-7000-8000-000000000001"


def test_exception_is_summarized_without_its_message() -> None:
    # Valeur construite à l'exécution : la pile reprend les lignes de code, pas les valeurs.
    row = "-".join(["secret", "row", "value"])
    try:
        raise RuntimeError(f"DETAIL: Failing row contains ({row})")
    except RuntimeError:
        record = logging.makeLogRecord({"msg": "failed", "levelname": "ERROR"})
        record.exc_info = sys.exc_info()

    text = JsonFormatter().format(record)
    line = json.loads(text)

    assert line["exception_types"] == ["builtins.RuntimeError"]
    assert line["stack"]
    assert "exception" not in line
    assert "secret-row-value" not in text


def test_sanitize_keeps_identifiers_readable_and_hides_amounts() -> None:
    from decimal import Decimal
    from enum import StrEnum
    from uuid import UUID

    class Status(StrEnum):
        ACTIVE = "ACTIVE"

    identifier = UUID("0199f2a4-1c44-7a51-8f0e-9a7d2b3c1e55")
    instant = datetime(2026, 10, 14, 8, 0, tzinfo=UTC)

    assert sanitize("organization_id", identifier) == str(identifier)
    assert sanitize("at", instant) == "2026-10-14T08:00:00+00:00"
    assert sanitize("status", Status.ACTIVE) == "ACTIVE"
    assert sanitize("margin", Decimal("1250.00")) == "<Decimal>"


def test_sanitize_masks_key_value_pairs() -> None:
    assert sanitize("headers", [("authorization", "Bearer abc"), ("accept", "json")]) == [
        REDACTED,
        "json",
    ]


def test_uvicorn_color_message_is_dropped() -> None:
    line = json.loads(JsonFormatter().format(_record(color_message="\x1b[36m1\x1b[0m")))

    assert "color_message" not in line
