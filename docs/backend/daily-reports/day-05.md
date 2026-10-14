# Jour 5 — Base FastAPI et gestion des erreurs

Date : 2026-10-13 et 2026-10-14 · Statut : **TERMINÉ AVEC RÉSERVES**. Réserves :
- Q-102 : garde-fous de configuration étendus à `staging` et `demo`, à confirmer ;
- le dépôt GitHub est toujours public (Q-71, hérité du Jour 4).

## Objectif du jour

Consigne de `roadmap_backend_fastapi.md`, Jour 5 :
- configuration validée par environnement, fabrique d'application, routeur `/api/v1` ;
- `/health/live` et `/health/ready`, cette dernière vérifiant la base ;
- gestion centralisée des erreurs au format cohérent, journaux structurés sans secrets ;
- OpenAPI, CORS configurable, cycle de vie propre, dépendance de session ;
- aucune logique métier dans `main.py`, tests API, documentation du démarrage, Ruff, types et Pytest.

## Décisions prises avec l'utilisateur

| Sujet | Choix |
|---|---|
| Base pour vérifier `/health/ready` | Téléchargement des images Docker autorisé (PostgreSQL 18, Python 3.14, uv) ; ce choix a aussi levé la réserve Docker du Jour 4 |
| Endpoint `/hello` (ajouté par l'utilisateur au Jour 4) | Retiré |
| D-24, membre `type` des erreurs (RFC 9457) | `about:blank` : `title` = phrase HTTP standard ; le sens est porté par `code` |

Choix techniques, documentés :
- `pydantic-settings` 2.15.0 pour la configuration (D-11) ;
- base de test éphémère `db-test` (Compose, profil `test`, `tmpfs`, port 5434) ;
- plugin pytest d'AnyIO pour les futurs tests asynchrones (aucun nécessaire au Jour 5).

## Prérequis vérifiés

- Jour 4 : versions épinglées, `uv.lock`, application minimale, Compose. Docker a été vérifié au début du Jour 5 (build, santé, Alembic, persistance du volume).
- La revue contradictoire du Jour 4 (11 constats confirmés) a été traitée avant le code du Jour 5 (`day-04.md`).

## Fichiers

**Créés** (`backend/`) :

| Fichier | Contenu |
|---|---|
| `app/core/config.py` | `Settings` (pydantic-settings) : `APP_ENV` obligatoire, URL `postgresql+asyncpg` analysée sans jamais citer sa valeur, origines CORS, garde-fous des environnements déployés, base de test en `_test` |
| `app/core/exceptions.py` | Hiérarchie `AppError` du catalogue (`error-handling.md` §5), en-têtes `WWW-Authenticate` et `Retry-After` |
| `app/core/errors.py` | Réponses Problem Details ; gestionnaires 422 (sans valeur saisie), HTTP du framework, SQLSTATE (409, 503), 500 (avec `X-Request-ID`, en-têtes de sécurité et CORS) ; journaux 500 sans message d'exception |
| `app/core/logging.py` | JSON sur la sortie standard, nettoyage récursif des champs sensibles, redirection des journaux d'uvicorn, suppression de son doublon des 500 |
| `app/core/middleware.py` | Middleware ASGI pur : `X-Request-ID` (UUID valide ou UUIDv7 généré), journal d'accès unique sans chaîne de requête, en-têtes de sécurité, marquage DEMO |
| `app/db/session.py` | Moteur asyncpg (`hide_parameters`, `statement_timeout`, délai de connexion), session par requête de portée `function` (`DbSession`) |
| `app/api/v1/router.py`, `endpoints/health.py` | Routeur `/api/v1` (422 documenté en Problem Details) ; sondes `live` et `ready` |
| `tests/` | `conftest.py`, `support.py` ; `unit/core/` (configuration, journaux, erreurs) ; `api/` (sondes, erreurs, middlewares, OpenAPI, journaux) ; `integration/` (base de test) |
| `docs/backend/daily-reports/day-05.md` | Ce rapport |

**Modifiés** :
- `app/main.py` : fabrique `create_app()` (configuration, journalisation, cycle de vie, CORS, middlewares, erreurs, routeur) ; `/hello` retiré, avec son test ;
- `pyproject.toml`, `uv.lock` : `pydantic-settings`, marqueurs de tests, configuration de mypy ;
- `Dockerfile` : `uvicorn --factory … --no-access-log --no-server-header` ;
- `docker-compose.yml` : service `db-test`, variables `LOG_LEVEL` et `CORS_ALLOWED_ORIGINS` ;
- `.env.example` : nouvelles variables et garde-fous ;
- `backend/README.md`, `README.md` : commandes, base de test, API, variables, dépendances ;
- `docs/backend/` :
  - `error-handling.md` : D-24, codes `BAD_REQUEST` et `CONFLICT`, règles implémentées, journal des 500 ;
  - `architecture.md` : D-11, D-24, §4 ;
  - `api-conventions.md` : §11 ;
  - `testing-strategy.md` : §3, §4, §5 ;
  - `risks-and-open-questions.md` : Q-102 ;
- `.claude/tests/test_hooks.py` : un cas isolé dans un projet temporaire (section « Démarche »).

## Démarche et revues

| Étape | Résultat |
|---|---|
| Lecture des spécifications | `architecture.md` §3 à §7, `error-handling.md`, `api-conventions.md` §11 à §13, `security-design.md` §15 à §18, `testing-strategy.md` |
| Vérifications préalables dans les sources installées | `Depends(…, scope="function")` existe (FastAPI 0.143) ; SQLAlchemy expose `exc.orig.sqlstate` pour asyncpg |
| Écarts découverts en codant | **FastAPI 0.143 n'aplatit plus les routes incluses** (`_IncludedRouter`) : le test « toutes les routes sous `/api/v1` » passait à vide. Il utilise maintenant `iter_route_contexts`, public. **Pydantic recopiait l'URL de la base** (avec le mot de passe) dans l'erreur de configuration : corrigé par `hide_input_in_errors`, puis par l'analyse protégée de l'URL |
| Revue de code (skill `code-review-madasource`) | Premier essai interrompu par une coupure réseau, relancé. Prêt avec réserves, 0 bloquant, 6 importants. Principaux : `WWW-Authenticate` perdu (casse), bannière `server: uvicorn`, 422 OpenAPI au mauvais format, traces journalisées non nettoyées, tests de journaux absents, suivi incohérent. Tous corrigés |
| Audit de sécurité (agent `security-auditor`) | Premier essai interrompu par la même coupure, relancé. 0 critique, 2 élevés, 1 moyen, 6 faibles. Élevés : fragment du mot de passe dans l'erreur de démarrage (`ValueError` de l'analyse du port) ; messages d'exception (DETAIL asyncpg, données d'une réponse) dans les journaux 500. Moyen : garde-fous contournables (`APP_ENV` omis, mot de passe court, staging et demo). Tous corrigés et testés ; le moyen ouvre Q-102 |
| Vérification ciblée des correctifs (agent `security-auditor`) | Voir « Vérification finale » |
| Auto-test des hooks | Un cas échouait depuis la création de `backend/.venv` au Jour 4 : le hook préfère le Ruff du projet au faux binaire du test. Test isolé dans un projet temporaire, assertion inchangée : 0 échec |

