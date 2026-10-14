# Backend MadaSource

API REST FastAPI de MadaSource (monolithe modulaire). État au Jour 6 : fondation de l'application (configuration validée, fabrique d'application, routeur `/api/v1`, sondes de santé, erreurs au format Problem Details, journaux JSON, CORS), base déclarative SQLAlchemy, migrations Alembic, deux rôles PostgreSQL et base de test isolée ; aucune table métier.

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
| Migrations | voir la section « Migrations » ci-dessous |

Points de fonctionnement :
- **tests** : marqueurs `unit` (sans base ni HTTP), `api` (client HTTP en mémoire, sans base), `integration` (base de test). Tout avertissement est traité comme une erreur (`filterwarnings = error`). Sans `TEST_DATABASE_URL` et `TEST_MIGRATION_DATABASE_URL`, les tests d'intégration **échouent** avec la marche à suivre : ils ne sont jamais ignorés ;
- **base de test** : service `db-test` (profil `test`), données en mémoire (`tmpfs`), vides à chaque démarrage, port hôte 5434. Le schéma y est créé une fois par session de tests par `alembic upgrade head` (propriétaire du schéma) ; l'application s'y connecte avec le rôle applicatif ; chaque test d'intégration travaille dans une transaction annulée à la fin, la session de requête la rejoignant par points de sauvegarde. La configuration de test refuse toute base dont le nom ne se termine pas par `_test`. Jamais la base de développement ;
- **serveur** : `--factory` appelle `create_app()`, qui lit et valide la configuration ; `--no-access-log` laisse un seul journal d'accès, celui de l'application (D-12) ; `--no-server-header` retire la bannière `server: uvicorn` ;
- **base de données** : deux rôles. L'application utilise `madasource_app` (`DATABASE_URL`) : lecture et écriture des données, aucun droit sur le schéma. Alembic utilise le propriétaire du schéma (`MIGRATION_DATABASE_URL`). Une connexion refusée, un délai dépassé ou une authentification refusée donnent 503 `SERVICE_UNAVAILABLE`, jamais 500.

## Migrations

Depuis `backend/`, avec `MIGRATION_DATABASE_URL` (propriétaire du schéma) ; règles : skill `database-migrations`.

| Action | Commande |
|---|---|
| État de la base | `uv run --env-file ../.env alembic current` |
| Têtes et historique (sans base) | `uv run alembic heads` ; `uv run alembic history --verbose` |
| Appliquer jusqu'à la tête | `uv run --env-file ../.env alembic upgrade head` |
| Relire le SQL sans l'appliquer | `uv run --env-file ../.env alembic upgrade head --sql` |
| Écart entre modèles et base | `uv run --env-file ../.env alembic check` (« No new upgrade operations detected. ») |
| Nouvelle révision à partir des modèles | `uv run --env-file ../.env alembic revision --autogenerate -m "<message en anglais>"`, puis **relecture ligne à ligne** |
| Nouvelle révision écrite à la main | `uv run alembic revision -m "<message en anglais>"` (droits, contraintes `CHECK`, données de référence) |

