"""Session de requête dans la base de test : validation, annulation, fermeture, isolation.

Chaque test travaille dans la transaction externe de la fixture `db_connection`, annulée à
la fin : rien ne subsiste d'un test à l'autre. Faute de table métier au Jour 6, les essais
utilisent une table temporaire, que le rôle applicatif a le droit de créer.
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


async def test_nothing_leaks_from_a_previous_test(db_connection: AsyncConnection) -> None:
    # La table temporaire et ses lignes des tests précédents ont été annulées avec eux.
    exists = await db_connection.scalar(text("SELECT to_regclass('pg_temp.probe_writes')"))

    assert exists is None
