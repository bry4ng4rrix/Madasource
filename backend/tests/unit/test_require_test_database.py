"""Garde-fou de `make migrations-check` : Alembic ne vise qu'une base dont le nom finit par _test.

Régression : écrit en Python sur une seule ligne dans le Makefile, le garde-fou était invalide
(`try:` après `;`) et refusait toute URL, y compris en CI. Les tests passent donc par le point
d'entrée réellement appelé par le Makefile (`python -m scripts.require_test_database`).
"""

import runpy
import sys
from collections.abc import Callable

import pytest

from scripts.require_test_database import REFUSAL, VARIABLE, is_test_database_url

pytestmark = pytest.mark.unit

TEST_URL = "postgresql+asyncpg://test-owner:test-secret@localhost:5434/madasource_test"
REFUSED = {
    "base-de-dev": "postgresql+asyncpg://test-owner:test-secret@localhost:5433/madasource",
    "suffixe-non-final": "postgresql+asyncpg://test-owner:test-secret@db:5434/madasource_test_x",
    "sans-hote": "postgresql+asyncpg://test-owner:test-secret@/madasource_test",
    "sans-port": "postgresql+asyncpg://test-owner:test-secret@localhost/madasource_test",
    "sans-base": "postgresql+asyncpg://test-owner:test-secret@localhost:5434",
    "base-remplacee-par-la-requete": f"{TEST_URL}?database=madasource",
    "serveur-remplace-par-dsn": f"{TEST_URL}?dsn=postgresql://localhost:5433/",
    "url-invalide": "pas-une-url",
    "arobase-dans-le-mot-de-passe": "postgresql+asyncpg://test-owner:test-secret@x@localhost/x_test",
    "vide": "",
}


MODULE = "scripts.require_test_database"


@pytest.fixture
def run_as_module(monkeypatch: pytest.MonkeyPatch) -> Callable[[], None]:
    """Comme `python -m` : module absent de sys.modules (rétabli après le test), puis exécuté."""
    monkeypatch.delitem(sys.modules, MODULE, raising=False)

    def run() -> None:
        runpy.run_module(MODULE, run_name="__main__")

    return run


def test_base_de_test_acceptee(
    monkeypatch: pytest.MonkeyPatch, run_as_module: Callable[[], None]
) -> None:
    assert is_test_database_url(TEST_URL)
    monkeypatch.setenv(VARIABLE, TEST_URL)
    run_as_module()


@pytest.mark.parametrize("url", list(REFUSED.values()), ids=list(REFUSED))
def test_autre_base_refusee(
    monkeypatch: pytest.MonkeyPatch, run_as_module: Callable[[], None], url: str
) -> None:
    assert not is_test_database_url(url)
    monkeypatch.setenv(VARIABLE, url)
    with pytest.raises(SystemExit) as refusal:
        run_as_module()
    # Message affiché par l'interpréteur : fixe, sans aucune partie de l'URL.
    assert refusal.value.code == REFUSAL
    assert "test-secret" not in str(refusal.value.code)


def test_variable_absente_refusee(
    monkeypatch: pytest.MonkeyPatch, run_as_module: Callable[[], None]
) -> None:
    monkeypatch.delenv(VARIABLE, raising=False)
    assert not is_test_database_url(None)
    with pytest.raises(SystemExit) as refusal:
        run_as_module()
    assert refusal.value.code == REFUSAL
