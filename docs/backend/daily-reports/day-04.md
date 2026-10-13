# Jour 4 — Initialisation du dépôt

Date : 2026-10-13 · Statut : **TERMINÉ AVEC RÉSERVES**. Réserves :
- **Docker non vérifié** : l'utilisateur a autorisé les téléchargements Python, pas ceux des images Docker. Le Dockerfile et `docker-compose.yml` sont écrits, et la syntaxe de Compose est validée ; ni build ni démarrage n'ont été faits ;
- **le dépôt GitHub est public** (constaté ce jour, R-26, Q-71) : action de l'utilisateur requise.

## Objectif du jour

Consigne de `roadmap_backend_fastapi.md`, Jour 4 :
- créer le squelette (`backend/app`, `backend/tests`, `backend/alembic`, `.gitignore`, `.env.example`, `README.md`, `backend/pyproject.toml`, `backend/Dockerfile`, `docker-compose.yml`) ;
- configurer Python, FastAPI, SQLAlchemy async, Pydantic v2, Alembic, PostgreSQL, Pytest et Ruff avec des versions épinglées ;
- faire démarrer par Compose le backend et PostgreSQL, avec healthchecks et volume persistant ;
- ajouter un endpoint health minimal et un test smoke, sans workflow métier ;
- vérifier l'installation et le démarrage depuis un environnement propre.

Consignes de l'utilisateur : ne pas refaire ce qui existe (dépôt Git, documentation) ; aucun frontend.

## Décisions prises avec l'utilisateur (2026-10-13)

| Sujet | Choix | Effet |
|---|---|---|
| Python (D-27) | **3.14** | 3.14.8 en local ; image `python:3.14.8-slim-trixie` |
| PostgreSQL | **18** | Image `postgres:18.6-trixie` |
| Pilote (D-10) | **asyncpg** | 0.32.0 |
| Téléchargements | **Python seulement** | Paquets dans `backend/.venv` ; aucune image Docker |

Conséquences proposées :
- **D-15** : UUIDv7 généré par l'application (`uuid.uuid7()`, présent dans Python 3.14.8, vérifié), mis en œuvre au Jour 6 ;
- **vérificateur de types** : mypy, en mode strict.

## Prérequis vérifiés

- Jours 1 à 3 présents ; `check.md` : Jour 3 « OK avec réserves » (Trade provisoire, Q-82). Le Jour 4 ne dépend pas de Q-82.
- Dépôt Git existant (branche `main`, remote GitHub), non réinitialisé. Arbre propre au départ. L'utilisateur a commité et poussé le travail en cours plusieurs fois pendant la journée, jusqu'au commit `e11a456`.
- Outils du poste : uv 0.13.0, Python 3.14.8 et 3.12.14, Docker 29.9.0, Compose 5.6.0. Ports occupés : 5432 et 6379 ; 5433, 8001 et 8002 libres.
- **Visibilité du dépôt** : `https://api.github.com/repos/bry4ng4rrix/Madasource` répond **200** sans authentification, donc le dépôt est **public**.

## Fichiers

**Créés** :

| Fichier | Contenu |
|---|---|
| `backend/pyproject.toml` | 6 dépendances et 4 outils épinglés exactement ; configuration de uv (`required-version`), Ruff, mypy strict, Pytest |
| `backend/uv.lock`, `backend/.python-version` | Verrou complet (37 paquets) ; Python 3.14 |
| `backend/app/__init__.py`, `backend/app/main.py` | Application minimale : `GET /api/v1/health/live`, OpenAPI sous `/api/v1` |
| `backend/tests/api/test_health.py`, `test_hello.py` | 4 tests : sonde, présence dans l'OpenAPI, absence de documentation hors `/api/v1`, `/hello` |
| `backend/alembic.ini`, `backend/alembic/` | Squelette asynchrone : URL lue dans `DATABASE_URL`, gabarit de migration conforme à Ruff, hooks Ruff après génération ; aucune migration |
| `backend/Dockerfile`, `backend/.dockerignore` | Multi-étapes, uv 0.13.0, `uv sync --locked --no-dev`, UID 10001 non root, fichiers appartenant à root |
| `docker-compose.yml` | `db` (PostgreSQL 18) et `backend`, healthchecks, volume `madasource_pgdata`, ports liés à 127.0.0.1 |
| `.env.example` | Variables documentées, valeurs factices |
| `README.md`, `backend/README.md` | Présentation ; commandes officielles (source de vérité), dépendances justifiées |
| `docs/backend/daily-reports/day-04.md` | Ce rapport |

