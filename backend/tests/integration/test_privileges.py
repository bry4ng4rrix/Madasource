"""Droits réels du rôle applicatif sur la base de test (security-design.md §19).

L'application se connecte avec `madasource_app` : elle lit et écrit des données, mais ne
peut ni modifier le schéma, ni lire la table de version d'Alembic, ni administrer la base.
"""

import secrets

import httpx2
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.roles import APP_ROLE
from app.db.session import DbSession
from app.main import create_app
from tests.support import make_settings

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

INSUFFICIENT_PRIVILEGE = "42501"


async def _sqlstate_of(connection: AsyncConnection, statement: str) -> str | None:
    """Exécute l'instruction dans un point de sauvegarde et renvoie le SQLSTATE d'échec."""
    try:
        async with connection.begin_nested():
            await connection.execute(text(statement))
    except DBAPIError as exc:
        return getattr(exc.orig, "sqlstate", None)
    return None


async def test_application_connects_as_the_app_role(db_connection: AsyncConnection) -> None:
    role = await db_connection.scalar(
        text(
            "SELECT rolname || ':' || rolsuper || rolcreatedb || rolcreaterole || rolbypassrls "
            "FROM pg_roles WHERE rolname = current_user"
        )
    )

    assert role == f"{APP_ROLE}:falsefalsefalsefalse"


@pytest.mark.parametrize(
    "statement",
    [
        "CREATE TABLE public.not_allowed (id integer)",
        "CREATE SCHEMA not_allowed",
        "SELECT version_num FROM alembic_version",
        "DROP TABLE alembic_version",
    ],
)
async def test_application_cannot_change_the_schema(
    db_connection: AsyncConnection, statement: str
) -> None:
    assert await _sqlstate_of(db_connection, statement) == INSUFFICIENT_PRIVILEGE


async def test_schema_privileges_come_from_the_baseline_migration(
    db_connection: AsyncConnection,
) -> None:
    privilege = text("SELECT has_schema_privilege(:role, 'public', :privilege)")
    usage = await db_connection.scalar(privilege, {"role": APP_ROLE, "privilege": "USAGE"})
    create = await db_connection.scalar(privilege, {"role": APP_ROLE, "privilege": "CREATE"})
    public_usage = await db_connection.scalar(
        text("SELECT has_schema_privilege('public', 'public', 'USAGE')")
    )

    assert usage is True
    assert create is False
    assert public_usage is False


async def test_wrong_password_is_a_503(test_database_url: str) -> None:
    wrong_password = secrets.token_hex(12)
    wrong = make_url(test_database_url).set(password=wrong_password)
    app = create_app(
        make_settings(app_env="test", database_url=wrong.render_as_string(hide_password=False))
    )

    async def query(session: DbSession) -> dict[str, int]:
        return {"value": (await session.execute(text("SELECT 1"))).scalar_one()}

    app.add_api_route("/api/v1/_test/query", query, methods=["GET"])
    async with app.router.lifespan_context(app):
        transport = httpx2.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx2.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/api/v1/_test/query")

    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"
    assert response.headers["retry-after"] == "5"
    assert wrong_password not in response.text
