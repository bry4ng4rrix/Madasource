"""Migrations Alembic sur la base de test éphémère (testing-strategy.md §2, « Migrations »).

Montée vers la tête, absence d'écart entre modèles et migrations, réversibilité de la
dernière révision, contrôle des droits sur le schéma. Le retour arrière n'est exécuté que
sur cette base jetable (`run_alembic` ne vise qu'elle), d'une seule révision, puis la tête
est rétablie : jamais `downgrade base`. Ces tests modifient l'état de la base partagée par
la session : ils ne sont pas compatibles avec une exécution parallèle (pytest-xdist).
"""

import importlib.util
from types import ModuleType

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.support import ALEMBIC_INI, database_urls_for_tests, run_alembic

pytestmark = pytest.mark.integration

VERSIONS = ALEMBIC_INI.parent / "alembic" / "versions"


def _script() -> ScriptDirectory:
    return ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))


def _head() -> str:
    head = _script().get_current_head()
    assert head is not None
    return head


def _revision_module(revision: str) -> ModuleType:
    [path] = VERSIONS.glob(f"*_{revision}_*.py")
    spec = importlib.util.spec_from_file_location(f"revision_{revision}", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_history_is_linear_with_a_single_head() -> None:
    script = _script()

    assert len(script.get_heads()) == 1
    assert [r.revision for r in script.walk_revisions()] == ["179c8cc724de", "03d1bd152b99"]


def test_database_is_at_head_and_matches_the_models(
    migrated_test_database: str, capsys: pytest.CaptureFixture[str]
) -> None:
    run_alembic("current")
    assert _head() in capsys.readouterr().out

    # Aucune opération en attente entre les modèles et la base (lève une exception sinon).
    run_alembic("check")


def test_last_revision_is_reversible(
    migrated_test_database: str, capsys: pytest.CaptureFixture[str]
) -> None:
    head = _head()
    try:
        run_alembic("downgrade", "-1")
        run_alembic("current")
        current = capsys.readouterr().out
        assert head not in current
        assert "03d1bd152b99" in current
    finally:
        run_alembic("upgrade", "head")
    run_alembic("current")
    assert head in capsys.readouterr().out


def test_offline_sql_can_be_reviewed(
    migrated_test_database: str, capsys: pytest.CaptureFixture[str]
) -> None:
    run_alembic("upgrade", "head", sql=True)
    upgrade_sql = capsys.readouterr().out
    run_alembic("downgrade", "03d1bd152b99:base", sql=True)
    downgrade_sql = capsys.readouterr().out

    assert "REVOKE ALL ON SCHEMA public FROM PUBLIC" in upgrade_sql
    assert "GRANT USAGE ON SCHEMA public TO madasource_app" in upgrade_sql
    assert "has_schema_privilege" in upgrade_sql
    # Le retour arrière de la première révision rétablit le défaut de PostgreSQL.
    assert "GRANT USAGE ON SCHEMA public TO PUBLIC" in downgrade_sql
    assert "changeme" not in upgrade_sql + downgrade_sql


@pytest.mark.anyio
async def test_privilege_verification_fails_when_public_keeps_access(
    migrated_test_database: str,
) -> None:
    """La révision de contrôle échoue si les droits n'ont pas pris effet (constat I1)."""
    verify_sql = _revision_module("179c8cc724de").VERIFY_SCHEMA_PRIVILEGES_SQL
    _, migration_url = database_urls_for_tests()
    engine = create_async_engine(migration_url)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                await connection.execute(text(verify_sql))  # état réel : contrôle réussi
                await connection.execute(text("GRANT USAGE ON SCHEMA public TO PUBLIC"))
                with pytest.raises(DBAPIError, match="PUBLIC garde des droits"):
                    await connection.execute(text(verify_sql))
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()