**Modifiés** :
- `.gitignore` : `.env`, `.env.*` (sauf `.env.example`), environnements virtuels, caches. Tes lignes sont conservées.
- `docs/backend/architecture.md` : D-10, D-15 et D-27 retenus ou proposés ; ajout de mypy ; uv retenu ; `pydantic-settings` reporté au Jour 5.
- `docs/backend/error-handling.md` : pilote asyncpg.
- `docs/backend/risks-and-open-questions.md` : R-20 clos ; R-26 et Q-71 (dépôt public).
- `CLAUDE.md` (local, non versionné) : stack et faits du dépôt.
- `backend/app/main.py` : ton endpoint `/hello` a été conservé. Deux changements autour : sa mise en forme (une ligne vide en trop, un saut de ligne final manquant), et un test qui lui est dédié.

## Démarche et incidents

| Étape | Résultat |
|---|---|
| Résolution des versions | `uv lock` : FastAPI 0.143.0, Starlette 1.7.0, Pydantic 2.14.1, SQLAlchemy 2.1.4, asyncpg 0.32.0, Alembic 1.20.0, uvicorn 0.54.0, Pytest 9.1.1, Ruff 0.17.0, mypy 2.4.0 ; toutes compatibles avec Python 3.14 |
| Test client et `httpx` | Starlette 1.7 déclare obsolète `httpx` pour son `TestClient`, ce qui fait échouer la suite (avertissements traités comme erreurs). Remplacé par `httpx2` 2.13.1, après vérification : publié par l'auteur de `httpx`, dépôt `pydantic/httpx2`, et Starlette le liste dans ses propres dépendances. Le filtre d'avertissements n'a pas été assoupli |
| Tri des imports | Ruff classait le dossier `alembic/` comme module du projet : `known-first-party = ["app"]` et `known-third-party = ["alembic"]` |
| Images Docker | Tags vérifiés dans les registres sans télécharger d'image (métadonnées) : `python:3.14.8-slim-trixie`, `postgres:18.6-trixie`, `ghcr.io/astral-sh/uv:0.13.0`. Configuration de PostgreSQL 18 lue : `PGDATA=/var/lib/postgresql/18/docker`, volume `/var/lib/postgresql` |
| Chemins de l'API | Première version avec la sonde et l'OpenAPI à la racine, en écart avec les décisions du Jour 2 (`api-conventions.md` §3 et §13). Code aligné : `/api/v1/health/live`, `/api/v1/openapi.json`, `/api/v1/docs` |
| Revue DevOps (agent `devops-engineer`) | 0 bloquant, 5 importants, 9 mineurs. Principaux : `--frozen` au lieu de `--locked`, `.dockerignore` sans effet sur les sous-dossiers, faux « healthy » au premier démarrage de PostgreSQL, `.env` non chargé hors Docker, nom réel du volume. Corrigés, sauf l'épinglage par digest (Jour 7) |
| Revue finale (skill `code-review-madasource`) | Prêt avec réserves, 0 bloquant. Principaux : Docker présenté comme vérifié dans les README, gabarit de migration non conforme à Ruff, documents périmés, R-26 à reformuler. Corrigés |
| Revue contradictoire (workflow, 3 dimensions et vérificateurs) | Voir « Vérification finale » |

## Commandes exécutées et résultats réels

| Commande | Résultat |
|---|---|
| `curl https://api.github.com/repos/bry4ng4rrix/Madasource` | HTTP 200 : dépôt public |
| `git check-ignore -v .env .env.local backend/.venv/x` ; `git check-ignore .env.example` | Les trois premiers sont ignorés ; `.env.example` ne l'est pas |
| `uv lock` puis `uv sync` | 36 paquets résolus pour CPython 3.14.8, installés dans `backend/.venv` |
| Import des paquets et `hasattr(uuid, "uuid7")` | Versions attendues ; `True` |
| `uv run alembic init -t async alembic` | Squelette créé, puis adapté |
| `uv lock --check` | « Resolved 37 packages », code 0 |
| `uv run ruff check .` / `uv run ruff format --check .` | All checks passed / 6 files already formatted |
| `uv run mypy` | Success: no issues found in 5 source files |
| `uv run pytest` | **4 passed** |
| `uv run alembic heads` | Code 0, aucune tête |
| `alembic current` sans `DATABASE_URL` | `RuntimeError: DATABASE_URL n'est pas définie : voir .env.example.` |
| `uv run --env-file ../.env.example alembic upgrade head --sql` | `BEGIN;` puis `COMMIT;`, code 0 (mode hors ligne, sans base) |
| Deux révisions générées dans une **copie** de `backend/` | Gabarit et hooks : les deux fichiers passent `ruff check` et `ruff format --check`. Le dépôt réel n'a aucune migration |
| Copie propre (sans `.venv` ni caches) : `uv sync --locked`, Ruff, mypy, Pytest | Tout réussit (4 passed) : installation reproductible depuis `uv.lock` |
| `uvicorn app.main:app --port 8002` depuis la copie propre, puis `curl` | `/api/v1/health/live` 200 `{"status":"ok"}` ; `/hello` 200 ; `/api/v1/openapi.json` et `/api/v1/docs` 200 ; `/openapi.json` et `/docs` 404. Serveur arrêté par son PID, port libéré |
| `docker compose --env-file .env.example config --quiet` | Code 0 ; ports `127.0.0.1:5433` et `127.0.0.1:8001`, volume `madasource_pgdata` |
| `docker compose config --quiet` sans `.env` | Refus explicite : « POSTGRES_USER manquant, voir .env.example » |
| Recherche de motifs de secrets | Seulement des valeurs factices (`.env.example`) et des commentaires |

