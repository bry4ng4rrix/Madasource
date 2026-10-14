"""Migrations Alembic sur la base de test éphémère (testing-strategy.md §2, « Migrations »).

Montée vers la tête, absence d'écart entre modèles et migrations, réversibilité de la
dernière révision. Le retour arrière n'est exécuté que sur cette base jetable, puis la
tête est rétablie : jamais `downgrade base`, jamais sur une autre base.
"""

import os
from collections.abc import Iterator

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from tests.support import ALEMBIC_INI, database_urls_for_tests, run_alembic

pytestmark = pytest.mark.integration


@pytest.fixture
def migration_environment(migrated_test_database: str) -> Iterator[str]:
    """MIGRATION_DATABASE_URL pointe vers la base de test pendant le test."""
    _, migration_url = database_urls_for_tests()
    previous = os.environ.get("MIGRATION_DATABASE_URL")
    os.environ["MIGRATION_DATABASE_URL"] = migration_url
    try:
        yield migration_url
    finally:
        if previous is None:
            os.environ.pop("MIGRATION_DATABASE_URL", None)
        else:
            os.environ["MIGRATION_DATABASE_URL"] = previous


def _script() -> ScriptDirectory:
    return ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))


def _head() -> str:
    head = _script().get_current_head()
    assert head is not None
    return head


def test_history_has_a_single_head() -> None:
    assert len(_script().get_heads()) == 1


def test_database_is_at_head_and_matches_the_models(
    migration_environment: str, capsys: pytest.CaptureFixture[str]
) -> None:
    run_alembic("current")
    assert _head() in capsys.readouterr().out

    # Aucune opération en attente entre les modèles et la base (lève une exception sinon).
    run_alembic("check")


def test_last_revision_is_reversible(
    migration_environment: str, capsys: pytest.CaptureFixture[str]
) -> None:
    head = _head()
    try:
        run_alembic("downgrade", "-1")
        run_alembic("current")
        assert head not in capsys.readouterr().out
    finally:
        run_alembic("upgrade", "head")
    run_alembic("current")
    assert head in capsys.readouterr().out


def test_offline_sql_can_be_reviewed(
    migration_environment: str, capsys: pytest.CaptureFixture[str]
) -> None:
    run_alembic("upgrade", "head", sql=True)
    sql = capsys.readouterr().out

    assert "REVOKE ALL ON SCHEMA public FROM PUBLIC" in sql
    assert "GRANT USAGE ON SCHEMA public TO madasource_app" in sql
    assert "changeme" not in sql
