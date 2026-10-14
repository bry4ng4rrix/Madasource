# Jour 6 — PostgreSQL, SQLAlchemy et Alembic

Date : 2026-10-14 · Statut : **TERMINÉ AVEC RÉSERVES**. Réserves :
- **Q-103** : délais de la base, droits de `PUBLIC` sur la base, propriétaire non superutilisateur en local, à valider ;
- le dépôt GitHub est toujours public (Q-71, hérité).

## Objectif du jour

Consigne de `roadmap_backend_fastapi.md`, Jour 6 :
- finaliser SQLAlchemy 2.x async : base déclarative, fabrique et gestion des sessions ;
- configurer Alembic et la découverte des modèles ;
- configurer une base de test isolée ;
- n'ajouter que les migrations réellement nécessaires ;
- vérifier la montée vers la tête, l'annulation en cas d'exception, la fermeture des sessions, les erreurs de connexion et les commandes Alembic ;
- documenter `upgrade`, la création d'une migration et le retour arrière prudent ;
- ne créer aucune table métier.

## Décisions prises avec l'utilisateur (2026-10-14)

| Sujet | Choix |
|---|---|
| Rôles PostgreSQL | **Deux rôles dès maintenant** : le propriétaire du schéma pour Alembic (`MIGRATION_DATABASE_URL`) ; `madasource_app` pour l'application (`DATABASE_URL`), sans droit sur le schéma |
| Identifiants (D-15) | **UUIDv7 générés par l'application** (`uuid.uuid7()`) |

## Prérequis vérifiés

- Jours 4 et 5 livrés ; 148 tests au vert au départ ; bases de développement et de test disponibles dans Compose.
- La base de développement existante (volume `madasource_pgdata`) n'a jamais été réinitialisée : le rôle applicatif y a été créé par le script idempotent, puis les migrations y ont été appliquées.

## Fichiers

**Créés** :

| Fichier | Contenu |
|---|---|
| `backend/app/db/base.py` | `Base` (convention de nommage, `timestamptz`, `uuid`), `new_id()` (UUIDv7), `UUIDPrimaryKeyMixin` |
| `backend/app/db/registry.py` | Découverte des modèles `app/modules/*/models.py` ; aucun au Jour 6 |
| `backend/app/db/roles.py` | Rôle applicatif `madasource_app` et règles des deux rôles |
| `backend/alembic/versions/…_03d1bd152b99_schema_privileges_baseline.py` | Retire au rôle `PUBLIC` l'usage du schéma `public`, l'accorde au seul `madasource_app` ; vérifie que le rôle existe ; réversible |
| `backend/alembic/versions/…_179c8cc724de_verify_schema_privileges.py` | Vérifie que les droits ont réellement pris effet ; lecture seule |
| `infrastructure/postgres/10-create-app-role.sh` | Création idempotente du rôle applicatif (mot de passe lu par `\getenv`) |
| `backend/tests/unit/db/test_base.py` | Convention de nommage, types, UUIDv7, politique du schéma (pas de `float`, `Numeric` avec précision, `timestamptz`), longueur et unicité des noms |
| `backend/tests/integration/test_migrations.py` | Tête unique, base à la tête, `alembic check`, réversibilité, SQL hors ligne, échec du contrôle si `PUBLIC` garde des droits |
| `backend/tests/integration/test_privileges.py` | Rôle applicatif réel : pas de DDL, pas d'accès à `alembic_version`, droits du schéma, 503 sur mot de passe refusé |
| `backend/tests/integration/test_session_isolation.py` | Validation, annulation, une session par requête, transaction externe inchangée, délais de session |
| `docs/backend/daily-reports/day-06.md` | Ce rapport |

**Modifiés** :
- **`backend/app/db/session.py`** : `lock_timeout` et `idle_in_transaction_session_timeout` ; écouteur `do_connect` qui convertit les erreurs réseau d'ouverture de connexion en `DatabaseUnavailableError` (503).
- **`backend/app/core/`** :
  - `config.py` : deux délais ;
  - `exceptions.py` : `DEFAULT_RETRY_AFTER_SECONDS` ;
  - `errors.py` : SQLSTATE 28, 3D, 53 et 57P en 503, avec `Retry-After` ;
  - `api/v1/endpoints/health.py` : constante partagée.
- **`backend/alembic/env.py`** : `MIGRATION_DATABASE_URL` ou URL passée par les tests ; métadonnées découvertes ; comparaison des types ; journalisation conservée ; verrou consultatif ; `lock_timeout` de 10 s.
- **`backend/alembic.ini`** : noms de fichiers datés, en UTC.
- **`backend/pyproject.toml`** : mypy sur les migrations ; asyncpg sans types déclaré.
- **`backend/tests/conftest.py`, `support.py`** : migration de la base de test une fois par session ; transaction externe ; points de sauvegarde ; client HTTP asynchrone en mémoire ; `run_alembic` limité à la base de test.
- **`backend/tests/api/test_errors.py`** : erreurs de connexion simulées (refus, toutes les adresses en échec, nom introuvable, délai) et SQLSTATE supplémentaires.
- **`docker-compose.yml`, `.env.example`** :
  - rôle applicatif sur `db` et `db-test` ;
  - `MIGRATION_DATABASE_URL`, `TEST_MIGRATION_DATABASE_URL` ;
  - le backend se connecte avec `madasource_app` ;
  - montage du dossier `infrastructure/postgres`.
