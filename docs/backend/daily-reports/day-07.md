# Jour 7 — Qualité et intégration continue

Date : 2026-10-14 · Statut : **TERMINÉ AVEC RÉSERVES**. Réserves :
- le workflow GitHub Actions n'a **jamais tourné sur GitHub** : chaque job a été rejoué en local, et la première exécution aura lieu à ton premier push ;
- **Q-104** : seuil de couverture, délai de carence des versions, sous-modules importables entre modules, à valider ;
- le dépôt GitHub est toujours public (Q-71, hérité) : les journaux de CI le seront aussi.

## Objectif du jour

Consigne de `roadmap_backend_fastapi.md`, Jour 7 :
- configurer des commandes reproductibles : Ruff lint et format, vérification de types, Pytest unitaire et intégration, vérification des migrations, build Docker ;
- ajouter GitHub Actions sur push et pull request ;
- faire tourner les tests sur une base isolée, jamais la production ;
- documenter les commandes ;
- ne rien ignorer pour rendre la CI verte.

S'y ajoutent les éléments prévus pour ce jour par les documents des Jours 2 à 6 : test d'architecture (D-05, D-07), recherche de secrets et contrôle « aucun `.env` suivi » (security-design §17), seuil de couverture (testing-strategy §10), épinglage des images par empreinte.

## Décisions prises avec l'utilisateur (2026-10-14)

| Sujet | Choix |
|---|---|
| Vérificateur de types | **mypy** (mode strict, greffon Pydantic) |
| Recherche de secrets | **gitleaks** |
| CI | **J'écris la CI, tu pousses toi-même** : rien n'est poussé ni exécuté sur GitHub par Claude |

## Prérequis vérifiés

- Jours 4 à 6 livrés ; 184 tests au vert au départ ; base de test disponible dans Compose.
- Une partie du travail du jour a été commitée par toi en cours de journée (commit `0961309`) ; le reste est dans l'arbre de travail, non commité.

## Fichiers

