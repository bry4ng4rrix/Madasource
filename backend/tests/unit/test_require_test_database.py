"""Garde-fou de `make migrations-check` : Alembic ne vise qu'une base dont le nom finit par _test.

Régression : écrit en Python sur une seule ligne dans le Makefile, le garde-fou était invalide
(`try:` après `;`) et refusait toute URL, y compris en CI.
"""

import pytest

from scripts import require_test_database
from scripts.require_test_database import REFUSAL, VARIABLE, is_test_database_url, main

pytestmark = pytest.mark.unit

TEST_URL = "postgresql+asyncpg://test-owner:test-secret@localhost:5434/madasource_test"
REFUSED = {
    "base-de-dev": "postgresql+asyncpg://test-owner:test-secret@localhost:5433/madasource",
    "suffixe-non-final": "postgresql+asyncpg://test-owner:test-secret@localhost/madasource_test_copie",
    "sans-base": "postgresql+asyncpg://test-owner:test-secret@localhost:5434",
    "url-invalide": "pas-une-url",
    "arobase-dans-le-mot-de-passe": "postgresql+asyncpg://test-owner:a@b@localhost/madasource_test",
    "vide": "",
}


def test_base_de_test_acceptee(monkeypatch: pytest.MonkeyPatch) -> None:
    assert is_test_database_url(TEST_URL)
    monkeypatch.setenv(VARIABLE, TEST_URL)
    main()


@pytest.mark.parametrize("url", list(REFUSED.values()), ids=list(REFUSED))
def test_autre_base_refusee(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    assert not is_test_database_url(url)
    monkeypatch.setenv(VARIABLE, url)
    with pytest.raises(SystemExit) as refusal:
        main()
    assert refusal.value.code == REFUSAL
    assert "test-secret" not in REFUSAL


def test_variable_absente_refusee(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(VARIABLE, raising=False)
    assert not is_test_database_url(None)
    with pytest.raises(SystemExit) as refusal:
        require_test_database.main()
    assert refusal.value.code == REFUSAL
