# Jour 2 — Architecture modulaire et conventions API

Date : 2026-10-12 · Statut : **TERMINÉ**. Jour documentaire : aucun code applicatif. Les décisions `À VALIDER` attendent la réponse du client.

## Objectif du jour

Consigne de `roadmap_backend_fastapi.md`, Jour 2 : à partir du Jour 1, définir l'architecture backend FastAPI dans six documents. Il fallait couvrir :
- la responsabilité de chaque module et les dépendances permises ;
- la convention `/api/v1`, la pagination, les filtres, les erreurs, les logs, les dates, les devises, les UUID, les tests et les transactions ;
- la communication entre modules sans imports circulaires ;
- les décisions à confirmer, marquées comme telles.

## Prérequis vérifiés

- Livrables du Jour 1 présents ; `check.md` : Jour 1 OK.
- Le dépôt Git a été initialisé par l'utilisateur et poussé sur GitHub. Sept commits de l'utilisateur pendant la journée, dont :
  - le versionnement du cahier des charges (PDF identique à celui analysé au Jour 1, même empreinte SHA-256) ;
  - un `.gitignore` qui exclut `CLAUDE.md` et les deux roadmaps.
- `planning.md` a été retiré puis réajouté, avec un contenu identique à l'original : aucune source n'a changé.

## Fichiers

**Créés** (`docs/backend/`) :

| Fichier | Contenu |
|---|---|
| `architecture.md` | Principes, structure du code, cycle d'une requête, transactions et concurrence, configuration, conventions transverses (dates, montants, UUID, journaux, santé), feature flags, mode DEMO, langues, intégrations, tâches asynchrones, exploitation, **33 décisions D-01 à D-33**, traçabilité de la revue d'architecture, justification de la stack |
| `module-boundaries.md` | 23 modules sur 20 niveaux ; dépendances permises ; couche HTTP ; **2 ports** (P-01 avec audience, P-03), 3 ports retirés ; règles de données inter-modules et projections publiées ; flux détaillés ; contrôle automatique ; **ordre de construction** |
| `api-conventions.md` | Versionnement, carte des domaines du CdC §56, méthodes et actions (acceptation sur un chemin unique), JSON, pagination, tri, filtres, formats des dates, montants et quantités (chaînes seulement en entrée), codes, idempotence, en-têtes, statuts HTTP, OpenAPI (audiences et sélection explicite des schémas), limites, exemples |
| `error-handling.md` | Problem Details (RFC 9457), validation sans renvoi de la valeur saisie, catalogue de 25 codes, hiérarchie d'exceptions, gestionnaires (SQLSTATE, réponses 500, `WWW-Authenticate`), règles de sécurité des messages, journalisation, tests obligatoires |
| `testing-strategy.md` | Niveaux de tests, outils, base PostgreSQL éphémère, isolation par point de sauvegarde, tests de concurrence et écritures de sécurité, matrice obligatoire, règles critiques, non-exposition par audience, migrations |
| `security-design.md` | Actifs, menaces, correspondance OWASP API Top 10 2023, authentification, autorisation par **audience**, confidentialité des prix (non-déduction, deux jeux de termes en Modèle A), coordonnées bancaires, documents, messagerie, notifications, mode DEMO, audit, **58 décisions S-01 à S-58**, traçabilité de la relecture de sécurité |
| `daily-reports/day-02.md` | Ce rapport |

**Modifiés** :
- documents du Jour 1, avec les ajouts marqués « (J2) » :
  - `actors-and-permissions.md` : correction critique C-1, lignes ajoutées ;
  - `business-rules.md` : 16 règles ajoutées, légende du statut « Proposé » ;
  - `requirements.md` : §6, clés étrangères montantes corrigées ;
  - `risks-and-open-questions.md` : R-26 à R-31, SRC-16 à SRC-19, Q-78 à Q-93 ;
  - `v1-scope.md` ;
- configuration : `CLAUDE.md` (fichier local), `.claude/rules/backend-python.md`, `.claude/rules/tests.md`, skills `fastapi-module` et `secure-api`, `claude-code-setup.md`, `claude-code-audit.md`.

Aucun code applicatif, aucun `.env`, aucun secret.

## Démarche et revues

