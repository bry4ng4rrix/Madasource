# Stratégie de tests — backend MadaSource

Jour 2 · 2026-10-12 · Statut : proposition à valider. Révisée après les revues `backend-architect` et `security-auditor` du Jour 2.

Références :
- règles permanentes : CLAUDE.md, `.claude/rules/tests.md` ;
- procédure : skill `pytest-workflow` ;
- agent : `test-engineer`.

## 1. Principes

1. Toute fonctionnalité a des tests adaptés. Un jour n'est terminé que si leur résultat est connu (roadmap, section 5).
2. On ne rend jamais une suite verte en affaiblissant une assertion, en ajoutant `skip` ou `xfail`, ou en supprimant un test (RJ 7).
3. Les tests s'exécutent contre une **base PostgreSQL de test isolée**, jamais la base de développement partagée ni la production (RJ 6, RJ 7).
4. Les règles critiques sont testées au plus près de leur logique (tests unitaires) **et** à travers l'API (tests de bout en bout des permissions).
5. Aucune dépendance au temps réel, au réseau externe ni à l'ordre d'exécution des tests.

## 2. Niveaux de tests

| Niveau | Dossier | Ce qui est testé | Base | HTTP |
|---|---|---|---|---|
| Unitaire | `backend/tests/unit/<module>/` | Logique pure : calcul de prix (Decimal), machines d'état, score de matching, formatage des références, évaluation des permissions, Money et Quantity | Non | Non |
| Intégration | `backend/tests/integration/<module>/` | Services et repositories : contraintes, transactions, verrous, concurrence, ports | PostgreSQL de test | Non |
| API | `backend/tests/api/<module>/` | Endpoints : statuts HTTP, schémas de réponse, permissions, erreurs, non-exposition | PostgreSQL de test | Client ASGI en mémoire |
| Migrations | `backend/tests/integration/migrations/` | Montée complète, absence d'écart entre modèles et migrations, réversibilité de la dernière révision | PostgreSQL de test | Non |
| Contrat OpenAPI | `backend/tests/api/` | Absence de champ interdit dans les schémas publics, acheteur et exportateur ; détection des changements cassants (facultatif) | Non | Non |
| Parcours complet | `backend/tests/e2e/` (dossier ajouté à la structure RJ, D-03) | Parcours Audit A pour Vanilla, Cloves et Cocoa | PostgreSQL de test | Client ASGI |
| Sécurité | Intégré aux niveaux API et E2E, renforcé à l'Audit B | Accès horizontaux, élévation de privilèges, fuites, jetons | PostgreSQL de test | Client ASGI |
| Performance | Hors de la suite courante (Audit C) | Volumétrie synthétique en local | Dédiée | — |

Répartition visée : beaucoup de tests unitaires sur les règles, une couverture systématique des permissions au niveau API, peu de parcours complets mais tous critiques.

## 3. Outils

Dépendances de développement à justifier et épingler au Jour 4.

| Besoin | Outil proposé | Justification |
|---|---|---|
| Lanceur | `pytest` | Imposé par la stack (RJ section 1) |
| Tests asynchrones | **Plugin pytest d'AnyIO** (backend asyncio seul), retenu au Jour 5 | AnyIO est déjà une dépendance de Starlette et FastAPI : pas de paquet supplémentaire |
| Client HTTP de test | `httpx2` (Jour 4) : Starlette 1.7 rend `httpx` obsolète pour son `TestClient`, voir `backend/README.md`. `TestClient`, ou `AsyncClient` et transport ASGI | Appelle l'application en mémoire, sans serveur. Le transport ASGI de httpx **n'exécute pas** le cycle de démarrage et d'arrêt (lifespan) : les fixtures le déclenchent explicitement. |
| Couverture | `pytest-cov` 7.1.0, retenu au Jour 7 | Mesure des lignes et des branches, seuil bloquant (section 10) |
| Données de test | Fonctions de fabrication écrites dans le projet (pas de bibliothèque) | Pas de dépendance ; données explicites |
| Temps | Horloge injectable (D-13), sans bibliothèque de gel du temps | Dates contrôlées sans modifier l'horloge du système |

