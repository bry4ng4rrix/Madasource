"""Base de test éphémère : sonde de disponibilité et session par requête.

Exige `docker compose --profile test up -d db-test` et `TEST_DATABASE_URL`.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import DbSession
from app.main import create_app

pytestmark = pytest.mark.integration


def test_ready_returns_ok_when_database_answers(db_client: TestClient) -> None:
    response = db_client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@dataclass
class SessionHarness:
    app: FastAPI
    client: TestClient
    sessions: list[AsyncSession] = field(default_factory=list)


@pytest.fixture
def harness(db_settings: Settings) -> Iterator[SessionHarness]:
    """Application réelle, plus deux routes de test qui utilisent la session de requête."""
    app = create_app(db_settings)
    sessions: list[AsyncSession] = []

    async def query(session: DbSession) -> dict[str, int]:
        sessions.append(session)
        value = (await session.execute(text("SELECT 41 + 1"))).scalar_one()
        return {"value": value}

    async def query_then_fail(session: DbSession) -> None:
        sessions.append(session)
        await session.execute(text("SELECT 1"))
        raise RuntimeError("failure after a query")

    app.add_api_route("/api/v1/_test/query", query, methods=["GET"])
    app.add_api_route("/api/v1/_test/query-then-fail", query_then_fail, methods=["GET"])
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield SessionHarness(app=app, client=test_client, sessions=sessions)


def test_session_dependency_runs_queries(harness: SessionHarness) -> None:
    response = harness.client.get("/api/v1/_test/query")

    assert response.status_code == 200
    assert response.json() == {"value": 42}


def test_session_is_rolled_back_and_released_after_an_error(harness: SessionHarness) -> None:
    response = harness.client.get("/api/v1/_test/query-then-fail")

    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
    [session] = harness.sessions
    assert not session.in_transaction()
    assert harness.app.state.engine.pool.checkedout() == 0


def test_engine_is_disposed_on_shutdown(db_settings: Settings) -> None:
    app = create_app(db_settings)
    with TestClient(app) as test_client:
        assert test_client.get("/api/v1/health/ready").status_code == 200
        engine = app.state.engine
        assert engine.pool.checkedin() >= 1

    assert engine.pool.checkedin() == 0
