# Backend MadaSource

API REST FastAPI de MadaSource (monolithe modulaire). État au Jour 4 : squelette du dépôt, application minimale et sonde de vivacité `GET /api/v1/health/live`, sans logique métier.

Ce fichier est la **source de vérité des commandes** du backend. Les autres documents, y compris les skills de Claude Code, renvoient ici.

## Prérequis

| Outil | Version | Rôle |
|---|---|---|
| Python | 3.14 (`.python-version`) | Exécution (D-27) |
| uv | 0.13.0 (imposée par `required-version` dans `pyproject.toml`) | Environnement virtuel et dépendances, à partir de `uv.lock` |
| Docker et Docker Compose | Docker 29, Compose 5 (versions du poste de développement) | PostgreSQL et backend en conteneurs |

## Installation

Depuis `backend/` :

```bash
uv sync --locked   # crée backend/.venv à partir de uv.lock (dépendances et outils de dev)
```

`--locked` refuse d'installer si `uv.lock` ne correspond plus à `pyproject.toml`. Après une modification volontaire des dépendances : `uv lock`, puis relecture du diff de `uv.lock`.

## Commandes officielles

Depuis `backend/` :

| Contrôle | Commande |
|---|---|
| Verrou à jour | `uv lock --check` |
| Lint | `uv run ruff check .` |
| Format (vérification) | `uv run ruff format --check .` |
| Types | `uv run mypy` (mode strict ; fichiers déclarés dans `pyproject.toml`) |
| Tests | `uv run pytest` |
| Serveur local | `uv run uvicorn app.main:app --reload --port 8002` |
| Migrations : têtes | `uv run alembic heads` |
| Migrations : SQL hors ligne | `uv run --env-file ../.env alembic upgrade head --sql` |
| Migrations : application | `uv run --env-file ../.env alembic upgrade head` (base démarrée) |

Points de fonctionnement :
- les tests transforment tout avertissement en erreur (`filterwarnings = error`) : un avertissement d'obsolescence fait échouer la suite au lieu de passer inaperçu ;
- Alembic lit l'URL de la base dans la variable d'environnement `DATABASE_URL`, jamais dans `alembic.ini`. Rien ne charge `.env` automatiquement : l'option `--env-file ../.env` de `uv run` le fait (elle fonctionne aussi sous fish, contrairement à `source .env`) ;
- chaque révision générée par Alembic est corrigée puis formatée par Ruff (hooks `post_write_hooks` d'`alembic.ini`) ;
- aucune migration n'existe au Jour 4 ; la configuration est finalisée au Jour 6. Règles : skill `database-migrations` ; jamais de `downgrade base` ni de réinitialisation d'une base.

## Docker Compose

> **Non vérifié au Jour 4.** Le téléchargement des images Docker n'a pas été autorisé : seule la syntaxe de `docker-compose.yml` a été validée (`docker compose --env-file .env.example config`). La procédure ci-dessous est celle prévue ; elle sera exécutée dès que le téléchargement des images sera autorisé.

Depuis la racine du dépôt :

```bash
cp .env.example .env         # puis remplacer les valeurs factices
docker compose up -d --build # PostgreSQL 18 et backend
docker compose ps            # attendu : les deux services « healthy »
curl http://127.0.0.1:8001/api/v1/health/live
docker compose down          # arrêt ; ne jamais ajouter -v, qui supprime le volume de données
```

| Service | Image | Port hôte (défaut) | Santé |
|---|---|---|---|
| `db` | `postgres:18.6-trixie` | `127.0.0.1:5433` | `pg_isready -h 127.0.0.1` (par TCP) |
| `backend` | construite depuis `backend/Dockerfile` | `127.0.0.1:8001` | `GET /api/v1/health/live` |

Les données PostgreSQL sont dans le volume nommé `madasource_pgdata`. Les ports 5432, 6379 et 8000 sont souvent déjà occupés sur le poste : les ports hôte se changent par `MADASOURCE_DB_HOST_PORT` et `MADASOURCE_API_HOST_PORT`. Le serveur local (`uvicorn`, port 8002) et le backend de Compose (port 8001) peuvent tourner en même temps.

## Variables d'environnement

Toutes sont documentées dans `.env.example` (racine), avec des valeurs factices.

| Variable | Usage |
|---|---|
| `APP_ENV` | Environnement : `local`, `test`, `staging`, `production`, `demo` (D-11) ; validé à partir du Jour 5 |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Base créée par Docker Compose |
| `MADASOURCE_DB_HOST_PORT`, `MADASOURCE_API_HOST_PORT` | Ports de l'hôte |
| `DATABASE_URL` | URL de la base pour l'application et Alembic lancés depuis l'hôte |

## Dépendances

Versions épinglées exactement dans `pyproject.toml` ; dépendances transitives figées par `uv.lock`.

| Paquet | Version | Justification |
|---|---|---|
| `fastapi` | 0.143.0 | Framework de l'API (stack imposée) |
| `uvicorn` | 0.54.0 | Serveur ASGI qui exécute l'application, en local et dans l'image Docker |
| `pydantic` | 2.14.1 | Validation et schémas (stack imposée : Pydantic v2), épinglé explicitement |
| `sqlalchemy[asyncio]` | 2.1.4 | ORM asynchrone (stack imposée : SQLAlchemy 2.x async) ; l'extra installe `greenlet` |
| `asyncpg` | 0.32.0 | Pilote PostgreSQL asynchrone (D-10, choix du 2026-10-13) |
| `alembic` | 1.20.0 | Migrations (stack imposée) |
| `pytest` (dev) | 9.1.1 | Tests (stack imposée) |
| `httpx2` (dev) | 2.13.1 | Client HTTP du `TestClient` de Starlette. Starlette 1.7 rend obsolète l'usage de `httpx` au profit de `httpx2`, publié par l'auteur de `httpx` (dépôt `pydantic/httpx2`) |
| `ruff` (dev) | 0.17.0 | Lint et formatage (stack imposée) |
| `mypy` (dev) | 2.4.0 | Vérification de types, en mode strict, avec le greffon Pydantic |

Aucune autre dépendance : configuration validée (`pydantic-settings`), journalisation et tests asynchrones seront ajoutés et justifiés aux Jours 5 et 6, s'ils sont nécessaires.

## Structure

```text
backend/
├── app/
│   └── main.py          application minimale : GET /api/v1/health/live ; GET /hello (ajouté par
│                        l'utilisateur au Jour 4) ; fabrique d'application au Jour 5
├── alembic/             env.py asynchrone, gabarit conforme à Ruff ; versions/ vide (Jour 6)
├── tests/
│   └── api/             tests smoke de la sonde, de l'OpenAPI et de /hello
├── alembic.ini
├── Dockerfile           multi-étapes, UID 10001 non root, uv sync --locked --no-dev
├── pyproject.toml
├── uv.lock
└── .python-version
```

L'API et son schéma OpenAPI sont servis sous `/api/v1` (`/api/v1/openapi.json`, `/api/v1/docs`), conformément à [`api-conventions.md`](../docs/backend/api-conventions.md). Les modules métier (`app/modules/…`) sont créés au jour de leur implémentation, jamais à l'avance. Architecture et conventions : [`docs/backend/`](../docs/backend/).
