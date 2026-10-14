# Backend MadaSource

API REST FastAPI de MadaSource (monolithe modulaire). État au Jour 5 : fondation de l'application (configuration validée, fabrique d'application, routeur `/api/v1`, sondes de santé, erreurs au format Problem Details, journaux JSON, CORS, session de base de données), sans logique métier.

Ce fichier est la **source de vérité des commandes** du backend. Les autres documents, y compris les skills de Claude Code, renvoient ici.

## Prérequis

| Outil | Version | Rôle |
|---|---|---|
| Python | 3.14 (`.python-version`) | Exécution (D-27) |
| uv | 0.13.0 (imposée par `required-version` dans `pyproject.toml`) | Environnement virtuel et dépendances, à partir de `uv.lock` |
| Docker et Docker Compose | Docker 29, Compose 5 (versions du poste de développement) | PostgreSQL 18, base de test, backend en conteneur |

## Installation

Depuis la racine du dépôt, puis depuis `backend/` :

```bash
cp .env.example .env   # puis remplacer les valeurs factices (voir les commentaires du fichier)
cd backend
uv sync --locked       # crée backend/.venv à partir de uv.lock (dépendances et outils de dev)
```

`--locked` refuse d'installer si `uv.lock` ne correspond plus à `pyproject.toml`. Après une modification volontaire des dépendances : `uv lock`, puis relecture du diff de `uv.lock`.

Rien ne charge `.env` automatiquement : l'option `--env-file ../.env` de `uv run` le fait. Elle fonctionne aussi sous fish, contrairement à `source .env`.

## Commandes officielles

Depuis `backend/` :

| Contrôle | Commande |
|---|---|
| Verrou à jour | `uv lock --check` |
| Lint | `uv run ruff check .` |
| Format (vérification) | `uv run ruff format --check .` |
| Types | `uv run mypy` (mode strict ; fichiers déclarés dans `pyproject.toml`) |
| Base de test (avant les tests) | `docker compose --profile test up -d db-test` (depuis la racine) |
| Tests : suite complète | `uv run --env-file ../.env pytest` |
| Tests sans base | `uv run pytest -m "not integration"` (sélection, pas la suite complète) |
| Serveur local | `uv run --env-file ../.env uvicorn --factory app.main:create_app --reload --port 8002 --no-access-log --no-server-header` |
| Migrations : têtes | `uv run alembic heads` |
| Migrations : SQL hors ligne | `uv run --env-file ../.env alembic upgrade head --sql` |
| Migrations : application | `uv run --env-file ../.env alembic upgrade head` (base démarrée) |

Points de fonctionnement :
- **tests** : marqueurs `unit` (sans base ni HTTP), `api` (client HTTP en mémoire, sans base), `integration` (base de test). Tout avertissement est traité comme une erreur (`filterwarnings = error`). Sans `TEST_DATABASE_URL`, les tests d'intégration **échouent** avec la marche à suivre : ils ne sont jamais ignorés ;
- **base de test** : service `db-test` (profil `test`), données en mémoire (`tmpfs`), vides à chaque démarrage, port hôte 5434. La configuration de test refuse toute base dont le nom ne se termine pas par `_test`. Jamais la base de développement ;
- **serveur** : `--factory` appelle `create_app()`, qui lit et valide la configuration ; `--no-access-log` laisse un seul journal d'accès, celui de l'application (D-12) ; `--no-server-header` retire la bannière `server: uvicorn` ;
- **migrations** : Alembic lit `DATABASE_URL` dans l'environnement, jamais dans `alembic.ini`. Chaque révision générée est corrigée puis formatée par Ruff (hooks d'`alembic.ini`). Aucune migration avant le Jour 6. Règles : skill `database-migrations` ; jamais de `downgrade base` ni de réinitialisation d'une base.

## Docker Compose

Depuis la racine du dépôt (vérifié le 2026-10-13) :

```bash
docker compose up -d --build   # PostgreSQL 18 (db) et backend
docker compose ps              # attendu : les deux services « healthy »
curl http://127.0.0.1:8001/api/v1/health/ready
docker compose down            # arrêt ; ne jamais ajouter -v, qui supprime le volume de données
```

| Service | Image | Port hôte (défaut) | Santé |
|---|---|---|---|
| `db` | `postgres:18.6-trixie` | `127.0.0.1:5433` | `pg_isready -h 127.0.0.1` (par TCP) |
| `backend` | construite depuis `backend/Dockerfile` | `127.0.0.1:8001` | `GET /api/v1/health/live` |
| `db-test` (profil `test`) | `postgres:18.6-trixie`, `tmpfs` | `127.0.0.1:5434` | `pg_isready` |

Les données de développement sont dans le volume nommé `madasource_pgdata`. Les ports hôte se changent par `MADASOURCE_DB_HOST_PORT`, `MADASOURCE_API_HOST_PORT` et `MADASOURCE_TEST_DB_HOST_PORT` ; `DATABASE_URL` et `TEST_DATABASE_URL` doivent alors suivre. Le serveur local (port 8002) et le backend de Compose (port 8001) peuvent tourner en même temps.

## API