## Commandes exécutées et résultats réels

| Commande | Résultat |
|---|---|
| `uv lock` puis `uv sync --locked` | `pydantic-settings` 2.15.0 et `python-dotenv` 1.2.4 ajoutés ; 39 paquets verrouillés |
| `uv lock --check` | « Resolved 39 packages », code 0 |
| `uv run ruff check .` / `uv run ruff format --check .` | All checks passed / 28 files already formatted |
| `uv run mypy` | Success: no issues found in 27 source files |
| `docker compose --profile test up -d db-test` | `db-test` « healthy » ; `Mounts: []`, `tmpfs` sur `/var/lib/postgresql` |
| `uv run --env-file ../.env.example pytest` | **143 passed** avant la vérification ciblée, **148 passed** après (unitaires, API et 5 tests d'intégration contre la base de test) |
| `pytest -m integration` sans `TEST_DATABASE_URL` | Échec explicite, avec la marche à suivre (jamais ignoré) |
| `docker compose up -d --build backend` puis `curl` | `live` 200, `ready` 200 `{"status":"ok","database":"ok"}` ; route inconnue : 404 `application/problem+json` ; `/docs` racine : 404 ; aucun en-tête `server` ; `X-Request-ID`, `Cache-Control: no-store` |
| `docker compose stop db`, `curl …/ready`, `start db` | 503 `SERVICE_UNAVAILABLE` avec `Retry-After: 5` ; `live` reste à 200 ; `ready` revient à 200 après la relance |
| `docker compose logs backend` | Lignes JSON avec `request_id`, sans chaîne de requête ; démarrage et arrêt journalisés |
| uvicorn réel (script dans le répertoire temporaire, port 8003) avec une route qui lève une exception | Réponse 500 avec `X-Request-ID`, sans `server` ; une seule ligne `unhandled_exception`, aucun doublon d'uvicorn, aucune valeur secrète. Serveur arrêté, port libéré |
| `python3 -I .claude/tests/test_hooks.py` | 0 échec (après isolation du cas Ruff) |
| Contrôles de la documentation (identifiants, liens, tableaux) | OK |
| Recherche de motifs de secrets dans les fichiers modifiés | Aucun hors valeurs factices et tests |

## Vérification finale

**Vérification ciblée des correctifs** (agent `security-auditor`, essais sous uvicorn réel) : E1, E2, M3, F4 à F8, `WWW-Authenticate` et D-08 corrigés ; deux points partiels ; aucun nouveau défaut élevé. Suites données le 2026-10-14 :

| Constat | Traitement |
|---|---|
| Partiel : le schéma `ProblemDetails` du 422 et du 503 était documenté sous `application/json` | Référence au schéma placée sous `application/problem+json` ; tests renforcés |
| Partiel : une erreur de base en 503 était journalisée en `WARNING`, sans méthode ni chemin | `ERROR` pour tout 5xx, avec méthode et chemin ; test |
| Moyen : `alembic/env.py` analysait `DATABASE_URL` sans protection | Fonction commune `parse_database_url` ; erreur à message fixe (vérifié avec deux URL piégées) |
| Moyen : le formateur JSON écrivait encore la trace complète d'un journal tiers (`exc_info`) | Traces résumées partout (types et pile, jamais le message) ; test |
| Faible : `APP_ENV` avait une valeur par défaut dans Compose | Obligatoire (`${APP_ENV:?}`) |
| Faible : paires clé-valeur non masquées ; UUID et dates illisibles | Paires traitées comme des entrées ; UUID, dates et énumérations lisibles ; `Decimal` reste masqué (prix, D-12) ; tests |
| Faible : mot de passe contenant `@` sans port accepté (fin du mot de passe dans l'hôte) | Refusé avec le message fixe ; test |
| Faible : origines `http://` et `DEBUG` acceptés en `staging` et `demo` | Ajouté à Q-102 |
| Faible : message d'un validateur personnalisé qui transforme la saisie ; clés envoyées reprises dans `field` ; clés de données dans `validation_errors.loc` des journaux | Règle de rédaction des validateurs (`error-handling.md` §3) ; risque résiduel accepté et noté |
| Faible : `Vary: Origin` absent de certaines réponses 500 en mode `*` | Négligeable (`Cache-Control: no-store`) ; noté |
| Info : télémétrie OpenTelemetry embarquée dans FastAPI 0.143, inactive | Noté : ne jamais configurer de fournisseur sans revue (les exceptions y seraient exportées avec leur message) |

Après ces suites :
- Ruff et mypy OK ;
- **148 tests réussis**, dont 5 d'intégration ;
- conteneur reconstruit : `live` et `ready` à 200, 404 au format Problem Details, aucun en-tête `server`.

## Critères de sortie

| Critère (roadmap §5) | État |
|---|---|
| Périmètre implémenté et cohérent | Oui : tous les éléments de la consigne, vérifiés en local, par les tests et en conteneur |
| Tests appropriés et résultat connu | Oui : 148 tests, tous réussis, dont 5 contre une vraie base de test |
| Migrations et contraintes cohérentes | Sans objet (aucune table ; Jour 6) |
| Documentation et `.env.example` à jour | Oui |
| Aucun secret ajouté | Oui |
| Défauts critiques corrigés ou signalés | Oui : aucun critique ; constats élevés corrigés |
| Décisions non définies marquées `À VALIDER` | Oui : Q-102 |

## Décisions À VALIDER

| Sujet | Échéance |
|---|---|
| **Q-71** : passer le dépôt GitHub en privé | **Immédiat** |
| **Q-102** : garde-fous de configuration étendus à `staging` et `demo` ; mot de passe d'au moins 12 caractères ; `APP_ENV` obligatoire ; `DEBUG` refusé en production | Avant tout déploiement (Audit D) |
| mypy comme vérificateur de types | Jour 7 (CI) |
| D-15 : UUIDv7 généré par l'application | Jour 6 |
| Décisions du Jour 3, dont **Q-82** (Trade) | Voir `day-03.md` |

## Risques et limites

- **`/api/v1/health/ready` est public** : chaque appel occupe une connexion du pool pendant au plus 3 s. Limitation de débit au Jour 8 ; restriction au réseau interne par le reverse proxy à prévoir (Audit D).
- **`X-Request-ID` fourni par le client** : un client peut réutiliser l'identifiant d'une autre requête et brouiller la corrélation des journaux (choix retenu, `api-conventions.md` §11).
- **Pas encore de limite de taille de corps ni de limitation de débit** (`api-conventions.md` §14, Jour 8).
- **Compose connecte le backend avec le superutilisateur PostgreSQL** : les deux rôles (migrations, application) sont prévus au Jour 6.
- **Journaux** : les chemins sont journalisés ; aucune route ne doit porter de jeton dans son chemin (règle à conserver). Les cadres de pile des erreurs 500 reprennent des lignes de code, jamais des valeurs.
- **Images épinglées par étiquette, pas par condensat** (Jour 7) ; pas de TLS exigé vers la base en production (Audit D).
- **Télémétrie de FastAPI** (OpenTelemetry, inactive) : ne jamais configurer de fournisseur sans revue de sécurité.

## Préparation du Jour 6 (non exécuté)

Jour 6 — PostgreSQL, SQLAlchemy et Alembic : base déclarative avec la convention de nommage (`indexes-and-constraints.md` §1), fabrique de sessions, configuration d'Alembic et découverte des modèles, base de test isolée (transaction externe et points de sauvegarde par test, `testing-strategy.md` §4), vérification de la montée de version, de l'annulation et des erreurs de connexion. Pas de tables métier prématurées.

Prérequis et décisions :
- noms des rôles PostgreSQL (migrations et application, `indexes-and-constraints.md` §6.1) ;
- D-15 (UUIDv7 généré par l'application) ;
- Q-08 (précision des montants) avant la première migration monétaire : sans effet au Jour 6 s'il n'y a pas de table monétaire.

**Le Jour 6 ne sera pas lancé sans ta validation explicite.**
