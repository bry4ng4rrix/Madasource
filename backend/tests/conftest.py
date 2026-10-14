"""Fixtures communes (testing-strategy.md §4 et §5).

La configuration de test est construite explicitement, champ par champ : elle ne dépend
pas des variables d'environnement du poste. Les tests sans base pointent vers une adresse
injoignable ; les tests d'intégration exigent la base de test éphémère (`db-test`).

Base de test :
- le schéma est créé **une fois par session** de tests par `alembic upgrade head`, avec le
  propriétaire du schéma (`TEST_MIGRATION_DATABASE_URL`), ce qui teste aussi les migrations ;
- l'application s'y connecte avec le rôle applicatif (`TEST_DATABASE_URL`) ;
- chaque test d'intégration travaille dans une **transaction externe annulée** à la fin :
  la session de requête y rejoint la transaction par points de sauvegarde
  (`join_transaction_mode="create_savepoint"`), et ses validations n'en sortent jamais.
"""

from collections.abc import AsyncIterator, Iterator

import httpx2
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.session import create_engine
from app.main import create_app
from tests.support import database_urls_for_tests, make_settings, run_alembic


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    # raise_server_exceptions=False : les erreurs 500 sont vérifiées comme réponses HTTP.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def anyio_backend() -> str:
    """Tests asynchrones : plugin d'AnyIO, boucle asyncio seulement (testing-strategy §3)."""
    return "asyncio"


@pytest.fixture(scope="session")
def migrated_test_database() -> str:
    """Applique les migrations à la base de test, une fois par session ; renvoie la cible."""
    run_alembic("upgrade", "head")
    return "head"


@pytest.fixture
def test_database_url(migrated_test_database: str) -> str:
    """URL du rôle applicatif sur la base de test, déjà migrée."""
    app_url, _ = database_urls_for_tests()
    return app_url


@pytest.fixture
def db_settings(test_database_url: str) -> Settings:
    # app_env=test : la configuration refuse toute base dont le nom ne finit pas par _test.
    return make_settings(app_env="test", database_url=test_database_url)


@pytest.fixture
def db_client(db_settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(db_settings), raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
async def db_connection(db_settings: Settings) -> AsyncIterator[AsyncConnection]:
    """Connexion du rôle applicatif dans une transaction externe, annulée à la fin du test."""
    engine = create_engine(db_settings)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                yield connection
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()


@pytest.fixture
async def db_session(db_connection: AsyncConnection) -> AsyncIterator[AsyncSession]:
    """Session qui rejoint la transaction externe par points de sauvegarde."""
    async with AsyncSession(
        bind=db_connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    ) as session:
        yield session


@pytest.fixture
async def api(
    db_settings: Settings, db_connection: AsyncConnection
) -> AsyncIterator[tuple[FastAPI, httpx2.AsyncClient]]:
    """Application réelle et client HTTP en mémoire, isolés dans la transaction du test.

    La vraie dépendance `get_db_session` est conservée ; seule la fabrique de sessions est
    remplacée, pour que chaque session de requête rejoigne la transaction externe. Le
    transport ASGI n'exécute pas le cycle de vie : il est déclenché explicitement.
    """
    app = create_app(db_settings)
    async with app.router.lifespan_context(app):
        app.state.session_factory = async_sessionmaker(
            bind=db_connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        transport = httpx2.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx2.AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield app, client
