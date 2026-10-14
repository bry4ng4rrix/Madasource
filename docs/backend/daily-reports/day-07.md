# Jour 7 — Qualité et intégration continue

Date : 2026-10-14 · Statut : **TERMINÉ AVEC RÉSERVES**. Réserves :
- la CI ne bloque rien tant que la branche `main` n'est pas protégée sur GitHub (Q-104 f, action du propriétaire du dépôt) ;
- la version du workflow corrigée après les revues n'a pas encore tourné sur GitHub : seule la version intermédiaire du commit `98dceb2` y a tourné, avec succès ;
- **Q-104** : seuil de couverture, portée du délai de carence, conflit sur `ports`, réglages GitHub, outils supplémentaires, à valider ;
- le dépôt GitHub est toujours public (Q-71, hérité) : les journaux de CI le sont aussi.

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
| CI | **J'écris la CI, tu pousses toi-même** : rien n'a été poussé par Claude. Tu as poussé le commit `98dceb2` ; la CI a tourné sur GitHub à cette occasion |

## Prérequis vérifiés

- Jours 4 à 6 livrés ; 184 tests au vert au départ ; base de test disponible dans Compose.
- Une partie du travail du jour a été commitée par toi en cours de journée (commits `0961309` et `98dceb2`, ce dernier poussé) ; les correctifs issus des revues sont dans l'arbre de travail, non commités.

## Fichiers

