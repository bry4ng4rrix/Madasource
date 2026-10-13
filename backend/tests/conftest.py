"""Fixtures communes (testing-strategy.md §5).

La configuration de test est construite explicitement, champ par champ : elle ne dépend
pas des variables d'environnement du poste. Les tests sans base pointent vers une adresse
injoignable ; les tests d'intégration exigent la base de test éphémère (`db-test`).
"""

import os
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.support import make_settings


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
def test_database_url() -> str:
    """URL de la base de test éphémère. Son absence fait échouer le test, sans l'ignorer."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.fail(
            "TEST_DATABASE_URL absente. Démarrer la base de test "
            "(docker compose --profile test up -d db-test) puis lancer "
            "`uv run --env-file ../.env pytest` (backend/README.md)."
        )
    return url


@pytest.fixture
def db_settings(test_database_url: str) -> Settings:
    # app_env=test : la configuration refuse toute base dont le nom ne finit pas par _test.
    return make_settings(app_env="test", database_url=test_database_url)


@pytest.fixture
def db_client(db_settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(db_settings), raise_server_exceptions=False) as test_client:
        yield test_client