Règles :
- une migration par changement cohérent, relue avant application ; une révision appliquée ou partagée n'est jamais modifiée : on en crée une nouvelle ;
- chaque révision générée est corrigée puis formatée par Ruff (hooks d'`alembic.ini`) ; les fichiers sont nommés `AAAAMMJJ_HHMM_<révision>_<message>.py` (UTC) ;
- l'autogénération ne voit pas les contraintes `CHECK` ni les droits : ils s'écrivent à la main (`indexes-and-constraints.md` §3.5) ;
- **chaque migration qui crée une table accorde explicitement ses droits** au rôle `madasource_app` (`GRANT`, par table et par colonne, `indexes-and-constraints.md` §6.2) : sans cela, l'application ne peut pas l'utiliser ;
- **retour arrière prudent** : `uv run --env-file ../.env alembic downgrade -1`, une révision à la fois, seulement sur une base de développement ou de test, après relecture du `downgrade` et sauvegarde si des données existent. Ne jamais descendre sous la première révision (`03d1bd152b99`) : ce serait un `downgrade base`. Jamais de réinitialisation de base ni de suppression de volume pour « réparer » ; jamais sur une base de production ;
- **exécution** : un verrou consultatif sérialise les migrations (une seconde migration simultanée attend la première) ; ensuite, une migration qui attend un verrou de table plus de 10 s échoue au lieu de bloquer le trafic. Le SQL hors ligne (`--sql`) contient les mêmes protections ;
- les migrations ne s'exécutent pas au démarrage de l'application (D-26).

Rôle applicatif : il est créé par `infrastructure/postgres/10-create-app-role.sh` à l'initialisation d'une base vide. Pour une base déjà initialisée (volume existant), relancer le script, idempotent :

```bash
docker compose exec db sh /docker-entrypoint-initdb.d/10-create-app-role.sh
```

La première migration (`schema privileges baseline`) refuse de s'appliquer si ce rôle n'existe pas ; la deuxième (`verify schema privileges`) échoue si les droits n'ont pas réellement pris effet. Le script n'est exécuté automatiquement qu'à l'initialisation d'une base vide ; le dossier `infrastructure/postgres` est monté, donc une modification du script est visible sans recréer le conteneur.

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
| `APP_ENV` | **Obligatoire** : `local`, `test`, `staging`, `production`, `demo` (D-11) |
| `DATABASE_URL` | URL `postgresql+asyncpg://…` du rôle applicatif `madasource_app` (obligatoire) |
| `MIGRATION_DATABASE_URL` | URL du propriétaire du schéma, pour Alembic seulement |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `CORS_ALLOWED_ORIGINS` | Origines autorisées, séparées par des virgules |
| `DEMO_MODE` | `true` seulement avec `APP_ENV=demo` (D-18) |
| `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, `DATABASE_CONNECT_TIMEOUT_SECONDS`, `DATABASE_STATEMENT_TIMEOUT_MS`, `DATABASE_LOCK_TIMEOUT_MS`, `DATABASE_IDLE_IN_TRANSACTION_TIMEOUT_MS`, `READINESS_TIMEOUT_SECONDS` | Réglages facultatifs de la base (délais : Q-103) |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Base de développement créée par Compose ; `POSTGRES_USER` en est le propriétaire du schéma |
| `POSTGRES_APP_PASSWORD` | Mot de passe du rôle applicatif sur la base de développement |
| `POSTGRES_TEST_PASSWORD`, `POSTGRES_TEST_APP_PASSWORD`, `TEST_DATABASE_URL`, `TEST_MIGRATION_DATABASE_URL` | Base de test éphémère (propriétaire et rôle applicatif) |
| `MADASOURCE_DB_HOST_PORT`, `MADASOURCE_API_HOST_PORT`, `MADASOURCE_TEST_DB_HOST_PORT` | Ports de l'hôte |

Garde-fous au démarrage : en `staging`, `production` et `demo`, refus d'une origine CORS `*`, du mot de passe d'exemple de `.env.example` et d'un mot de passe de base de moins de 12 caractères (extension à `staging` et `demo` à valider, Q-102) ; en `production`, refus en plus des origines non HTTPS et de `LOG_LEVEL=DEBUG`. La documentation interactive est désactivée en `production` et en `demo`.

Compose exige ses variables pour toute commande, même sans le profil `test`. Un `.env` copié avant le Jour 6 est à compléter à partir de `.env.example` : `POSTGRES_APP_PASSWORD`, `MIGRATION_DATABASE_URL`, `POSTGRES_TEST_APP_PASSWORD`, `TEST_MIGRATION_DATABASE_URL`, et `DATABASE_URL` et `TEST_DATABASE_URL` qui passent au rôle `madasource_app`.

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
│   └── db/                     base.py (base déclarative, nommage, UUIDv7), registry.py (découverte des
│                               modèles), roles.py (rôle applicatif), session.py (moteur, DbSession)
├── alembic/                    env.py asynchrone ; versions/ : socle des droits sur le schéma (Jour 6)
├── tests/
│   ├── unit/                   configuration, journaux, exceptions, base déclarative
│   ├── api/                    sondes, erreurs, middlewares, OpenAPI, journaux (sans base)
│   ├── integration/            base de test : migrations, droits du rôle applicatif, sessions, sondes
│   ├── conftest.py, support.py fixtures et configuration de test explicite
├── alembic.ini
├── Dockerfile                  multi-étapes, UID 10001 non root, uv sync --locked --no-dev, uvicorn --factory
├── pyproject.toml
├── uv.lock
└── .python-version
```

Les modules métier (`app/modules/…`) sont créés au jour de leur implémentation, jamais à l'avance. Architecture et conventions : [`docs/backend/`](../docs/backend/).