| Fichier | Contenu |
|---|---|
| `.github/workflows/ci.yml` (nouveau) | Quatre jobs : `quality`, `tests` (PostgreSQL éphémère), `docker`, `secrets` ; jeton en lecture seule ; actions épinglées par empreinte de commit ; pas de cache ; `bash -eo pipefail` |
| `.github/gitleaks.toml` (nouveau) | Règles par défaut de gitleaks, plus la règle `url-credentials` ; deux listes d'autorisation étroites, justifiées dans security-design §17 |
| `backend/Makefile` (nouveau) | Commandes officielles : `install`, `lock-check`, `lint`, `format-check`, `types`, `imports`, `quality`, `test-fast`, `test`, `migrations-check` (base de test seulement, garde-fou `_test`), `docker-build` (contrôle de l'utilisateur de l'image construite), `check` |
| `backend/pyproject.toml`, `backend/uv.lock` | Contrats import-linter `socle` et `modules` ; dépendances de dev `import-linter` 2.15, `grimp` 3.17, `pytest-cov` 7.1.0 ; couverture des branches, seuil 95 % |
| `backend/app/modules/__init__.py` (nouveau) | Paquet conteneur des modules métier, exigé par le contrat `modules` ; aucun module créé à l'avance |
| `backend/app/db/registry.py` | Le paquet `app.modules` devient obligatoire : son absence est une erreur, plus une liste vide silencieuse |
| `backend/tests/architecture/test_boundaries.py` (nouveau) | Couche de chaque paquet d'`app` ; interface publique exacte des modules ; propriétaire de chaque table et clés étrangères vers un niveau strictement inférieur ; niveaux comparés à module-boundaries §2 ; cas fabriqués |
| `backend/tests/unit/db/test_base.py` | Registre des modèles : paquet obligatoire, découverte, `models.py` cassé ; paquets fabriqués retirés de `sys.modules` |
| `backend/Dockerfile`, `docker-compose.yml` | Images `uv`, `python` et `postgres` épinglées par empreinte (`@sha256:…`) |
| `backend/.dockerignore` | Caches d'import-linter et de grimp exclus du contexte de build |
| `.gitignore` | Motifs `*.env` et `.envrc` ajoutés |
| `infrastructure/postgres/10-create-app-role.sh` | `psql` en `VERBOSITY terse` : une erreur ne recopie plus la ligne contenant le mot de passe |
| `backend/README.md` | Commandes officielles (`make`), section « Intégration continue », dépendances justifiées, structure |
| `README.md` | État au Jour 7, CI |
| `docs/backend/testing-strategy.md` | §3, §4, §8, §9 (commandes), §10 (seuil de couverture appliqué, Q-104 a) |
| `docs/backend/module-boundaries.md` | §4 (proposition pour les dépendances HTTP d'`access_control`), §9 (contrôles implémentés, conflit sur `ports`), §10 |
| `docs/backend/architecture.md` | D-05 ; mypy retenu ; import-linter, GitHub Actions, gitleaks |
| `docs/backend/security-design.md` | §17 : détection de secrets et ses limites, contrôle `.env`, garde-fous de la CI, mot de passe du rôle applicatif |
| `docs/backend/api-conventions.md` | §16 : renvoi vers la proposition pour `access_control` |
| `docs/backend/risks-and-open-questions.md` | Q-104 (a à h) ; Q-71 (journaux de CI publics) |
| `docs/backend/daily-reports/day-07.md` | Ce rapport |

## Démarche et revues

| Étape | Résultat |
|---|---|
| Recherche des versions | Actions et gitleaks relevés sur l'API publique de GitHub. setup-uv v10.3.0, publiée 5 jours plus tôt, écartée au profit de v10.2.0 (délai de carence de 14 jours, Q-104 b) |
| Revue de code (agent `code-reviewer`) | Prêt avec réserves, 0 bloquant. Importants : clés étrangères de même niveau non détectées ; tables non attribuées (`Table` brut, tables du socle) ignorées en silence. Mineurs : sous-paquet d'une interface publique accepté ; paquets fabriqués laissés dans `sys.modules` ; niveaux vérifiés sur 4 modules seulement ; règle `.claude/rules/backend-python.md` contraire à l'ajout de `ports` ; doc qui disait la CI « implémentée ». Tous corrigés, sauf les fichiers de configuration de Claude (règle, skill `pytest-workflow`), non modifiés sans ton accord |
| Revue DevOps (agent `devops-engineer`) | 0 bloquant. Majeur : `make migrations-check` migrait la base de développement, sans garde-fou ; corrigé (base de test seulement, garde-fou `_test`, comme la CI). Mineurs : exceptions gitleaks possibles depuis un commit ; cache uv implicite ; délai de carence non appliqué à uv ; contrôle de l'utilisateur sur une image éventuellement périmée ; doc des migrations sur base vide. Corrigés ou ouverts en Q-104 |
| Audit sécurité (agent `security-auditor`) | 0 critique, 3 moyens : aucune règle gitleaks pour un mot de passe dans une URL (règle `url-credentials` ajoutée, auto-test) ; CI qui ne bloque rien sans protection de `main` (Q-104 f) ; délai de carence affirmé mais non appliqué à uv et aux paquets Python (doc corrigée, Q-104 b). Faibles : contrôle `.env` trop étroit (étendu à `*.env`, `.envrc` et à l'historique) ; cache uv (désactivé) ; annulation des exécutions sur `main` (limitée aux pull requests) ; pull requests de forks (réglage GitHub, Q-104 f). Info : mot de passe recopié par `psql` en cas d'erreur (vérifié, corrigé par `VERBOSITY terse`) |
| Vérification ciblée des correctifs (agents `devops-engineer`, `code-reviewer`) | VERIFICATION_A_COMPLETER |

## Commandes exécutées et résultats réels

| Commande | Résultat |
|---|---|
| `lint-imports` | `Contracts: 2 kept, 0 broken` |
| `lint-imports` après injection de violations, sur des copies dans le dossier temporaire de session (`core` → `db`, `audit` → `rfqs`, module `billing` non déclaré, puis `app.wiring` → `app.api`) | Chaque violation détectée ; copies supprimées |
| Recherche des empreintes : API publique de GitHub et `git ls-remote` | checkout v7.0.1 `3d3c42e5…`, setup-uv v10.2.0 `c18668ad…` (étiquettes légères : l'empreinte est celle du commit) |
| uv 0.13.0, gitleaks 8.30.1 : sommes officielles | Somme de gitleaks identique dans l'empreinte de GitHub et dans `checksums.txt` ; `sha256sum --check` réussi ; licence MIT lue dans l'archive |
| `psql` sur une instruction fautive contenant une valeur factice, modes `default` puis `terse` (base de test) | `default` recopie la ligne avec le mot de passe ; `terse` n'affiche que la position. Rien n'a été créé |
| gitleaks avec `.github/gitleaks.toml` sur tout l'historique | Avant les listes d'autorisation : 6 détections, toutes des valeurs factices de tests ; après : aucune fuite. Une valeur factice des tests placée hors de `backend/tests/` reste détectée |
| Contrôles du job `secrets` dans des dépôts Git jetables | `.env` et `.env.local` refusés ; `prod.env` ajouté puis supprimé détecté dans l'historique ; `.envrc` refusé ; `.env.example` accepté. Auto-test : échoue si la règle `url-credentials` manque |
| `make migrations-check` avec une base de développement, puis sans variable | Refus avant Alembic dans les deux cas (code 2) |
| `make check` (final) | Ruff, format, mypy (38 fichiers), import-linter : OK ; **170 passed, 23 deselected** |
| Rejeu du job `tests` sur une base **séparée et neuve** (projet Compose `madasource-ci`, port 5435, valeurs de `.env.example`), exactement comme en CI | Rôle `madasource_app` créé par le script modifié (non superutilisateur, `NOINHERIT`) ; aucun mot de passe dans les journaux du conteneur ; `make migrations-check` : les deux révisions appliquées depuis la base vide, « No new upgrade operations detected. » ; `make test` : **193 passed**, couverture **99,38 %** ; base arrêtée ensuite (`down` sans `-v`, données en mémoire) |
| Rejeu du job `docker` | `docker compose config --quiet` OK avec et sans le profil `test` ; image construite ; utilisateur `10001:10001` de l'image construite |
| Rejeu du job `secrets` : étapes extraites du YAML et exécutées telles quelles (`bash -eo pipefail`), téléchargement compris | 5 étapes réussies : aucun `.env` dans l'arbre ni l'historique, aucune exception hors configuration, somme vérifiée, auto-test (détection), historique : 26 commits, aucune fuite |
| Validation YAML du workflow (Ruby, Psych) | 4 jobs, étapes, `concurrency` et `defaults` attendus |
| GitHub Actions, run `38557251094` (commit `98dceb2`, poussé par toi), lu par l'API publique | **4 jobs réussis** : quality 19 s, tests 29 s, docker 11 s, secrets 7 s |

Les exécutions de `make test` en cours de journée (hors rejeu de la CI) ont visé ton `db-test` habituel (port 5434), base de test éphémère prévue pour cela : transactions annulées, retour arrière d'une révision puis remontée, comme aux jours précédents.

Non exécuté : `actionlint` et `zizmor` (non installés, Q-104 g) ; la version corrigée du workflow sur GitHub.

## Critères de sortie

| Critère (roadmap §5) | État |
|---|---|
| Périmètre implémenté et cohérent | Oui : commandes reproductibles (`Makefile`), CI sur push et pull request, base de test isolée (jamais la production ni la base de développement), commandes documentées, test d'architecture, recherche de secrets |
| Tests appropriés et résultat connu | Oui : 193 tests, couverture 99,38 % ; contrôles de la CI rejoués en local et cas d'échec fabriqués ; première exécution GitHub réussie |
| Migrations et contraintes cohérentes | Oui : aucune migration ajoutée ; montée depuis une base vide et `alembic check` sans écart, en local et en CI |
| Documentation et `.env.example` à jour | Oui ; `.env.example` inchangé, cohérent avec la CI qui l'utilise |
| Aucun secret ajouté | Oui : gitleaks sur l'historique et sur les modifications non commitées, aucune fuite ; valeurs factices seulement |
| Défauts critiques corrigés ou signalés | Oui : aucun bloquant ; constats majeurs et moyens corrigés ou ouverts en Q-104 |
| Aucune règle ni aucun test ignoré pour une CI verte | Oui : aucun `noqa`, `type: ignore`, `skip`, `xfail`, `continue-on-error` ni `\|\| true` ajouté ; les listes d'autorisation de gitleaks sont exactes et justifiées |
| Décisions non définies marquées `À VALIDER` | Oui : Q-104 |

## Décisions À VALIDER

| Sujet | Échéance |
|---|---|
| **Q-71** : passer le dépôt GitHub en privé ; d'ici là, les journaux de CI sont publics | **Immédiat** |
| **Q-104 f** : protéger `main` (statuts requis des quatre jobs, pas de push forcé) ; Secret Protection et protection au push ; approbation des contributeurs externes ; alertes Dependabot | **Immédiat** : sans cela, la CI ne bloque rien |
| **Q-104 a** : seuil de couverture de 95 % sur tout `app/` | Avant le Jour 9 |
| **Q-104 b** : étendre le délai de carence de 14 jours à uv et aux paquets Python, et choisir un mécanisme | Prochaine mise à jour de dépendance |
| **Q-104 c** : conflit sur `ports` entre `.claude/rules/backend-python.md` et module-boundaries §5.2 ; **Q-104 d** : dépendances HTTP d'`access_control` | Jour 9 |
| **Q-104 e** : déclencheurs de la CI ; **Q-104 g** : hook gitleaks sur le poste, actionlint ou zizmor, audit de vulnérabilités, `no-build` ; **Q-104 h** : sonde de santé du service `backend` | À ta convenance |
| Mise à jour du skill `pytest-workflow` (mode complet : `make check` et `make test`) et de la règle `backend-python.md` selon Q-104 c | Avec ton accord (configuration de Claude) |
| Q-102, Q-103 | Voir les rapports précédents |

## Risques et limites

- **CI non bloquante** : sans protection de `main`, un job rouge n'empêche ni un push direct ni une fusion.
- **Détection après coup** : la recherche de secrets a lieu après le push, sur un dépôt public. Un secret poussé doit être changé aussitôt ; le retirer de l'historique ne suffit pas. gitleaks n'analyse ni les PDF ni le diff propre des commits de fusion.
- **Dépôt public** : les journaux de CI sont publics ; ils ne contiennent que des valeurs factices et des rapports masqués.
- **Mises à jour** : les versions épinglées ne se mettent pas à jour seules ; aucune alerte de vulnérabilité n'est configurée côté projet (Q-104 f, g).
- **Test d'architecture** : sans objet tant qu'aucun module métier n'existe ; sa valeur est démontrée par les cas fabriqués. Les imports de `app.api` vers les modules seront contrôlés avec les premiers routers (Jour 9).

## Préparation du Jour 8 (non exécuté)

Jour 8 — Primitives de sécurité : hachage des mots de passe par une bibliothèque maintenue (Argon2id proposé, S-01), utilitaires de sécurité, configuration des secrets, validation d'entrées, protection des journaux, réponses HTTP sûres, stratégie de limitation de débit. Aucune cryptographie maison, aucun secret réel. Mise à jour de `security-design.md`.

Prérequis et décisions :
- choisir la bibliothèque de hachage (nouvelle dépendance, à justifier) et confirmer ses paramètres par rapport aux recommandations OWASP en vigueur ;
- limitation de débit : en mémoire pour une instance, ou stockage partagé (Redis) à justifier (security-design §15, À VALIDER au Jour 8) ;
- Q-102 et Q-103 restent ouverts ; Q-104 f est à traiter dès maintenant ;
- le prochain push dira si la version corrigée du workflow passe sur GitHub.

**Le Jour 8 ne sera pas lancé sans ta validation explicite.**