| Chemin | Rôle |
|---|---|
| `GET /api/v1/health/live` | Le processus répond (aucune dépendance consultée) |
| `GET /api/v1/health/ready` | La base répond (`SELECT 1`, délai `READINESS_TIMEOUT_SECONDS`) ; sinon 503 `SERVICE_UNAVAILABLE` avec `Retry-After: 5` |
| `/api/v1/openapi.json`, `/api/v1/docs` | Schéma et documentation interactive, en `local`, `test` et `staging` seulement |

Toute erreur est une réponse `application/problem+json` (RFC 9457, [`error-handling.md`](../docs/backend/error-handling.md)) : `type` = `about:blank`, `title` = phrase HTTP, `status`, `detail` facultatif, `code` stable (contrat du client), `request_id`, et `errors` (champ, code, message, jamais la valeur saisie) pour une validation.

Toute réponse porte `X-Request-ID` (repris s'il est un UUID valide, sinon généré), `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` et `Cache-Control: no-store` ; une instance de démonstration ajoute `X-MadaSource-Mode: demo`.

## Variables d'environnement

Toutes sont documentées dans `.env.example` (racine), avec des valeurs factices. La configuration est validée au démarrage : une valeur invalide empêche le démarrage, sans jamais recopier la valeur reçue dans le message d'erreur.

| Variable | Usage |
|---|---|
| `APP_ENV` | `local`, `test`, `staging`, `production`, `demo` (D-11) |
| `DATABASE_URL` | URL `postgresql+asyncpg://…` (obligatoire) |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `CORS_ALLOWED_ORIGINS` | Origines autorisées, séparées par des virgules |
| `DEMO_MODE` | `true` seulement avec `APP_ENV=demo` (D-18) |
| `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, `DATABASE_CONNECT_TIMEOUT_SECONDS`, `DATABASE_STATEMENT_TIMEOUT_MS`, `READINESS_TIMEOUT_SECONDS` | Réglages facultatifs de la base |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Base de développement créée par Compose |
| `POSTGRES_TEST_PASSWORD`, `TEST_DATABASE_URL` | Base de test éphémère |
| `MADASOURCE_DB_HOST_PORT`, `MADASOURCE_API_HOST_PORT`, `MADASOURCE_TEST_DB_HOST_PORT` | Ports de l'hôte |

En `production`, le démarrage est refusé si : origine CORS `*` ou non HTTPS, `DEMO_MODE` actif, mot de passe d'exemple de `.env.example`. La documentation interactive y est désactivée.

## Dépendances

Versions épinglées exactement dans `pyproject.toml` ; dépendances transitives figées par `uv.lock`.

| Paquet | Version | Justification |
|---|---|---|
| `fastapi` | 0.143.0 | Framework de l'API (stack imposée) |
| `uvicorn` | 0.54.0 | Serveur ASGI qui exécute l'application, en local et dans l'image Docker |
| `pydantic` | 2.14.1 | Validation et schémas (stack imposée : Pydantic v2), épinglé explicitement |
| `pydantic-settings` | 2.15.0 | Configuration lue dans l'environnement et validée au démarrage (D-11, Jour 5). Bibliothèque de l'équipe Pydantic ; apporte `python-dotenv` (dépendance transitive, non utilisée par l'application : aucun fichier `.env` n'est lu implicitement) |
| `sqlalchemy[asyncio]` | 2.1.4 | ORM asynchrone (stack imposée : SQLAlchemy 2.x async) ; l'extra installe `greenlet` |
| `asyncpg` | 0.32.0 | Pilote PostgreSQL asynchrone (D-10, choix du 2026-10-13) |
| `alembic` | 1.20.0 | Migrations (stack imposée) |
| `pytest` (dev) | 9.1.1 | Tests (stack imposée) ; tests asynchrones par le plugin d'AnyIO, déjà installé avec Starlette |
| `httpx2` (dev) | 2.13.1 | Client HTTP du `TestClient` de Starlette. Starlette 1.7 rend obsolète l'usage de `httpx` au profit de `httpx2`, publié par l'auteur de `httpx` (dépôt `pydantic/httpx2`) |
| `ruff` (dev) | 0.17.0 | Lint et formatage (stack imposée) |
| `mypy` (dev) | 2.4.0 | Vérification de types, en mode strict, avec le greffon Pydantic |

## Structure

```text
backend/
├── app/
│   ├── main.py                 fabrique create_app() : configuration, cycle de vie, middlewares, erreurs, routers
│   ├── api/v1/router.py        routeur /api/v1
│   ├── api/v1/endpoints/       health.py (sondes)
│   ├── core/                   config.py, exceptions.py, errors.py (Problem Details), logging.py, middleware.py
│   └── db/session.py           moteur asyncpg, session par requête (DbSession)
├── alembic/                    env.py asynchrone, gabarit conforme à Ruff ; versions/ vide (Jour 6)
├── tests/
│   ├── unit/                   configuration, journaux, exceptions
│   ├── api/                    sondes, erreurs, middlewares, OpenAPI (sans base)
│   ├── integration/            base de test : sonde ready, session par requête
│   ├── conftest.py, support.py fixtures et configuration de test explicite
├── alembic.ini
├── Dockerfile                  multi-étapes, UID 10001 non root, uv sync --locked --no-dev, uvicorn --factory
├── pyproject.toml
├── uv.lock
└── .python-version
```

Les modules métier (`app/modules/…`) sont créés au jour de leur implémentation, jamais à l'avance. Architecture et conventions : [`docs/backend/`](../docs/backend/).
