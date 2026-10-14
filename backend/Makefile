# Commandes reproductibles du backend (Jour 7). Utilisées telles quelles en local et en CI.
# Référence : backend/README.md, section « Commandes officielles ».
#
# En local, les variables viennent d'un fichier : make test ENV_FILE=../.env
# En CI, elles sont fournies par le job : ENV_FILE reste vide.

ENV_FILE ?=
IMAGE ?= madasource-backend:check
UV_RUN := uv run --locked $(if $(ENV_FILE),--env-file $(ENV_FILE),)

# Alembic sur la base de test seulement : propriétaire du schéma de TEST_MIGRATION_DATABASE_URL.
ALEMBIC_TEST := $(UV_RUN) sh -c 'MIGRATION_DATABASE_URL="$$TEST_MIGRATION_DATABASE_URL" exec alembic "$$@"' alembic
# Même garde-fou que les tests (testing-strategy.md §4) : une base dont le nom finit par _test.
TEST_DB_GUARD := import os, sys; from app.core.config import parse_database_url; \
	raw = os.environ.get("TEST_MIGRATION_DATABASE_URL", ""); \
	try: name = parse_database_url(raw).database or "" if raw else ""; \
	except ValueError: name = ""; \
	sys.exit(None if name.endswith("_test") else "TEST_MIGRATION_DATABASE_URL doit être une URL valide vers une base dont le nom finit par _test")

.PHONY: help install lock-check lint format-check types imports quality test-fast test \
	migrations-check docker-build check

help: ## Liste des cibles
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "%-18s %s\n", $$1, $$2}'

install: ## Environnement à partir de uv.lock (refuse un verrou périmé)
	uv sync --locked

lock-check: ## uv.lock correspond à pyproject.toml
	uv lock --check

lint: ## Ruff : règles de lint
	$(UV_RUN) ruff check .

format-check: ## Ruff : formatage (vérification seulement)
	$(UV_RUN) ruff format --check .

types: ## mypy en mode strict
	$(UV_RUN) mypy

imports: ## Frontières de l'architecture (import-linter)
	$(UV_RUN) lint-imports

quality: lock-check lint format-check types imports ## Tous les contrôles statiques

test-fast: ## Tests sans base (unitaires, API, architecture) ; sélection, pas la suite complète
	$(UV_RUN) pytest -m "not integration"

test: ## Suite complète avec couverture (exige la base de test et TEST_* )
	$(UV_RUN) pytest --cov

migrations-check: ## Base de test : montée vers la tête, puis absence d'écart (TEST_MIGRATION_DATABASE_URL)
	$(UV_RUN) python -c '$(TEST_DB_GUARD)'
	$(ALEMBIC_TEST) upgrade head
	$(ALEMBIC_TEST) check

docker-build: ## Image du backend, exécutée sans privilège (aucun envoi vers un registre)
	@iid="$$(mktemp)" && trap 'rm -f "$$iid"' EXIT && \
	docker build --iidfile "$$iid" --tag $(IMAGE) . && \
	user="$$(docker image inspect --format '{{.Config.User}}' "$$(cat "$$iid")")" && \
	echo "Utilisateur de l'image construite : $$user" && test "$$user" = "10001:10001"

check: quality test-fast ## Contrôles rapides, sans base ni Docker
