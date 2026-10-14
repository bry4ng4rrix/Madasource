"""Session de requête dans la base de test : validation, annulation, fermeture, isolation.

Chaque test travaille dans la transaction externe de la fixture `db_connection`, annulée à
la fin : rien ne subsiste d'un test à l'autre, et l'identifiant de cette transaction ne
change jamais pendant le test. Faute de table métier au Jour 6, les essais utilisent une
table temporaire, que le rôle applicatif a le droit de créer (Q-103). La fixture `api`
partage une seule connexion : des requêtes simultanées dans un même test ne sont pas
prises en charge (les tests de concurrence auront leur propre base, testing-strategy §4).
"""

import httpx2
import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from app.db.session import DbSession

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

CREATE_PROBE = "CREATE TEMPORARY TABLE probe_writes (value text NOT NULL)"


@pytest.fixture
async def probe_api(
    api: tuple[FastAPI, httpx2.AsyncClient], db_connection: AsyncConnection
) -> tuple[httpx2.AsyncClient, list[AsyncSession]]:
    app, client = api
    await db_connection.execute(text(CREATE_PROBE))
    sessions: list[AsyncSession] = []

    async def write_and_commit(session: DbSession) -> dict[str, str]:
        sessions.append(session)
        await session.execute(text("INSERT INTO probe_writes VALUES ('committed')"))
        await session.commit()
        return {"status": "ok"}

    async def write_then_fail(session: DbSession) -> None:
        sessions.append(session)
        await session.execute(text("INSERT INTO probe_writes VALUES ('must-not-stay')"))
        raise RuntimeError("failure after a write")

    app.add_api_route("/api/v1/_test/write", write_and_commit, methods=["POST"])
    app.add_api_route("/api/v1/_test/write-then-fail", write_then_fail, methods=["POST"])
    return client, sessions


async def _values(connection: AsyncConnection) -> list[str]:
    result = await connection.execute(text("SELECT value FROM probe_writes ORDER BY value"))
    return list(result.scalars())


async def test_committed_write_is_visible_inside_the_test_transaction(
    probe_api: tuple[httpx2.AsyncClient, list[AsyncSession]], db_connection: AsyncConnection
) -> None:
    client, sessions = probe_api

    response = await client.post("/api/v1/_test/write")

    assert response.status_code == 200
    assert await _values(db_connection) == ["committed"]
    [session] = sessions
    assert not session.in_transaction()


async def test_error_rolls_back_the_request_writes(
    probe_api: tuple[httpx2.AsyncClient, list[AsyncSession]], db_connection: AsyncConnection
) -> None:
    client, sessions = probe_api

    response = await client.post("/api/v1/_test/write-then-fail")

    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
    assert await _values(db_connection) == []
    [session] = sessions
    assert not session.in_transaction()


async def test_each_request_gets_its_own_session(
    probe_api: tuple[httpx2.AsyncClient, list[AsyncSession]], db_connection: AsyncConnection
) -> None:
    client, sessions = probe_api

    await client.post("/api/v1/_test/write")
    await client.post("/api/v1/_test/write-then-fail")
    await client.post("/api/v1/_test/write")

    assert len({id(session) for session in sessions}) == 3
    assert await _values(db_connection) == ["committed", "committed"]


async def test_request_commits_never_leave_the_outer_transaction(
    probe_api: tuple[httpx2.AsyncClient, list[AsyncSession]], db_connection: AsyncConnection
) -> None:
    """Un commit de la session de requête libère seulement un point de sauvegarde."""
    client, _ = probe_api
    before = await db_connection.scalar(text("SELECT pg_current_xact_id()::text"))

    await client.post("/api/v1/_test/write")
    await client.post("/api/v1/_test/write-then-fail")

    after = await db_connection.scalar(text("SELECT pg_current_xact_id()::text"))
    assert after == before
    assert db_connection.in_transaction()


async def test_db_session_commit_stays_in_the_outer_transaction(
    db_session: AsyncSession, db_connection: AsyncConnection
) -> None:
    before = await db_connection.scalar(text("SELECT pg_current_xact_id()::text"))
    await db_session.execute(text(CREATE_PROBE))
    await db_session.execute(text("INSERT INTO probe_writes VALUES ('from-session')"))
    await db_session.commit()

    assert await _values(db_connection) == ["from-session"]
    assert await db_connection.scalar(text("SELECT pg_current_xact_id()::text")) == before


async def test_session_timeouts_are_set(db_connection: AsyncConnection) -> None:
    # Valeurs proposées (Q-103) : verrou 5 s, transaction inactive 60 s, requête 5 s en test.
    assert await db_connection.scalar(text("SHOW lock_timeout")) == "5s"
    assert await db_connection.scalar(text("SHOW idle_in_transaction_session_timeout")) == "1min"
    assert await db_connection.scalar(text("SHOW statement_timeout")) == "5s"