## 4. Base de données de test

| Règle | Statut |
|---|---|
| Base dédiée, dont le nom se termine par `_test` (par exemple `madasource_test`), servie par un **PostgreSQL éphémère** : un conteneur de test dont les données vivent en mémoire (tmpfs) et repartent vides à chaque démarrage. La CI démarre le même service Compose, avec les valeurs factices de `.env.example`. Aucune base persistante n'est donc jamais supprimée ni réinitialisée par les tests (CLAUDE.md). Même version majeure de PostgreSQL qu'en production. | **Implémenté** en local (Jour 5) ; en CI, job `tests` écrit au Jour 7, rejoué en local ; première exécution sur GitHub le 2026-10-14 (commit `98dceb2`, version intermédiaire du workflow) : quatre jobs réussis. La version corrigée (commit `670bff6`, run `38561360442`) a échoué à `make migrations-check` : garde-fou `_test` invalide, corrigé le 2026-10-16 (rapport du Jour 7, addendum), pas encore réexécuté sur GitHub |
| **Garde-fou** : la configuration de test refuse de démarrer si l'environnement n'est pas `test` ou si le nom de la base ne se termine pas par `_test`. Aucun test ne peut toucher la base de développement. La cible de connexion (hôte, port, utilisateur, base) ne vient que de l'URL : `parse_database_url` n'admet que les paramètres de requête d'une liste blanche (`ssl`, `prepared_statement_cache_size`), car asyncpg appliquerait `?database=…`, `?host=…` ou `?dsn=…` ; une URL de test précise l'hôte et le port, sinon asyncpg les prendrait dans `PGHOST` ou `PGPORT` (Q-105). | **Implémenté au Jour 5** : service Compose `db-test` (profil `test`, `tmpfs`, port 5434), `TEST_DATABASE_URL`, contrôle dans `Settings`. Liste blanche et hôte et port explicites : 2026-10-16 (addendum du Jour 7, Q-105). `make migrations-check` applique la même règle (`has_explicit_test_target`, partagée avec `tests/support.py`) par `scripts/require_test_database.py` |
| Schéma créé une fois par session de tests par `alembic upgrade head` sur cette base vide, ce qui teste aussi les migrations. Jamais par `create_all`. Une réinitialisation d'une base de test persistante, si elle devenait nécessaire, serait une exception explicite à faire valider par l'utilisateur. | **Implémenté au Jour 6** (`migrated_test_database`, avec le propriétaire du schéma ; l'application teste avec `madasource_app`) |
| **Isolation par test** : chaque test s'exécute dans une transaction externe annulée à la fin. La session applicative y travaille par points de sauvegarde (mode « rejoindre une transaction externe » de SQLAlchemy 2.x, `join_transaction_mode="create_savepoint"`). Les commits des services n'en sortent jamais. | **Implémenté au Jour 6** (`db_connection`, `db_session`, `api` : la vraie dépendance de session est conservée, seule sa fabrique rejoint la transaction externe ; l'identifiant de la transaction externe ne change jamais pendant un test, ce qui est vérifié). Limites : une seule connexion par test, donc pas de requêtes simultanées dans un même test ; les tests de migration modifient la base partagée par la session, donc pas d'exécution parallèle (pytest-xdist) ; la transaction externe est fermée par le serveur après 60 s d'inactivité (`idle_in_transaction_session_timeout`) : une pause plus longue au débogueur fait échouer le test |
| **Tests de concurrence** (marqueur `concurrency`) : ils exigent de vraies transactions parallèles validées. Ils tournent sans transaction externe, sur des données propres à chaque test, **sans nettoyage**, dans une **base éphémère distincte** (ou un job de CI séparé). Ainsi, leurs données validées (compteurs, audit) ne rendent pas les autres tests dépendants de l'ordre d'exécution. Les droits restreints du rôle applicatif sur la table d'audit (pas de `DELETE`, [security-design.md](security-design.md) §18) sont respectés. | Proposé (C33, revue finale) |
| **Écritures de sécurité** (D-29). En production, elles s'exécutent après l'annulation de la transaction principale, dans une nouvelle transaction. En test, cette transaction est un point de sauvegarde distinct sur la connexion de test, ouvert **après** l'annulation de celui de la requête : l'écriture reste visible des assertions et disparaît à la fin du test. Un point de sauvegarde imbriqué dans celui de la requête serait annulé avec elle ; une session ouverte à part sur le moteur ne verrait pas les données du test. | Proposé (revue finale) |

## 5. Organisation et fixtures

Marqueurs : `unit`, `integration`, `api`, `concurrency`, `e2e`, `slow`. La suite rapide (`unit`) tourne sans base.

Fixtures communes (`backend/tests/conftest.py`), proposées :

| Fixture | Rôle |
|---|---|
| `settings`, `db_settings` | Configuration explicite, sans dépendre de l'environnement (`tests/support.py`, `make_settings`) ; `db_settings` vise la base de test, avec le garde-fou de la section 4 |
| `db_engine`, `db_session` | Moteur et session isolée par test |
| `app`, `client` | Application construite par la factory, client HTTP en mémoire |
| `clock` | Horloge contrôlable |
| Acteurs : `buyer_a`, `buyer_b`, `exporter_a`, `exporter_b`, `admin` | Utilisateurs et organisations prêts à l'emploi : **deux organisations par type**, pour les tests d'accès croisé |
| Fabriques `make_<entité>(...)` | Création d'objets valides avec des valeurs par défaut factices et explicites |

## 6. Tests obligatoires

### 6.1 Pour chaque endpoint privé (skill `secure-api`)

| Cas | Attendu |
|---|---|
| Sans jeton | 401 `AUTHENTICATION_REQUIRED` |
| Jeton invalide, expiré ou révoqué | 401 `INVALID_TOKEN` |
| Rôle sans la permission | 403 `PERMISSION_DENIED` |
| Ressource d'une autre organisation (`buyer_b` sur une RFQ de `buyer_a`) | 404 `RESOURCE_NOT_FOUND`, réponse identique à un identifiant inexistant |
| Bon rôle, bonne organisation | Succès et schéma conforme |
| Champ réservé au serveur envoyé par le client (`status`, `organization_id`, marge…) | 422 |
| Champs sensibles dans la réponse | Absents (section 7) |

### 6.2 Machines d'état

Tests pilotés par une table, **exhaustifs** (les ensembles d'états sont petits) :
- chaque transition permise réussit, produit l'événement attendu (audit, TradeEvent) et respecte l'acteur autorisé ;
- **toute** autre paire (état de départ, état d'arrivée) est refusée avec 409 `INVALID_STATE_TRANSITION`.

Machines concernées : RFQ, destinataire de RFQ, quotation, négociation, Trade, Payment Record, expédition, vérification, échantillon, litige, exception, produit, statut de compte d'organisation (D-28) ([workflows.md](workflows.md)).

### 6.3 Règles critiques

| Domaine | Tests |
|---|---|
| Montants | Calculs exacts en Decimal ; arrondis selon la règle retenue (Q-08) ; refus de combiner deux devises ; aucun `float` |
| Validité | Quotation valide une seconde avant `expires_at` et expirée à `expires_at` (horloge contrôlée, UTC) ; une quotation expirée n'est ni présentée comme active ni acceptable (BR-QUO-04, BR-QUO-05) |
| Matching | Même entrée → même résultat ; correspondance parfaite, partielle, impossible ; donnée manquante jamais réputée satisfaite ; pondérations versionnées (RJ 22) |
| Identifiants lisibles | Unicité sous concurrence, format, passage d'année |
| Acceptation et Trade | Deux acceptations simultanées → un seul Trade ; rejouer l'acceptation → même Trade ; échec en cours de création → aucune écriture (BR-TRD-01 à BR-TRD-03) |
| Termes figés | Modifier la quotation ou un taux de change après acceptation ne change pas le Trade (BR-TRD-05) |
| Audit | Chaque action sensible écrit un événement ; aucun chemin de code ne modifie ni ne supprime un événement (BR-AUD-01, BR-AUD-02) |
| Feature flags | Module désactivé : routes absentes. Catégorie désactivée : création refusée (`CATEGORY_DISABLED`) et masquage public (D-17) |
| Configuration | La production refuse de démarrer en debug, avec un secret par défaut ou avec `DEMO_MODE` (D-11, D-18) |
| Erreurs | Catalogue de [error-handling.md](error-handling.md) §10 |
| Verrous et concurrence | Deux quotations simultanées sur la même RFQ : aucune erreur d'interblocage (`FOR NO KEY UPDATE`, parent verrouillé avant l'insertion, C4). L'état revérifié après verrouillage est l'état en base, même si l'objet était déjà chargé (`populate_existing`, C3). |
| Acceptation | Chemin unique ; version transmise différente de la version courante → 409 `OFFER_VERSION_MISMATCH` ; rejeu → même réponse 200 (D-33, S-43) |
| Ports | Comportement par défaut : P-01 refuse un contexte non branché ; P-03 sans implémentation laisse la RFQ en Submitted. Les implémentations des modules actifs sont branchées (C9). |
| Écritures de sécurité | Rejeu d'un jeton de rafraîchissement → 401 **et** session révoquée en base, malgré l'annulation de la transaction de la requête (D-29) |
| Outbox | Aucun email n'est envoyé si la transaction est annulée ; l'envoi a lieu après validation (D-20) |
| DTO inter-modules | Une fonction publique d'un module ne renvoie jamais d'objet ORM (C15) |

### 6.4 Sécurité

Les tests demandés par la relecture de sécurité du Jour 2 sont listés dans [security-design.md](security-design.md#21-tests-de-sécurité) §21 : non-déduction de la marge par audience, isolement des exportateurs concurrents, audience des documents et des versions, coordonnées bancaires, séparation des tâches, mode DEMO, notifications. Ils s'ajoutent à la matrice de la section 6.1.

## 7. Non-exposition des données sensibles

Deux garde-fous complémentaires, contre le risque R-01 et les fuites de données privées :

1. **Assertion de réponse** : une fonction d'aide de test parcourt récursivement le JSON d'une réponse et échoue si une clé interdite **à l'audience de la réponse** apparaît. Il y a **une liste par audience**, alignée sur les classes de base du point 2, car une même clé peut être légitime pour une audience et interdite pour une autre :
   - `supplier_unit_price` est permis à `exporter_owner` pour sa propre quotation, interdit à `buyer` et `public` ;
   - les coordonnées bancaires sont permises au propriétaire (masquées), interdites ailleurs ;
   - `commission` n'est permise qu'à son payeur (S-41).

   Clés interdites à toutes les audiences non admin : `margin`, `internal_notes`, `verification_notes`, `password_hash`, `storage_key`. Les listes viennent de la classification des données (Jour 3).
2. **Contrôle statique des schémas** : un test parcourt tous les schémas de réponse et vérifie, **par leur classe de base d'audience** (`PublicSchema`, `BuyerSchema`, `ExporterOwnerSchema`, `ExporterRecipientSchema`, `AdminSchema`, `AdminFinanceSchema`), qu'aucun ne déclare de propriété interdite à son audience. Le contrôle ne repose pas sur un suffixe de nom, qui laisserait passer `ProductPublic` ou un schéma admin sans droit financier (C27). Il ne demande aucune donnée et protège dès qu'un schéma change.
3. **Pas d'union de schémas** : un test vérifie qu'aucun endpoint ne déclare un `response_model` en union de schémas d'audiences différentes, et qu'un endpoint multi-audiences sert exactement le schéma choisi par la politique (D-32, C16).
4. **Ensemble exact des clés** : pour chaque projection, les tests API comparent l'ensemble des clés renvoyées à la liste blanche attendue, et non seulement à une liste d'interdits (S-37).

## 8. Migrations

| Test | Fréquence |
|---|---|
| `alembic upgrade head` sur une base vide | En local, à la première exécution de la suite après le démarrage de `db-test` (section 4). En CI, par `make migrations-check`, avant la suite, qui trouve alors la base à jour |
| Montée par la commande `alembic` elle-même, puis aucun écart (`make migrations-check`, base de test seulement, garde-fou `_test`) | CI, avant les tests (Jour 7) ; en local à la demande |
| Aucun écart entre modèles et migrations (`alembic check`) | Chaque exécution de la suite (`test_migrations.py`), donc en CI |
| Dernière révision : `downgrade -1` puis `upgrade head`, sur la base de test uniquement | Chaque exécution de la suite, donc en CI |
| Migration de données : test dédié avec un jeu de données de départ | Au cas par cas |

## 9. Commandes

Fixées au Jour 7 : cibles de `backend/Makefile`, décrites dans `backend/README.md` (source de vérité). En résumé, depuis `backend/` :

| Usage | Commande |
|---|---|
| Contrôles statiques et tests sans base | `make check` |
| Suite complète avec couverture (base de test démarrée) | `make test ENV_FILE=../.env` |
| Un module | `uv run --env-file ../.env pytest tests -k rfqs -q` |

La CI (`.github/workflows/ci.yml`) exécute les mêmes cibles : lint, format, vérification de types, frontières de l'architecture, suite complète avec PostgreSQL éphémère et couverture, contrôle des migrations, build Docker, recherche de secrets. Aucun contrôle n'est facultatif : un job en échec fait échouer la CI. Mais tant que la branche `main` n'est pas protégée sur GitHub (statuts requis), cet échec n'empêche ni un push direct ni une fusion (Q-104 f). Le workflow a été exécuté une première fois sur GitHub le 2026-10-14, dans sa version intermédiaire (commit `98dceb2`) : quatre jobs réussis. La version corrigée (commit `670bff6`) a échoué au job `tests` (garde-fou de `migrations-check` invalide) ; correctif du 2026-10-16, rejoué en local, à pousser.

## 10. Couverture

- Mesurée à chaque exécution de `make test`, en local et en CI. Le rapport est affiché dans le journal du job ; il n'est envoyé à aucun service externe.
- Proposition du Jour 2 : bloquer la CI sous 85 % de lignes couvertes sur `app/modules/`.
- **Appliqué au Jour 7, `À VALIDER` (Q-104)** : échec sous **95 %**, lignes et branches, sur tout `app/` et sur `scripts/` (`fail_under` dans `pyproject.toml`). `app/modules/` ne contient encore aucun code : un seuil limité à ce dossier ne mesurerait rien. Mesure au Jour 7 : 99,38 % (2026-10-14), 99,42 % après le correctif du 2026-10-16. Le seuil n'est jamais abaissé pour obtenir une CI verte.
- La couverture est un indicateur, pas un objectif : un test sans assertion utile ne compte pas.

## 11. Données de test

- Entièrement fictives et identifiables : préfixe `test-`, domaine `example.com`, sociétés inventées. Jamais de donnée réelle d'entreprise, de personne ou de prix (`.claude/rules/tests.md`).
- Les jeux de démonstration (DEMO) sont distincts des données de test et marqués comme tels (D-18).

## 12. Hors de la suite automatique en V1

| Sujet | Traitement |
|---|---|
| Fournisseur d'email réel | Adaptateur console en test. Le contrat de l'interface est testé ; pas d'envoi réel. |
| Stockage S3 réel | Adaptateur local en test. Un stockage S3-compatible local (conteneur) peut être ajouté au Jour 29 si le besoin est justifié. |
| Performance et charge | Audit C, données synthétiques, jamais sur la production |
| Interface utilisateur | Hors périmètre (backend uniquement) |
