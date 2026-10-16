"""Aides partagées par les tests : configuration explicite, sans dépendre de l'environnement."""

import os
import sys
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config

from app.core.config import Settings, has_explicit_test_target, parse_database_url

# Aucun service n'écoute sur ce port : toute connexion est refusée immédiatement.
UNREACHABLE_DATABASE_URL = "postgresql+asyncpg://unused:unused@127.0.0.1:9/unreachable"
ALLOWED_ORIGIN = "http://localhost:3000"
# URL injoignable au mot de passe assez fort pour un environnement déployé (valeur factice).
DEPLOYED_DATABASE_URL = "postgresql+asyncpg://madasource:StrongValue42xyz@127.0.0.1:9/madasource"
# Clé de signature factice des tests : 48 caractères, sans le préfixe refusé en déploiement
# (changeme) ; volontairement sans aléa, pour ne ressembler à aucun vrai secret.
TEST_SIGNING_KEY = "test-" + "x" * 43


def make_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "app_env": "local",
        "database_url": UNREACHABLE_DATABASE_URL,
        "database_pool_size": 2,
        "database_max_overflow": 0,
        "database_connect_timeout_seconds": 2.0,
        "database_statement_timeout_ms": 5_000,
        "readiness_timeout_seconds": 2.0,
        "cors_allowed_origins": (ALLOWED_ORIGIN,),
        "log_level": "INFO",
        "demo_mode": False,
        "auth_signing_key": TEST_SIGNING_KEY,
    }
    values.update(overrides)
    return Settings(**values)


ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def database_urls_for_tests() -> tuple[str, str]:
    """URL de la base de test : (rôle applicatif, propriétaire du schéma).

    Leur absence fait échouer le test, sans l'ignorer. Garde-fou : les deux URL visent le
    même serveur (hôte, port) et la même base, dont le nom se termine par _test
    (testing-strategy.md §4).
    """
    app_url = os.environ.get("TEST_DATABASE_URL")
    migration_url = os.environ.get("TEST_MIGRATION_DATABASE_URL")
    if not app_url or not migration_url:
        pytest.fail(
            "TEST_DATABASE_URL et TEST_MIGRATION_DATABASE_URL sont requises. Démarrer la base "
            "de test (docker compose --profile test up -d db-test) puis lancer "
            "`uv run --env-file ../.env pytest` (backend/README.md)."
        )
    app_target, migration_target = parse_database_url(app_url), parse_database_url(migration_url)
    targets = {(u.host, u.port, u.database) for u in (app_target, migration_target)}
    if len(targets) != 1 or not has_explicit_test_target(app_target):
        pytest.fail(
            "Les URL de test doivent viser la même base, dont le nom finit par _test, "
            "avec un hôte et un port explicites."
        )
    return app_url, migration_url


def run_alembic(name: str, *args: str, **options: Any) -> None:
    """Exécute une commande Alembic **sur la base de test seulement**.

    L'URL vient toujours de TEST_MIGRATION_DATABASE_URL (garde-fou _test) et est passée à
    env.py par les attributs de la configuration : la variable MIGRATION_DATABASE_URL du
    poste, qui peut viser la base de développement, n'est jamais utilisée ici. Alembic ne
    reconfigure pas la journalisation des tests.
    """
    _, migration_url = database_urls_for_tests()
    # stdout passé explicitement : la valeur par défaut d'Alembic est figée à l'import, et
    # la sortie échapperait à la capture de pytest.
    config = Config(str(ALEMBIC_INI), stdout=sys.stdout)
    config.attributes["migration_database_url"] = migration_url
    config.attributes["configure_logger"] = False
    getattr(command, name)(config, *args, **options)