**Non exécuté**, par décision de l'utilisateur : `docker compose build`, `up`, `ps` et le test de persistance du volume.

## Vérification finale

À compléter avec le résultat de la revue contradictoire.

## Critères de sortie

| Critère (roadmap §5) | État |
|---|---|
| Périmètre implémenté et cohérent | **Partiel** : squelette, versions épinglées, application, test smoke et Compose écrits ; démarrage par Compose **non vérifié** (images non autorisées) |
| Tests appropriés et résultat connu | Oui : 4 tests, 4 réussis, y compris depuis une copie propre |
| Migrations et contraintes cohérentes | Sans objet (aucune migration) ; Alembic configuré, gabarit testé |
| Documentation et `.env.example` à jour | Oui |
| Aucun secret ajouté | Oui : `.env` ignoré et absent ; valeurs factices seulement |
| Défauts critiques corrigés ou signalés | Signalé : dépôt public (R-26, Q-71), action de l'utilisateur |
| Décisions non définies marquées `À VALIDER` | Oui (section suivante) |

## Décisions À VALIDER

| Sujet | Échéance |
|---|---|
| **Q-71 : passer le dépôt GitHub en privé** ; le cahier des charges et la conception de sécurité y sont publics | **Immédiat** |
| Autoriser le téléchargement des images Docker (`postgres:18.6-trixie`, `python:3.14.8-slim-trixie`, `ghcr.io/astral-sh/uv:0.13.0`) pour vérifier Compose | Avant le Jour 5, qui teste la disponibilité de la base |
| Garder ou retirer `/hello` : hors du préfixe `/api/v1` (`api-conventions.md`) et hors du périmètre de la roadmap | Avant le Jour 5 |
| D-15 : UUIDv7 généré par l'application | Jour 6 |
| Décisions du Jour 3 en attente, dont **Q-82** (Trade) | Voir `day-03.md` |

## Risques et limites

- **Docker non vérifié** : une erreur de build ou de démarrage reste possible (chemins, permissions UID 10001, healthchecks). Revue statique seulement.
- **Dépôt public** : tout fichier poussé est lisible par tous, historique compris.
- **Versions récentes** : Starlette 1.7 a déjà rendu `httpx` obsolète ; d'autres changements de ce type sont possibles. Le filtre `filterwarnings = error` les révélera dès qu'ils apparaîtront.
- **Base de données** : aucune connexion réelle n'a été testée (pas de PostgreSQL du projet démarré). Le PostgreSQL natif du poste (port 5432) appartient à d'autres projets et n'a pas été utilisé.

## Préparation du Jour 5 (non exécuté)

Jour 5 — Base FastAPI et gestion des erreurs : fabrique d'application, configuration validée par environnement, routeur `/api/v1`, `/health/live`, `/health/ready` (vérifie la base), erreurs centralisées au format de `error-handling.md`, logs structurés sans secrets, OpenAPI, CORS configurable, cycle de vie, dépendance de session.

Prérequis :
- **une base PostgreSQL pour tester `/health/ready`** : soit l'autorisation de télécharger l'image `postgres:18.6-trixie` (recommandé), soit ton accord explicite pour une base dédiée sur le PostgreSQL natif du poste ;
- justification de `pydantic-settings` (configuration validée, D-11) ;
- décision sur `/hello`.

**Le Jour 5 ne sera pas lancé sans ta validation explicite.**