| Fichier | Contenu |
|---|---|
| `.github/workflows/ci.yml` (nouveau) | Quatre jobs : `quality`, `tests` (PostgreSQL éphémère), `docker`, `secrets` ; jeton en lecture seule ; actions épinglées par empreinte de commit |
| `backend/Makefile` (nouveau) | Commandes officielles : `install`, `lock-check`, `lint`, `format-check`, `types`, `imports`, `quality`, `test-fast`, `test`, `migrations-check`, `docker-build`, `check` |
| `backend/pyproject.toml`, `backend/uv.lock` | Contrats import-linter `socle` et `modules` ; dépendances de dev `import-linter` 2.15, `grimp` 3.17, `pytest-cov` 7.1.0 ; couverture des branches, seuil 95 % |
| `backend/app/modules/__init__.py` (nouveau) | Paquet conteneur des modules métier, exigé par le contrat `modules` ; aucun module créé à l'avance |
| `backend/tests/architecture/test_boundaries.py` (nouveau) | Niveaux lus dans le contrat `modules` ; interface publique des modules (grimp) ; clés étrangères vers les niveaux inférieurs ; un cas fabriqué par règle |
| `backend/tests/unit/db/test_base.py` | Registre des modèles : paquet de modules absent, découverte d'un modèle, `models.py` cassé |
| `backend/Dockerfile`, `docker-compose.yml` | Images `uv`, `python` et `postgres` épinglées par empreinte (`@sha256:…`) |
| `backend/.dockerignore` | Caches d'import-linter et de grimp exclus du contexte de build |
| `backend/README.md` | Commandes officielles (`make`), section « Intégration continue », dépendances justifiées, structure |
| `README.md` | État au Jour 7, CI |
| `docs/backend/testing-strategy.md` | §3, §4 (base de test en CI), §8, §9 (commandes), §10 (seuil de couverture appliqué, Q-104) |
| `docs/backend/module-boundaries.md` | §4 (proposition pour les dépendances HTTP d'`access_control`), §9 (contrôles implémentés), §10 |
| `docs/backend/architecture.md` | D-05 ; mypy retenu ; import-linter, GitHub Actions, gitleaks |
| `docs/backend/security-design.md` | §17 : gitleaks, contrôle `.env`, garde-fous de la CI |
| `docs/backend/api-conventions.md` | §16 : renvoi vers la proposition pour `access_control` |
| `docs/backend/risks-and-open-questions.md` | Q-104 ; Q-71 (journaux de CI publics) |
| `docs/backend/daily-reports/day-07.md` | Ce rapport |

## Démarche et revues

REVUES_A_COMPLETER

## Commandes exécutées et résultats réels

| Commande | Résultat |
|---|---|
| `lint-imports` | `Contracts: 2 kept, 0 broken` |
| `lint-imports` après injection de 3 violations (`core` → `db`, `audit` → `rfqs`, module `billing` non déclaré) | Les 3 violations détectées ; injections retirées |
| `make help` ; `make check` | 13 cibles listées ; Ruff, format, mypy (38 fichiers), import-linter OK ; **169 passed, 23 deselected** |
| Recherche des empreintes : API publique de GitHub et `git ls-remote` | checkout v7.0.1 `3d3c42e5…`, setup-uv v10.2.0 `c18668ad…` (étiquettes légères : l'empreinte est celle du commit) ; setup-uv v10.3.0 (5 jours) écartée |
| uv 0.13.0, gitleaks 8.30.1 : sommes officielles | Somme de gitleaks identique dans l'empreinte de GitHub et dans le fichier `checksums.txt` de la release ; `sha256sum --check` réussi ; licence MIT lue dans l'archive |
| Rejeu du job `quality` (`make install`, `make quality`) | Code de sortie 0 |
| Rejeu du job `tests` sur une base **séparée** (projet Compose `madasource-ci`, port 5435, valeurs de `.env.example`), pour ne pas toucher ton `db-test` | `migrations-check` depuis une base vide : « No new upgrade operations detected. » ; `make test` : **192 passed**, couverture **99,08 %** (seuil 95 %) ; base arrêtée ensuite (`down` sans `-v`, données en mémoire) |
| Rejeu du job `docker` | `docker compose config --quiet` OK avec et sans le profil `test` ; image construite ; utilisateur `10001:10001` vérifié |
| Contrôle de l'utilisateur sur une image qui tourne en root (`postgres`) | Échec, code 1 : le contrôle n'est pas vacuous |
| `gitleaks git --redact` sur tout l'historique | 25 commits, **aucune fuite** |
| `gitleaks git --pre-commit` (modifications non commitées) ; `gitleaks dir` (workflow, Makefile) | Aucune fuite |
| gitleaks sur un faux jeton GitHub généré dans le dossier temporaire de session | Détecté (`github-pat`), valeur masquée, code 1 ; fichier supprimé |
| Contrôle « aucun `.env` suivi » dans un dépôt Git jetable | Accepte les `.env.example` ; refuse `.env` et `sub/.env.local` ; sur le dépôt réel : aucun `.env` suivi |
| Validation YAML du workflow (Ruby, Psych) | 4 jobs, structure attendue |
| `uv lock` après déclaration de `grimp` | Diff limité à la déclaration ; aucun nouveau paquet ; `uv lock --check` OK |
| `make check` ; `make test ENV_FILE=../.env.example` (après documentation) | 169 passed ; **192 passed**, 99,08 % |

Non exécuté : le workflow sur GitHub (ton choix), `actionlint` (outil non installé, installation non demandée).

## Critères de sortie

CRITERES_A_COMPLETER

## Décisions À VALIDER

| Sujet | Échéance |
|---|---|
| **Q-71** : passer le dépôt GitHub en privé ; d'ici là, les journaux de CI sont publics | **Immédiat** |
| **Q-104** (a) seuil de couverture : 95 % (lignes et branches) sur tout `app/`, au lieu des 85 % sur `app/modules/` proposés au Jour 2 | Avant le Jour 9 (premiers modules) |
| **Q-104** (b) délai de carence de 14 jours avant d'adopter une nouvelle version d'action ou d'outil de CI | Prochaine mise à jour d'une version |
| **Q-104** (c) `ports` ajouté aux sous-modules importables d'un autre module (module-boundaries §9) ; (d) dépendances HTTP d'`access_control` dans `access_control/dependencies.py` | Jour 9 |
| **Q-104** (e) CI à chaque push sur toute branche et à chaque pull request (une branche avec pull request ouverte est testée deux fois) | Après le premier push |
| Q-102, Q-103 | Voir les rapports précédents |

## Risques et limites

- **CI jamais exécutée sur GitHub** : le rejeu local ne couvre pas l'environnement du runner (version de Docker et de Compose, téléchargement de CPython 3.14.8 par uv, cache de setup-uv). Un premier échec à ton push reste possible : à corriger alors sans affaiblir aucun contrôle.
- **Dépôt public** : les journaux de CI sont publics ; ils ne contiennent que des valeurs factices et des rapports masqués.
- **Mises à jour** : les versions épinglées ne se mettent pas à jour seules (aucun outil de mise à jour automatique n'est configuré) ; procédure dans `backend/README.md`.
- **gitleaks** ne voit que ce qui est suivi par Git : il ne remplace pas la discipline sur `.env` (ignoré par Git, protégé par le hook local).
- **Test d'architecture** : sans objet tant qu'aucun module métier n'existe ; sa valeur est démontrée par les cas fabriqués.

## Préparation du Jour 8 (non exécuté)

Jour 8 — Primitives de sécurité : hachage des mots de passe par une bibliothèque maintenue (Argon2id proposé, S-01), utilitaires de sécurité, configuration des secrets, validation d'entrées, protection des journaux, réponses HTTP sûres, stratégie de limitation de débit. Aucune cryptographie maison, aucun secret réel. Mise à jour de `security-design.md`.

Prérequis et décisions :
- choisir la bibliothèque de hachage (nouvelle dépendance, à justifier) et confirmer ses paramètres par rapport aux recommandations OWASP en vigueur ;
- limitation de débit : en mémoire pour une instance, ou stockage partagé (Redis) à justifier (security-design §15, À VALIDER au Jour 8) ;
- Q-102 (garde-fous de configuration) et Q-103 restent ouverts ;
- le premier push du workflow, par toi, dira si la CI passe sur GitHub.

**Le Jour 8 ne sera pas lancé sans ta validation explicite.**