- **`backend/README.md`, `README.md`** : section « Migrations », rôles, variables, structure.
- **`docs/backend/`** :
  - `architecture.md` : D-08, D-09, D-15 ;
  - `indexes-and-constraints.md` : §1, §6.1, §7 ;
  - `security-design.md` : §19 ;
  - `testing-strategy.md` : §4 ;
  - `error-handling.md` : §6 ;
  - `risks-and-open-questions.md` : Q-103.
- **`.claude/skills/database-migrations/SKILL.md`** : commandes et règle des droits par table.

## Démarche et revues

| Étape | Résultat |
|---|---|
| Sonde préalable | Une base injoignable donnait 500 au lieu de 503 : asyncpg lève des erreurs du système à l'ouverture d'une connexion, que SQLAlchemy ne traduit pas |
| Revue de code (skill `code-review-madasource`) | Non prêt, 1 bloquant. Une panne DNS ou l'échec de toutes les adresses de `localhost` donnaient encore 500, car seules `ConnectionError` et `TimeoutError` étaient traduites. Importants : journalisation d'Alembic qui polluait les tests ; `run_alembic` dépendant de la variable du poste ; nouveaux SQLSTATE non testés. Tous corrigés |
| Relecture base de données (agent `database-reviewer`) | 0 bloquant, 5 importants, 7 mineurs. Principaux : migration sans effet si exécutée sans droits (I1) ; test d'isolation qui ne pouvait pas échouer (I3) ; `PUBLIC` garde `CONNECT` et `TEMP` (I4, à valider) ; pas de `lock_timeout` (I5) ; noms tronqués en silence au-delà de 63 caractères ; mot de passe dans les arguments de `psql` ; pas de verrou entre migrations simultanées. Corrigés ou ouverts en Q-103 |
| Incident | Après modification du script de rôle, le conteneur exécutait encore l'ancienne version : un fichier monté seul reste lié à son ancien contenu quand il est remplacé. Le dossier est désormais monté ; les conteneurs `db` et `db-test` ont été recréés, le volume de développement conservé (version Alembic `179c8cc724de` intacte) |
| Vérification ciblée des correctifs (agent `database-reviewer`) | Voir « Vérification finale » |

Règle respectée : la première révision avait déjà été appliquée à la base de développement. Elle n'a pas été modifiée ; le contrôle des droits fait l'objet d'une seconde révision.

## Commandes exécutées et résultats réels

| Commande | Résultat |
|---|---|
| Sonde (route avec `DbSession`, base injoignable) avant correction | 500 pour une connexion refusée, un délai dépassé ou un mot de passe refusé |
| Même sonde après correction (5 cas : `127.0.0.1:9`, `localhost:9`, `db.invalid`, adresse qui dépasse le délai, mot de passe refusé) | **503 `SERVICE_UNAVAILABLE`, `Retry-After: 5`** dans les 5 cas |
| `docker compose --profile test up -d --force-recreate db-test` | Script exécuté à l'initialisation ; `madasource_app` : non superutilisateur, sans `CREATEDB` ni `CREATEROLE`, `NOINHERIT` |
| `docker compose exec db sh …/10-create-app-role.sh` (deux fois, base existante) | Réussi deux fois : idempotent ; aucune réinitialisation |
| Alembic sur la base de test : `heads`, `upgrade head`, `current`, `check`, `downgrade -1`, `upgrade head`, `upgrade head --sql` | Une tête ; montée réussie ; « No new upgrade operations detected. » ; retour arrière d'une révision puis remontée réussis ; SQL relu (`REVOKE`, `GRANT`) |
| Alembic sur la base de développement : `upgrade head`, `current` | `179c8cc724de (head)` |
| `uv lock --check` ; `ruff check` ; `ruff format --check` ; `mypy` | 39 paquets ; OK ; 37 fichiers formatés ; 36 fichiers sans erreur |
| `uv run --env-file ../.env.example pytest -q`, lancé deux fois | **183 passed** les deux fois, sans état résiduel ; **184 passed** après la vérification ciblée |
| `pytest -s tests/integration`, recherche de « Logging error » | 0 occurrence |
| `docker compose up -d --build backend`, `curl …/ready`, `pg_stat_activity` | `ready` 200 ; le backend est connecté en tant que `madasource_app` |
| Contrôles de la documentation (identifiants, liens, tableaux) | OK |

## Vérification finale

**Vérification ciblée des correctifs** (agent `database-reviewer`, avec essais de mutation) : les 8 correctifs sont confirmés. Retirer l'écouteur `do_connect` fait échouer 5 tests, et passer en `control_fully` fait échouer le test d'isolation : les tests détectent bien les régressions. Aucun nouveau bloquant. Suites données le 2026-10-14 :

