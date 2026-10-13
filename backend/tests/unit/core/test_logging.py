"""Journaux JSON nettoyés (D-12)."""

import json
import logging
import sys

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
    "key", ["password", "new_password", "access_token", "Authorization", "cookie", "iban"]
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


def test_exception_is_formatted() -> None:
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = logging.makeLogRecord({"msg": "failed", "levelname": "ERROR"})
        record.exc_info = sys.exc_info()

    line = json.loads(JsonFormatter().format(record))

    assert "RuntimeError: boom" in line["exception"]


def test_uvicorn_color_message_is_dropped() -> None:
    line = json.loads(JsonFormatter().format(_record(color_message="\x1b[36m1\x1b[0m")))

    assert "color_message" not in line
