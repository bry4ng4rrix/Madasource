# Commandes reproductibles du backend (Jour 7). Utilisées telles quelles en local et en CI.
# Référence : backend/README.md, section « Commandes officielles ».
#
# En local, les variables viennent d'un fichier : make test ENV_FILE=../.env
# En CI, elles sont fournies par le job : ENV_FILE reste vide.

ENV_FILE ?=
IMAGE ?= madasource-backend:check
UV_RUN := uv run --locked $(if $(ENV_FILE),--env-file $(ENV_FILE),)

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

migrations-check: ## Montée vers la tête et absence d'écart (exige MIGRATION_DATABASE_URL)
	$(UV_RUN) alembic upgrade head
	$(UV_RUN) alembic check

docker-build: ## Image du backend, exécutée sans privilège (aucun envoi vers un registre)
	docker build --tag $(IMAGE) .
	test "$$(docker image inspect --format '{{.Config.User}}' $(IMAGE))" = "10001:10001"

check: quality test-fast ## Contrôles rapides, sans base ni Docker
