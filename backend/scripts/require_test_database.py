"""Garde-fou de `make migrations-check` : Alembic ne vise qu'une base dont le nom finit par _test.

Même règle que les tests (testing-strategy.md §4). Lancé par le Makefile avant toute commande
Alembic (`python -m scripts.require_test_database`) ; un refus arrête la cible avec un message
fixe, sans citer l'URL.
"""

import os
import sys

from app.core.config import has_explicit_test_target, parse_database_url

VARIABLE = "TEST_MIGRATION_DATABASE_URL"
REFUSAL = (
    f"{VARIABLE} doit être une URL valide vers une base dont le nom finit par _test, "
    "avec un hôte et un port explicites"
)


def is_test_database_url(raw: str | None) -> bool:
    """Vrai seulement pour une URL valide, d'hôte et de port explicites, vers une base *_test."""
    if not raw:
        return False
    try:
        url = parse_database_url(raw)
    except ValueError:
        return False
    return has_explicit_test_target(url)


def main() -> None:
    if not is_test_database_url(os.environ.get(VARIABLE)):
        sys.exit(REFUSAL)


if __name__ == "__main__":
    main()