| Étape | Résultat |
|---|---|
| 1. Rédaction des six documents | Voir ci-dessus |
| 2. **Relecture de sécurité** de la matrice de visibilité du Jour 1 (agent `security-auditor`, lecture seule), recommandée par la revue du Jour 1 | 32 constats : **1 critique**, 11 élevés, 14 moyens, 6 faibles. Critique : la notion de « partie » était bilatérale alors que le Modèle A est trilatéral (acheteur, MadaSource, exportateur), ce qui exposait la marge. Correction : audiences explicites, deux jeux de termes figés par Trade, paiements orientés. Tous les constats sont traités ([security-design.md](../security-design.md#22-relecture-de-sécurité-du-jour-2) §22). |
| 3. **Revue d'architecture** (agent `backend-architect`, avec vérification dans les documentations officielles) | 35 constats : **1 bloquant**, 15 majeurs, 18 mineurs, 1 suggestion. Bloquant : cycle autour du statut de compte, d'où D-28. Autres : verrous `FOR NO KEY UPDATE` avec `populate_existing`, ports réduits de 5 à 2, projections publiées, écritures de sécurité hors transaction. Tous traités ([architecture.md](../architecture.md#13-revue-darchitecture-du-jour-2) §13). |
| 4. **Revue finale** (skill `code-review-madasource`, agent `code-reviewer` en contexte séparé) | Premier essai interrompu par la limite d'utilisation de la session ; relancé à 20 h 11. Verdict avant corrections : non prêt. 26 constats : **2 bloquants** (ordre de construction des modules, S-18 surévaluée), 8 importants, 16 facultatifs. Tous traités. Ce lancement confirme que le skill fonctionne en contexte séparé. |

## Décisions structurantes proposées

| Décision | Contenu |
|---|---|
| D-05, D-06 | Modules ordonnés en 20 niveaux, dépendances vers le bas uniquement ; deux ports seulement |
| D-08, D-09 | Une transaction par cas d'usage, validée avant la réponse. Verrous `FOR NO KEY UPDATE` avec `populate_existing` ; parent avant enfant ; ordre des niveaux |
| D-14 | Montants en `Decimal`/`NUMERIC`, en chaînes seulement en entrée JSON, sortie par modèles Pydantic |
| D-28 | Statut de compte porté par l'organisation ; statuts exportateur à valider (Q-12) |
| D-29 | Écritures de sécurité exécutées après l'annulation de la transaction principale |
| D-31, D-32 | DTO entre modules ; schéma de réponse choisi explicitement selon l'audience, jamais par union |
| D-33 | L'acceptation est orchestrée par `trades`, sur un chemin unique, avec la version de l'offre |
| S-19, S-39 | Non-déduction des composantes de prix ; deux jeux de termes en Modèle A |
| S-29 | Sept audiences explicites, au lieu de « Partie » |
| S-34 | Séparation des tâches pour la confirmation des paiements |
| [module-boundaries.md](../module-boundaries.md#11-ordre-de-construction) §11 | Ordre de construction : rétro-branchement pour `audit` et `notifications` ; noyau minimal recommandé pour `documents` au Jour 14 (Q-93) |

## Commandes exécutées et résultats réels

| Commande | Résultat |
|---|---|
| `git status`, `git log`, `git ls-files`, `git check-ignore`, `git diff c6e27d8 HEAD -- planning.md` | Dépôt et commits inspectés. Le PDF et `planning.md` sont suivis ; `CLAUDE.md` et les roadmaps ne le sont plus, mais restent dans l'historique ; `.env` n'est pas ignoré ; `planning.md` est identique à l'original. |
| `sha256sum` des deux copies du PDF | Identiques |
| Python 3.14.8 et 3.12.14 : `hasattr(uuid, "uuid7")` | Présent en 3.14.8, absent en 3.12.14 |
| Pydantic 2.13.5 : sérialisation d'un `Decimal` | `{"amount":"43.30"}`, en chaîne |
| Pydantic 2.13.5 : erreur de validation d'un mot de passe trop court | La valeur saisie figure dans `input` : le gestionnaire d'erreurs doit la retirer |
| `python3 …/scratchpad/hooktest/check_refs.py` (après corrections) | 0 problème : identifiants Q, R, SRC, REQ, NFR, BR, D, S et P tous définis ; liens et ancres valides (section suivante) |
| `python3 .claude/tests/test_hooks.py` | 0 échec |
| Validation du frontmatter (pyyaml) | 18/18 valides |

Les affirmations sur FastAPI, SQLAlchemy, PostgreSQL et import-linter viennent de la revue d'architecture, qui cite les documentations officielles consultées le 2026-10-12. Je ne les ai pas revérifiées moi-même : elles sont à confirmer sur les versions épinglées aux Jours 4 et 5.

## Critères de sortie

| Critère (roadmap §5) | État |
|---|---|
| Périmètre implémenté et cohérent | Oui : tous les thèmes de la consigne sont traités (confirmé par la revue finale), et tous les constats des trois revues ont été corrigés |
| Tests appropriés et résultat connu | Sans objet : jour documentaire. La stratégie de tests est rédigée. |
| Migrations et contraintes cohérentes | Sans objet (Jour 3 et suivants) |
| Documentation et `.env.example` à jour | Documentation : oui. `.env.example` : sans objet (Jour 4) |
| Aucun secret ajouté | Oui |
| Défauts critiques corrigés ou signalés | Oui : tous corrigés. La visibilité du dépôt distant est signalée (R-26, Q-71). |
| Décisions non définies marquées `À VALIDER` | Oui : 16 nouvelles questions (Q-78 à Q-93). Les statuts Proposé et À VALIDER ont été harmonisés entre les documents. |

## Décisions À VALIDER

| Question | Sujet | Échéance |
|---|---|---|
| **Q-71** | Le dépôt GitHub est-il privé ? Le cahier des charges, et l'historique de `CLAUDE.md` et des roadmaps, peuvent-ils y rester ? | **Immédiat** |
| Q-93 | Ordre de construction (rétro-branchement ou noyau minimal anticipé) | Avant le Jour 9 |
| Q-12 | Statuts du compte exportateur (D-28) | Avant le Jour 3 |
| Q-82 | En Modèle A, objets du Trade partagés ou bilatéraux avec MadaSource | Jour 3, bloque le Jour 27 |
| Q-80, Q-89 | Second facteur pour les admins ; répartition des permissions admin | Jours 9-10 |
| Q-81, Q-87, Q-88 | Chiffrement et modification des coordonnées bancaires ; double validation des paiements | Jours 14 et 33 |
| Q-83 à Q-86, Q-90 à Q-92 | Documents, questions sur les RFQ, projection destinataire, profil public, champs vérifiés, règles de prix, litiges | Jours 14 à 35 |
| Q-78, Q-79 | Désactivation d'une catégorie ; hébergement | Jours 4 et 16 |
| D-10, D-15, D-24, D-27 | Pilote PostgreSQL, version d'UUID, forme du membre `type` des erreurs, version de Python | Jours 4-5 |

## Risques et limites

- **Dépôt distant** (R-26) : sa visibilité n'est pas vérifiée. Le cahier des charges y est versionné, et `CLAUDE.md` et les roadmaps restent dans l'historique malgré le `.gitignore`.
- **`.gitignore`** (R-20) : il ne couvre ni `.env` ni les environnements virtuels.
- **`CLAUDE.md` non versionné** : une copie fraîche du dépôt n'aura pas les règles permanentes du projet.
- Les corrections de la revue finale ont été vérifiées par contrôles automatiques (références, liens, frontmatter), mais n'ont pas fait l'objet d'une nouvelle revue complète par un agent.
- Les propositions « Proposé » restent des hypothèses de travail, à confirmer avant implémentation.

## Préparation du Jour 3 (non exécuté)

Jour 3 — Modèle de données et ERD. Livrables :
- `data-model.md` ;
- `erd.mmd` ;
- `data-classification.md` ;
- `indexes-and-constraints.md`.

Prérequis :
- documents des Jours 1 et 2, présents ;
- de préférence, les réponses à Q-09, Q-10, Q-12, Q-25, Q-37, Q-66, Q-67, Q-68, Q-74 et Q-82, faute de quoi les choix seront marqués `À VALIDER` ;
- agent `database-reviewer` à mobiliser sur le modèle.

Points à reprendre au Jour 3 :
- D-07, D-16, D-28, D-30 ;
- MembershipRole ;
- deux jeux de termes par Trade ;
- versions de quotation ;
- classification des champs (qui alimente les listes de clés interdites par audience) ;
- droits sur la table d'audit.

Commande : `/daily-delivery 3`, après validation de ce rapport.