| Constat | Traitement |
|---|---|
| Important : la cause d'un échec de connexion n'était plus journalisée (refus, nom introuvable, délai, TLS indiscernables) | Journal `database_connect_failed` avec types et `errno`, jamais le message (qui cite l'hôte) ; test |
| Mineur : le `lock_timeout` des migrations s'appliquait à l'attente du verrou consultatif (une seconde migration échouait au lieu d'attendre) | `SET LOCAL lock_timeout = 0`, verrou, puis `SET LOCAL lock_timeout = '10s'` |
| Mineur : verrou et délai absents du SQL hors ligne | Émis aussi en mode hors ligne (vérifié dans `upgrade head --sql`) |
| Mineur : `log_statement` non désactivé dans le script de rôle | `SET log_statement = 'none'` ; avertissement : tout script déposé dans `infrastructure/postgres` serait exécuté à l'initialisation |
| Mineur : réponses 503 et 500 non vérifiées contre la fuite de message | Assertions ajoutées |
| Mineur : clé du verrou consultatif sans registre | Registre dans `indexes-and-constraints.md` §7 |
| Mineur : transaction externe des tests fermée après 60 s d'inactivité | Documenté (`testing-strategy.md` §4) |
| Mineur : `env.py` sans garde-fou propre contre la base de développement | Accepté : le CLI vise la base désignée par `MIGRATION_DATABASE_URL` ; les tests passent toujours par `run_alembic`, limité à la base de test |
| À décider : erreur TLS de configuration en 503 réessayable | Ajouté à Q-103 (e) |

Après ces suites :
- Ruff et mypy OK ;
- **184 tests réussis** ;
- script de rôle relancé sur les deux bases ;
- backend reconstruit : `ready` à 200 ;
- base de développement : `179c8cc724de (head)`, `alembic check` sans écart.

## Critères de sortie

| Critère (roadmap §5) | État |
|---|---|
| Périmètre implémenté et cohérent | Oui : base déclarative, sessions, Alembic, découverte des modèles, base de test isolée, deux migrations nécessaires (droits), aucune table métier |
| Tests appropriés et résultat connu | Oui : 184 tests, dont migrations, droits réels, isolation, erreurs de connexion |
| Migrations et contraintes cohérentes | Oui : une tête, `alembic check` sans écart, réversibilité testée, SQL relu |
| Documentation et `.env.example` à jour | Oui |
| Aucun secret ajouté | Oui : valeurs factices seulement ; mot de passe du rôle jamais en argument ni dans les journaux |
| Défauts critiques corrigés ou signalés | Oui : bloquant corrigé ; points à valider en Q-103 |
| Décisions non définies marquées `À VALIDER` | Oui : Q-103 |

## Décisions À VALIDER

| Sujet | Échéance |
|---|---|
| **Q-71** : passer le dépôt GitHub en privé | **Immédiat** |
| **Q-103** : délais (`lock_timeout` 5 s, 10 s pour les migrations, transaction inactive 60 s) ; retrait de `CONNECT` et `TEMPORARY` au rôle `PUBLIC` ; propriétaire non superutilisateur en local et en test ; droits des rôles de supervision (Audit D) | Avant les premières tables (Jour 9) |
| Q-102 (garde-fous hors production), mypy, Q-82 (Trade) | Voir les rapports précédents |

## Risques et limites

- **Propriétaire superutilisateur en local et en test** : les tests ne reproduisent pas une migration exécutée par un propriétaire non superutilisateur. La révision de contrôle fait échouer une telle migration si elle reste sans effet (Q-103).
- **Tables temporaires** : le rôle applicatif peut en créer, car `PUBLIC` garde `TEMPORARY`. Les tests d'isolation s'en servent faute de table métier (Q-103).
- **Tests** : une seule connexion par test, donc pas de requêtes simultanées dans un même test. Les tests de migration modifient la base partagée : pas d'exécution parallèle.
- **Montage du script** : le script de rôle n'est exécuté automatiquement qu'à l'initialisation d'une base vide. Pour une base existante, il faut le relancer à la main (README).
- **Production** : le rôle propriétaire non superutilisateur et la création du rôle applicatif relèvent de l'exploitation (Audit D).

## Préparation du Jour 7 (non exécuté)

Jour 7 — Qualité et intégration continue : CI GitHub Actions (lint, format, types, tests unitaires, API et d'intégration avec un PostgreSQL 18 éphémère, migrations, build de l'image), test d'architecture (D-07 : imports entre modules, clés étrangères vers les niveaux inférieurs), analyse de secrets, épinglage des images par condensat.

Prérequis et décisions :
- confirmer **mypy** comme vérificateur de types ;
- choisir l'outil d'analyse de secrets (à justifier) ;
- la CI s'exécutera sur GitHub, dont le dépôt est **public** (Q-71) : les journaux de CI y seraient visibles par tous ;
- aucune exécution de CI sans ton accord (premier push d'un workflow).

**Le Jour 7 ne sera pas lancé sans ta validation explicite.**
